"""Ch. 5 checks, chemical/phase equilibrium (EquilibriumTP, Nasa9LogK).

a. two-phase N2 + H2O(g) | H2O(l) vs analytic n_v = n_N2 p_sat / (p - p_sat);
b. Newton Jacobian J = sum nu (nu/n - nu_phase/N_phase) vs central FD of the residual;
c. 2 H2 + O2 <=> 2 H2O with Nasa9LogK at 3500 K: residual, H/O conservation,
   van 't Hoff d lnK/dT = Delta h / (R T^2) with h/RT from the bundled NASA-9 table.
"""
import math
import os
import warnings

from common import version_line, kintera, torch
from kintera import EquilibriumOptions, EquilibriumTP, nasa9_gibbs_rt
from kintera.equilibrium import Nasa9LogK

warnings.simplefilter("ignore")


def pf(ok):
    return "PASS" if ok else "FAIL"


def h2o_ideal(T):
    t = T / 273.16
    b, g = (24.845, 4.986009) if T > 273.16 else (22.98, 0.52)
    return (1 - 1 / t) * b - g * math.log(t) + math.log(611.7)


def residual(n, nu, phase, gas, P, p0, lnK):
    """sum_i nu_i ln a_i - lnK, a_i = n_i / N_phase (times P/p0 in the gas phase)."""
    tot = {}
    for ni, ph in zip(n, phase):
        tot[ph] = tot.get(ph, 0.0) + ni
    r = -lnK
    for ni, vi, ph in zip(n, nu, phase):
        la = math.log(ni / tot[ph]) + (math.log(P / p0) if ph == gas else 0.0)
        r += vi * la
    return r


def jac_formula(n, nu, phase):
    tot, dph = {}, {}
    for ni, vi, ph in zip(n, nu, phase):
        tot[ph] = tot.get(ph, 0.0) + ni
        dph[ph] = dph.get(ph, 0.0) + vi
    return sum(vi * (vi / ni - dph[ph] / tot[ph]) for ni, vi, ph in zip(n, nu, phase))


def check_ab():
    T, P, p0 = 300.0, 1.0e5, 1.0e5
    psat = math.exp(h2o_ideal(T))
    op = (EquilibriumOptions().components(["N2", "H2O", "H2O(l)"]).phases(["gas", "liquid"])
          .phase_ids([0, 0, 1]).reactions(["H2O <=> H2O(l)"]).gas_phase(0).standard_pressure(p0))
    lnK = math.log(p0 / psat)
    n0 = torch.tensor([1.0, 0.05, 0.05])
    n, gain, dg = EquilibriumTP(op)(torch.tensor(T), torch.tensor(P), n0, torch.tensor([lnK]))
    exact = 1.0 * psat / (P - psat)
    rel = abs(n[1].item() / exact - 1)
    ftol = op.ftol()
    print("== a. two-phase vapour-liquid, T=300 K, p=1e5 Pa, n0=(1, .05, .05)")
    print(f"  n_v={n[1].item():.14e} analytic={exact:.14e} rel={rel:.1e} tol 1e-10 {pf(rel <= 1e-10)}")
    print(f"  status={dg[0].item():.0f} (0 = converged) {pf(dg[0].item() == 0)}; iterations={dg[1].item():.0f};"
          f" reported error={dg[2].item():.1e} <= ftol={ftol:g} {pf(dg[2].item() <= ftol)}")
    dw = abs((n[1] + n[2]).item() / 0.1 - 1)
    print(f"  water conservation rel={dw:.1e} tol 1e-14 {pf(dw <= 1e-14)}")
    nu, phase = [0.0, -1.0, 1.0], [0, 0, 1]
    nn = [v.item() for v in n]
    J = jac_formula(nn, nu, phase)
    h = 1e-6 * nn[1]
    fd = (residual([a + h * b for a, b in zip(nn, nu)], nu, phase, 0, P, p0, lnK)
          - residual([a - h * b for a, b in zip(nn, nu)], nu, phase, 0, P, p0, lnK)) / (2 * h)
    relJ = abs(J / fd - 1)
    print("== b. Newton Jacobian at the converged state vs central FD along the reaction direction")
    print(f"  J={J:.12e} FD={fd:.12e} rel={relJ:.1e} tol 1e-8 {pf(relJ <= 1e-8)}"
          f"  (returned gain {gain.flatten()[0].item():.6e} is from the last Newton iterate)")


