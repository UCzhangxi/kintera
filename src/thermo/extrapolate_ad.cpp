// C/C++
#include <cmath>
#include <limits>

// kintera
#include <kintera/constants.h>

#include "eval_uhs.hpp"
#include "log_svp.hpp"
#include "thermo.hpp"

namespace kintera {

torch::Tensor ThermoXImpl::effective_cp(torch::Tensor temp, torch::Tensor pres,
                                        torch::Tensor xfrac, torch::Tensor gain,
                                        torch::optional<torch::Tensor> conc) {
  if (!conc.has_value()) {
    conc = compute("TPX->V", {temp, pres, xfrac});
  }

  if (!gain.defined()) {  // no-op
    auto cp = eval_cp_R(temp, conc.value(), options) * constants::Rgas;
    return (cp * xfrac).sum(-1);
  }

  LogSVPFunc::init(options->nucleation());

  auto logsvp_ddT = LogSVPFunc::grad(temp);

  torch::Tensor rate_ddT;

  if (gain.device().is_cpu()) {
    rate_ddT = std::get<0>(torch::linalg_lstsq(gain, logsvp_ddT));
  } else {
    auto pinv = torch::linalg_pinv(gain, /*atol=*/1e-6);
    rate_ddT = pinv.matmul(logsvp_ddT.unsqueeze(-1)).squeeze(-1);
  }

  auto enthalpy =
      eval_enthalpy_R(temp, conc.value(), options) * constants::Rgas;
  auto cp = eval_cp_R(temp, conc.value(), options) * constants::Rgas;

  auto cp_normal = (cp * xfrac).sum(-1);
  auto cp_latent = (enthalpy.matmul(stoich) * rate_ddT).sum(-1);

  return cp_normal + cp_latent;
}

void ThermoXImpl::extrapolate_dlnp(torch::Tensor temp, torch::Tensor pres,
                                   torch::Tensor xfrac,
                                   ExtrapOptions const& opts) {
  double dlnp = opts.dlnp();
  double ds_dlnp = opts.ds_dlnp();
  bool verbose = opts.verbose();

  if (verbose) {
    std::cout << "Extrapolating adiabat with dlnp = " << dlnp << std::endl;
  }

  int ngas = options->vapor_ids().size();
  int ncloud = options->cloud_ids().size();

  auto conc = compute("TPX->V", {temp, pres, xfrac});
  auto entropy_vol = compute("TPV->S", {temp, pres, conc});
  auto entropy_mole0 = entropy_vol / conc.sum(-1);
  auto entropy_target = entropy_mole0 + ds_dlnp * dlnp;

  // dry-gas mole fraction (dry never condenses; reference for rain-out)
  auto x_dry0 = conc.select(-1, 0) / conc.sum(-1);

  if (verbose) {
    std::cout << "Initial State: T = [" << temp.min().item<double>() << ", "
              << temp.max().item<double>() << "] K" << std::endl;
    std::cout << "               P = [" << pres.min().item<double>() << ", "
              << pres.max().item<double>() << "] Pa" << std::endl;
    std::cout << "               S = [" << entropy_mole0.min().item<double>()
              << ", " << entropy_mole0.max().item<double>() << "] J/K/mol"
              << std::endl;
    std::cout << "Composition:   X = { ";
    for (int i = 0; i < xfrac.size(-1); ++i) {
      std::cout << "[" << xfrac.select(-1, i).min().item<double>() << ", "
                << xfrac.select(-1, i).max().item<double>() << "], ";
    }
    std::cout << "}" << std::endl;
  }

  int iter = 0;
  pres *= exp(dlnp);
  auto xfrac0 = xfrac.clone();

  while (iter++ < options->max_iter()) {
    xfrac.copy_(xfrac0);
    auto gain = forward(temp, pres, xfrac);

    // pseudo-adiabat: the departing condensate carries its own molar entropy
    // s_cond away, d(n_gas * s_gas) = -sum_j s_cond,j * dn_j. Per mole of
    // (conserved) dry air the entropy target for the rained-out gas is then
    //   (x_dry_new / x_dry0) * s0 - sum_j s_cond,j * conc_cloud,j / n_gas
    auto entropy_step = entropy_target;
    if (opts.rainout()) {
      auto conc_full = compute("TPX->V", {temp, pres, xfrac});
      auto scond = eval_entropy_R(temp, pres, conc_full, stoich, options)
                       .narrow(-1, ngas, ncloud) *
                   constants::Rgas;
      auto n_gas = conc_full.narrow(-1, 0, ngas).sum(-1);
      auto x_dry_new = conc_full.select(-1, 0) / n_gas;
      auto cloud_flux =
          (scond * conc_full.narrow(-1, ngas, ncloud)).sum(-1) / n_gas;
      entropy_step =
          (x_dry_new / x_dry0) * entropy_mole0 - cloud_flux + ds_dlnp * dlnp;

      xfrac.narrow(-1, ngas, ncloud) = 0.;
      xfrac /= xfrac.sum(-1, true);
    }

    conc = compute("TPX->V", {temp, pres, xfrac});
    auto cp_mole = effective_cp(temp, pres, xfrac, gain, conc);

    entropy_vol = compute("TPV->S", {temp, pres, conc});
    auto entropy_mole = entropy_vol / conc.sum(-1);

    if (verbose) {
      std::cout << "Iter " << iter << std::endl;
      std::cout << "temp = [" << temp.min().item<double>() << ", "
                << temp.max().item<double>() << "] K" << std::endl;
      std::cout << "pres = [" << pres.min().item<double>() << ", "
                << pres.max().item<double>() << "] Pa" << std::endl;

      std::cout << "entropy_mole = [" << entropy_mole.min().item<double>()
                << ", " << entropy_mole.max().item<double>() << "] J/K/mol"
                << std::endl;

      std::cout << "Composition: X = { ";
      for (int i = 0; i < xfrac.size(-1); ++i) {
        std::cout << "[" << xfrac.select(-1, i).min().item<double>() << ", "
                  << xfrac.select(-1, i).max().item<double>() << "], ";
      }
      std::cout << "}" << std::endl;
    }

    if ((entropy_step - entropy_mole).abs().max().item<double>() <
        10 * options->ftol()) {
      break;
    }

    temp *= 1. + (entropy_step - entropy_mole) / cp_mole;
  }

  if (iter >= options->max_iter()) {
    TORCH_WARN("extrapolate_dlnp does not converge after ", options->max_iter(),
               " iterations.");
  }
}

void ThermoXImpl::extrapolate_dz(torch::Tensor temp, torch::Tensor pres,
                                 torch::Tensor xfrac,
                                 ExtrapOptions const& opts) {
  double grav = opts.grav();
  double dz = opts.dz();
  double ds_dz = opts.ds_dz();
  bool verbose = opts.verbose();

  if (verbose) {
    std::cout << "Extrapolating adiabat over dz = " << dz << " m"
              << " with gravity = " << grav << " m/s^2" << std::endl;
  }

  int ngas = options->vapor_ids().size();
  int ncloud = options->cloud_ids().size();

  auto conc = compute("TPX->V", {temp, pres, xfrac});
  auto rho0 = compute("V->D", {conc});
  auto entropy_mole0 = compute("TPV->S", {temp, pres, conc}) / conc.sum(-1);
  auto entropy_target = entropy_mole0 + ds_dz * dz;

  // dry-gas mole fraction (dry never condenses; reference for rain-out)
  auto x_dry0 = conc.select(-1, 0) / conc.sum(-1);

  if (verbose) {
    std::cout << "Initial State: T = [" << temp.min().item<double>() << ", "
              << temp.max().item<double>() << "] K" << std::endl;
    std::cout << "               P = [" << pres.min().item<double>() << ", "
              << pres.max().item<double>() << "] Pa" << std::endl;
    std::cout << "               S = [" << entropy_mole0.min().item<double>()
              << ", " << entropy_mole0.max().item<double>() << "] J/K/mol"
              << std::endl;
    std::cout << "Composition:   X = { ";
    for (int i = 0; i < xfrac.size(-1); ++i) {
      std::cout << "[" << xfrac.select(-1, i).min().item<double>() << ", "
                << xfrac.select(-1, i).max().item<double>() << "], ";
    }
    std::cout << "}" << std::endl;
  }

  auto mmw = (mu * xfrac).sum(-1);
  auto pres0 = pres.clone();
  auto xfrac0 = xfrac.clone();

  // using isothermal as an initial guess
  pres.set_(pres0 * exp(-grav * mmw * dz / (constants::Rgas * temp)));

  // ACTIVE-SET CHATTER GUARD (2026-08-06). Each iteration re-solves the
  // equilibrium, so at a level where a SECOND condensable is marginally
  // saturated the active set flips between iterations; cloud_flux (hence
  // entropy_step) and cp_mole then jump discontinuously and the residual cannot
  // settle. Measured on the Ge Neptune column: exactly the 3 cells where CH4
  // activates on top of an already-saturated H2S (P = 0.859/0.796/0.737 bar)
  // fail, and raising max_iter 30 -> 400 makes it WORSE (9 -> 20 warnings) --
  // the signature of oscillation, not of slow convergence.
  //   * relax halves whenever a step INCREASES the residual, damping the
  //   oscillation;
  //   * the best iterate is kept and restored if the loop exits unconverged, so
  //   a chattering
  //     cell returns its closest state rather than whichever side it last
  //     landed on.
  // Both are inert while the residual decreases monotonically => every
  // converging cell is bit-identical.
  double relax = 1.0;
  double best_resid = std::numeric_limits<double>::infinity();
  torch::Tensor best_temp, best_pres;

  int iter = 0;
  while (iter++ < options->max_iter()) {
    xfrac.copy_(xfrac0);
    auto gain = forward(temp, pres, xfrac);

    // pseudo-adiabat rain-out entropy target; see extrapolate_dlnp
    auto entropy_step = entropy_target;
    if (opts.rainout()) {
      auto conc_full = compute("TPX->V", {temp, pres, xfrac});
      auto scond = eval_entropy_R(temp, pres, conc_full, stoich, options)
                       .narrow(-1, ngas, ncloud) *
                   constants::Rgas;
      auto n_gas = conc_full.narrow(-1, 0, ngas).sum(-1);
      auto x_dry_new = conc_full.select(-1, 0) / n_gas;
      auto cloud_flux =
          (scond * conc_full.narrow(-1, ngas, ncloud)).sum(-1) / n_gas;
      entropy_step =
          (x_dry_new / x_dry0) * entropy_mole0 - cloud_flux + ds_dz * dz;

      xfrac.narrow(-1, ngas, ncloud) = 0.;
      xfrac /= xfrac.sum(-1, true);
    }

    conc = compute("TPX->V", {temp, pres, xfrac});
    auto cp_mole = effective_cp(temp, pres, xfrac, gain, conc);
    auto entropy_mole = compute("TPV->S", {temp, pres, conc}) / conc.sum(-1);

    if (verbose) {
      std::cout << "Iter " << iter << std::endl;
      std::cout << "temp = [" << temp.min().item<double>() << ", "
                << temp.max().item<double>() << "] K" << std::endl;
      std::cout << "pres = [" << pres.min().item<double>() << ", "
                << pres.max().item<double>() << "] Pa" << std::endl;

      std::cout << "entropy_mole = [" << entropy_mole.min().item<double>()
                << ", " << entropy_mole.max().item<double>() << "] J/K/mol"
                << std::endl;

      std::cout << "Composition: X = { ";
      for (int i = 0; i < xfrac.size(-1); ++i) {
        std::cout << "[" << xfrac.select(-1, i).min().item<double>() << ", "
                  << xfrac.select(-1, i).max().item<double>() << "], ";
      }
      std::cout << "}" << std::endl;
    }

    auto resid = (entropy_step - entropy_mole).abs().max().item<double>();
    if (resid < 10 * options->ftol()) {
      break;
    }
    if (resid < best_resid) {
      best_resid = resid;
      best_temp = temp.clone();
      best_pres = pres.clone();
    } else {
      relax *= 0.5;  // step made it worse: damp (active-set chatter)
    }

    auto pres1 = pres.clone();
    auto temp1 = temp.clone();

    // total gas mole fractions
    auto xg = xfrac.narrow(-1, 0, options->vapor_ids().size()).sum(-1);
    auto rho = compute("V->D", {conc});
    pres.set_(pres0 - 0.5 * (rho + rho0) * grav * dz);
    auto dlnp = pres.log() - pres1.log();
    temp.set_(temp1 * (1. + relax *
                                (entropy_step - entropy_mole +
                                 xg * constants::Rgas * dlnp) /
                                cp_mole));
    conc = compute("TPX->V", {temp, pres, xfrac});
    if (verbose) {
      std::cout << "  Sub-iter: pres = [" << pres.min().item<double>() << ", "
                << pres.max().item<double>() << "] Pa" << std::endl;
      std::cout << "            temp = [" << temp.min().item<double>() << ", "
                << temp.max().item<double>() << "] K" << std::endl;
      std::cout << "            dlnp = [" << dlnp.min().item<double>() << ", "
                << dlnp.max().item<double>() << "]" << std::endl;
    }
  }

  if (iter >= options->max_iter()) {
    if (best_temp.defined()) {  // restore the closest iterate, not the last one
      temp.set_(best_temp);
      pres.set_(best_pres);
    }
    TORCH_WARN("extrapolate_ad does not converge after ", options->max_iter(),
               " iterations (best residual ", best_resid, ").");
  }
}

}  // namespace kintera
