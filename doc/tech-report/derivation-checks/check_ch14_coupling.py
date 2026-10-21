"""Chapter 14 checks: the snapy-kintera interface, kintera side, with inputs built as snapy builds them.

Mirrored snapy lines (snapy f93b1cf1):
  src/eos/moist_mixture.cpp:149-151   DY->V, VU->T, VT->P in _cons2prim
  src/eos/moist_mixture.cpp:166       VT->U in _prim2intEng
  src/eos/ideal_moist.cpp:225-231     IdealMoist internal energy (own formula, kintera R, mu, cref, uref)
  src/eos/ideal_moist.cpp:241         IdealMoist temperature
  src/mesh/meshblock.cpp:823-837      saturation adjustment: rho, ie = E - KE, yfrac = rho_i / rho, forward, rho_i = y rho
  examples/run_hydro.cpp:179-193      Y->X, TPX->V, slice, evolve_implicit, del_rho = del_conc / inv_mu
Oracles are numpy re-implementations of the textbook relations, never the call under test.
"""
import warnings

import numpy as np
import yaml

from common import kintera, torch, version_line, DECK

warnings.filterwarnings("ignore")
torch.manual_seed(0)
R = 8.31446  # J/(mol K), the value both codes use (kintera constants.h)

print(version_line())

with open(DECK) as f:
    card = yaml.safe_load(f)
comp = {s["name"]: s["composition"] for s in card["species"]}

op = kintera.ThermoOptions.from_yaml(DECK)
# read the card values before ThermoY.reset() shifts uref in place
cref = np.array(op.cref_R(), dtype=float)
uref = np.array(op.uref_R(), dtype=float)
Tref = float(op.Tref())
th = kintera.ThermoY(op)
th.to(torch.float64)
names = list(op.species())
nv = len(op.vapor_ids())
ns = len(names)
ny = ns - 1
mu = 1.0 / th.inv_mu.numpy()
u0p = uref - cref * Tref  # J/mol / R, offset at T = 0 (conventions of the spec)
elements = sorted({e for n in names for e in comp[n]})
A = np.array([[comp[n].get(e, 0.0) for e in elements] for n in names])  # (ns, nel)


def tol_line(label, err, tol, what):
    print(f"({label}) {what}: max rel err {err:.2e} (tol {tol:g}) {'PASS' if err <= tol else 'FAIL'}")


# ---- a state built as snapy holds it: total rho, mass fractions (ny, ncell), internal energy J/m^3
T = np.array([140., 160., 200., 250., 280., 300.])
P = np.array([0.5e5, 1e5, 2e5, 4e5, 5e5, 6e5])
x = np.zeros((T.size, ns))
x[:, names.index("H2O")] = 0.01
x[:, names.index("NH3")] = 3e-3
x[:, names.index("H2S")] = 1e-3
x[:, 0] = 1 - x.sum(1)
conc = x * (P / (R * T))[:, None]           # mol/m^3, all gas, supersaturated in most cells
ivol = conc * mu                              # kg/m^3 per species (kintera "V")
rho = ivol.sum(1)
yfrac = (ivol[:, 1:] / rho[:, None]).T        # (ny, ncell): snapy's prim ICY rows
ie_np = (conc * R * (u0p + cref * T[:, None])).sum(1)   # textbook U = sum c_i R (u0_i' + cv_i T)
escale = (conc * R * cref * T[:, None]).sum(1)          # thermal energy scale (U itself is 0 at T = Tref)

tr = lambda a: torch.tensor(a, dtype=torch.float64)
V = th.compute("DY->V", [tr(rho), tr(yfrac)]).numpy()
tol_line("a", (np.abs(V - ivol).max(1) / rho).max(), 1e-14, "DY->V (snapy moist_mixture.cpp:149) against rho*(1-sum y), rho*y")
Y = th.compute("V->Y", [tr(V)]).numpy()
tol_line("b", np.abs(Y - yfrac).max() / yfrac.max(), 1e-14, "V->Y after DY->V returns the mass fractions")
U = th.compute("VT->U", [tr(V), tr(T)]).numpy()
tol_line("c", (np.abs(U - ie_np) / escale).max(), 1e-12, "VT->U [J/m^3] against sum c_i R (u0_i - cv_i Tref + cv_i T), c = rho_i/mu_i")
Tb = th.compute("VU->T", [tr(V), tr(U)]).numpy()
tol_line("d", np.abs(Tb / T - 1).max(), 1e-10, "VU->T(VT->U(T)) round trip (moist_mixture.cpp:150)")
Pk = th.compute("VT->P", [tr(V), tr(T)]).numpy()
tol_line("e", np.abs(Pk / P - 1).max(), 1e-14, "VT->P against R T sum_gas rho_i/mu_i (moist_mixture.cpp:151)")
Tp = th.compute("PV->T", [tr(P), tr(V)]).numpy()
tol_line("f", np.abs(Tp / T - 1).max(), 1e-14, "PV->T (moist_mixture.cpp:290) inverts VT->P")
X = th.compute("Y->X", [tr(yfrac)]).numpy()
tol_line("g", np.abs(X - x).max(), 1e-15, "Y->X (run_hydro.cpp:179) against x_i = (y_i/mu_i)/sum_j(y_j/mu_j), dry included")