def nasa9_table(names):
    """Parse the bundled NASA-9 table: name line, then 20 numbers (low range 10, high range 10)."""
    path = os.path.join(os.path.dirname(kintera.__file__), "data", "nasa9.dat")
    lines = [ln.strip() for ln in open(path) if ln.strip() and not ln.startswith("#")]
    out = {}
    for k, ln in enumerate(lines):
        if ln in names:
            out[ln] = [float(v) for v in " ".join(lines[k + 1:k + 5]).split()]
    return out


def h_rt(c, T, tmid=1000.0):
    a = c[:10] if T < tmid else c[10:]
    return (-a[0] / T**2 + a[1] * math.log(T) / T + a[2] + a[3] * T / 2 + a[4] * T**2 / 3
            + a[5] * T**3 / 4 + a[6] * T**4 / 5 + a[8] / T)


def s_r(c, T, tmid=1000.0):
    a = c[:10] if T < tmid else c[10:]
    return (-a[0] / (2 * T**2) - a[1] / T + a[2] * math.log(T) + a[3] * T + a[4] * T**2 / 2
            + a[5] * T**3 / 3 + a[6] * T**4 / 4 + a[9])


def check_c():
    T, P = 3500.0, 1.0e5
    names, nu = ["H2", "O2", "H2O"], [-2.0, -1.0, 2.0]
    op = (EquilibriumOptions().components(names).phases(["gas"]).phase_ids([0, 0, 0])
          .reactions(["2 H2 + O2 <=> 2 H2O"]).gas_phase(0).standard_pressure(P))
    lk = Nasa9LogK(op)
    lnK = lk(torch.tensor(T), torch.tensor(P)).item()
    init = torch.tensor([0.6, 0.2, 0.2])
    n, _, dg = EquilibriumTP(op)(torch.tensor(T), torch.tensor(P), init, torch.tensor([lnK]))
    nn, n0 = [v.item() for v in n], init.tolist()
    r = residual(nn, nu, [0, 0, 0], 0, P, P, lnK)
    dH = abs((2 * nn[0] + 2 * nn[2]) / (2 * n0[0] + 2 * n0[2]) - 1)
    dO = abs((2 * nn[1] + nn[2]) / (2 * n0[1] + n0[2]) - 1)
    print("== c. 2 H2 + O2 <=> 2 H2O, Nasa9LogK, T=3500 K, p=p0=1e5 Pa")
    print(f"  lnK={lnK:.10f} status={dg[0].item():.0f} n={['%.6e' % v for v in nn]}")
    print(f"  |residual|={abs(r):.1e} tol 1e-10 {pf(abs(r) <= 1e-10)}")
    print(f"  H rel={dH:.1e} tol 1e-14 {pf(dH <= 1e-14)}; O rel={dO:.1e} tol 1e-14 {pf(dO <= 1e-14)}")
    tab = nasa9_table(names)
    g_tab = sum(v * (h_rt(tab[s], T) - s_r(tab[s], T)) for s, v in zip(names, nu))
    g_lib = (nasa9_gibbs_rt(torch.tensor([T]), names)[0] * torch.tensor(nu)).sum().item()
    dg_rel = abs(g_tab / g_lib - 1)
    print(f"  table parse: Delta g/RT table={g_tab:.12f} library={g_lib:.12f} rel={dg_rel:.1e}"
          f" tol 1e-12 {pf(dg_rel <= 1e-12)}")
    h = 1e-2
    fd = (lk(torch.tensor(T + h), torch.tensor(P)).item() - lk(torch.tensor(T - h), torch.tensor(P)).item()) / (2 * h)
    vh = sum(v * h_rt(tab[s], T) for s, v in zip(names, nu)) / T
    relv = abs(fd / vh - 1)
    print(f"  van 't Hoff: FD dlnK/dT={fd:.10e} Delta h/(R T^2)={vh:.10e} rel={relv:.1e} tol 1e-6 {pf(relv <= 1e-6)}")


if __name__ == "__main__":
    print(version_line())
    check_ab()
    check_c()