# ---- IdealMoist keeps its own copy of the energy model (ideal_moist.cpp:30-51, 225-231, 241)
cvd_R, mud = cref[0], mu[0]
Rd = R / mud
cv_ratio_m1 = (cref[1:] * R / mu[1:]) / (cref[0] * Rd) - 1
inv_mu_ratio_m1 = mud / mu[1:] - 1
gammad = (cvd_R + 1) / cvd_R
u0_mass = u0p * R / mu                        # th.reset() already shifted uref; snapy reads the shifted copy
fsig = 1 + cv_ratio_m1 @ yfrac
feps = 1 + inv_mu_ratio_m1[: nv - 1] @ yfrac[: nv - 1] - yfrac[nv - 1:].sum(0)
ie_im = P * fsig / feps / (gammad - 1) + rho * (1 - yfrac.sum(0)) * u0_mass[0] + rho * (u0_mass[1:] @ yfrac)
tol_line("h", (np.abs(ie_im - U) / escale).max(), 1e-12, "IdealMoist W->I formula against kintera VT->U at the same state")
T_im = P / (rho * Rd * feps)
tol_line("i", np.abs(T_im / T - 1).max(), 1e-13, "IdealMoist W->T = p/(rho Rd f_eps) against the state temperature")
shifted = np.allclose(np.array(op.uref_R()), u0p)
print(f"(j) the options object snapy reads after ThermoYImpl::create holds the T=0 offsets (uref - cref Tref): {shifted} "
      f"{'PASS' if shifted else 'FAIL'}")

# ---- saturation adjustment exactly as meshblock.cpp:823-837 (KE = 0 here, so ie = E)
rho_t, ie_t, y_t = tr(rho), tr(U), tr(yfrac.copy())
dry_before = rho * (1 - yfrac.sum(0))           # hydro_u[IDN] is not touched by step (6)
diag = torch.zeros(T.size, 1, dtype=torch.float64)
th.forward(rho_t, ie_t, y_t, True, diag)
print("(k0) diag per cell at the default max_iter " + str(op.max_iter()) + " (negative = failed, D4 filed): "
      + " ".join(f"{v:.0f}" for v in diag.numpy().ravel()) + " INFO")
y1 = y_t.numpy()
rho_i1 = np.vstack([dry_before, y1 * rho])      # snapy: hydro_u[ICY:] = yfrac * rho (meshblock.cpp:837)
moved = np.abs(y1 - yfrac).max() / yfrac.max()
print(f"(k) adjustment moved mass fractions by up to {moved:.2e} of the largest (state was supersaturated) "
      f"{'PASS' if moved > 1e-3 else 'FAIL'}")
tol_line("l", np.abs(rho_i1.sum(0) / rho - 1).max(), 1e-14, "total density rho_dry + sum y' rho equals rho (dry row untouched)")
mol0 = conc @ A
mol1 = (rho_i1.T / mu) @ A
tol_line("m", (np.abs(mol1 - mol0) / mol0.max(0)).max(), 1e-13, "element moles H, He, N, O, S per cell conserved")
V1 = rho_i1.T
T1 = th.compute("VU->T", [tr(V1), tr(U)]).numpy()
# independent temperature from the linear energy model with the new composition and the SAME ie
c1 = V1 / mu
T1_np = (U / R - (c1 * u0p).sum(1)) / (c1 * cref).sum(1)
tol_line("n", np.abs(T1 / T1_np - 1).max(), 1e-12, "snapy's next VU->T at fixed ie (meshblock.cpp:825) = linear-model T")
dT = T1 - T
print("(o) latent warming T' - T per cell [K]: " + " ".join(f"{v:.3f}" for v in dT) + " INFO")
# phase-equilibrium at T': partial pressure of each condensing vapor vs the card's saturation curve
thx_op = kintera.ThermoOptions.from_yaml(DECK)
thx = kintera.ThermoX(thx_op)
thx.to(torch.float64)
X1 = th.compute("Y->X", [tr(y1)])
P1 = th.compute("VT->P", [tr(V1), tr(T1)])
c1x = thx.compute("TPX->V", [tr(T1), P1, X1])
rh = kintera.relative_humidity(tr(T1), c1x, thx.stoich, thx_op.nucleation()).numpy()
print("(p) max relative humidity per cell at (T', p') after the adjustment: "
      + " ".join(f"{v:.6f}" for v in rh.max(-1)) + " INFO")

# ---- failures are counted and the state is still written (thermo_y.cpp:364-378)
op2 = kintera.ThermoOptions.from_yaml(DECK)
op2.max_iter(1)
th2 = kintera.ThermoY(op2)
th2.to(torch.float64)
y2 = tr(yfrac.copy())
th2.forward(tr(rho), tr(U), y2, False)
nfail = th2.take_saturation_adjustment_failures()
again = th2.take_saturation_adjustment_failures()
dens2 = (1 - yfrac.sum(0)) * rho + (y2.numpy() * rho).sum(0)
print(f"(q) max_iter = 1: {nfail} failed cell(s) counted, count reset to {again} on the second read "
      f"{'PASS' if nfail > 0 and again == 0 else 'FAIL'}")
tol_line("r", np.abs(dens2 / rho - 1).max(), 1e-14, "failed cells: written state still conserves total density")

# ---- kinetics coupling, as run_hydro.cpp:179-193 (units of the hand-back)
#  (s) TPX->V on the adjusted state against rho_i / mu_i: the driver feeds the TPX->V concentrations
c_tpx = c1x.numpy()
err_g = np.abs(c_tpx[:, :nv] / c1[:, :nv] - 1).max()
tol_line("s", err_g, 1e-12, "gas concentrations from Y->X then TPX->V equal rho_i/mu_i [mol/m^3]")
cl = c1[:, nv:]
mask = cl > 1e-12 * c1.sum(1, keepdims=True)
err_c = np.abs(c_tpx[:, nv:][mask] / cl[mask] - 1).max() if mask.any() else 0.0
print(f"(t) cloud concentrations from TPX->V against rho_i/mu_i: max rel diff {err_c:.2e} "
      f"(filed as D16; the driver's tendencies start from these) INFO")
#  (u) del_rho = del_conc / inv_mu conserves mass for any stoichiometric change
S = th.stoich.numpy()                           # (ns, nreact), mass-balanced reactions of the card
rng = np.random.default_rng(0)
xi = rng.normal(size=(T.size, S.shape[1])) * 1e-3
del_conc = (S @ xi.T).T[:, 1:]                  # kinetics species = thermo species minus dry (run_hydro.cpp:184)
del_rho = del_conc / th.inv_mu.numpy()[1:]      # run_hydro.cpp:192
tol_line("u", np.abs(del_rho.sum(1)).max() / np.abs(del_rho).max(), 1e-14,
         "sum_i M_i delta_i = 0 for a stoichiometric change (mass hand-back)")
#  (v) holding E fixed while kinetics converts vapor to cloud = the fixed-U Jacobian assumption of C6-g;
#      the drivers pass TV->cp as the cvol argument (run_hydro.cpp:181, 187). Size of that substitution:
cp_vol = thx.compute("TV->cp", [tr(T1), c1x]).numpy()
cv_vol = th.compute("VT->cv", [tr(V1), tr(T1)]).numpy()
print("(v) ratio of the volumetric heat capacity the drivers pass (TV->cp) to the C_V of the fixed-U Jacobian: "
      + " ".join(f"{v:.4f}" for v in cp_vol / cv_vol) + " EXPECTED-FAIL (S14-1)")

# ---- (w) Lie splitting e^{dt B} e^{dt A}: local error -> dt^2/2 [B, A] (report eq-ch14-kinetics-splitting)
Am = torch.randn(3, 3, generator=torch.Generator().manual_seed(1), dtype=torch.float64)
Bm = torch.randn(3, 3, generator=torch.Generator().manual_seed(2), dtype=torch.float64)
comm = Bm @ Am - Am @ Bm
rels = []
for dt in (1e-2, 1e-3):
    err = torch.linalg.matrix_exp(dt * Bm) @ torch.linalg.matrix_exp(dt * Am) - torch.linalg.matrix_exp(dt * (Am + Bm))
    rels.append(float((err / dt**2 - 0.5 * comm).abs().max() / (0.5 * comm).abs().max()))
print(f"(w) split-step local error / dt^2 against [B,A]/2: rel diff {rels[0]:.2e} at dt=1e-2, {rels[1]:.2e} at dt=1e-3 "
      f"(first order in dt; tol 2e-2 at 1e-2) {'PASS' if rels[0] < 2e-2 and rels[1] < rels[0] / 5 else 'FAIL'}")
