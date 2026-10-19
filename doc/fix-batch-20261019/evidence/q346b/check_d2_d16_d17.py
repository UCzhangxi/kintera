"""Q346b D2, D16, D17 on tests/jupiter.yaml (ThermoX, TP).

D2  (src/thermo/equilibrate_uv.h:429-448, equilibrate_tp.h): start with ZERO vapour and condensate
    present; the solver must evaporate to saturation (or to complete evaporation).
D16 (src/thermo/thermo_x.cpp:364-367): "TPX->V" scales cloud concentrations by x_0 (species 0);
    probe x_0 = 0 with a cloud present.
D17 (src/thermo/eval_uhs.cpp:443-455): condensate entropies come from pinv(S_cloud^T) b. At an
    equilibrium state every nucleation reaction must have dG = 0, and the precipitating copies
    (H2O(l,p), NH3(s,p), same cv/u0 as their parent) should have the parent's chemical potential.
    dG/dxi by central finite difference of G = H - T S (totals from "TV->H", "TPV->S").
"""
import math

import numpy as np

from common import thermo_x, jupiter_x, torch, version_line, species
import tp_oracle

print(version_line())
P = 1.0e5

# ---------------- D2 ----------------
print("\n== D2: zero vapour, condensate present (cold start), max-iter 10 (default) and 50")
print("   oracle: the reaction of the condensate must end with r = 0 (condensate left) or r <= 0")
print("   (condensate gone); r = sum(a ln p) - logsvp, from tp_oracle.residuals")
op, th = thermo_x(max_iter=10)
sp = species(op)
for T0, src, dst, amt in [(280.0, "H2O(l)", "H2O", 2.5e-3), (300.0, "H2O(l)", "H2O", 2.5e-3),
                          (180.0, "NH3(s)", "NH3", 3e-4), (240.0, "NH4SH(s)", "NH3", 8e-5),
                          (280.0, "H2O(l)", "H2O", 5e-2), (160.0, "NH3(s)", "NH3", 3e-4),
                          (200.0, "NH4SH(s)", "NH3", 8e-5)]:
    for mi in (10, 50):
        op, th = thermo_x(max_iter=mi)
        x = torch.zeros(1, len(sp))
        x[0, sp.index(src)] = amt
        x[0, 0] = 1 - amt
        d = torch.zeros(1, 1)
        th.forward(torch.tensor([T0]), torch.tensor([P]), x, diag=d)
        order = ["dry", "H2O", "NH3", "H2S", "H2O(l)", "NH3(s)", "NH4SH(s)"]
        n = np.array([float(x[0, sp.index(s)]) for s in order])
        r = tp_oracle.residuals(n, T0, P)
        print(f"  {src:8s} T={T0:5.0f} max-iter {mi:2d}: diag {d.item():6.0f}  "
              f"vapour {n[order.index(dst)]:.4e}  cond left {n[order.index(src)]:.4e}  "
              f"r(rxn) {np.array2string(r, precision=2)}")

# ---------------- D16 ----------------
print("\n== D16: TPX->V with x_0 = 0 and a cloud present")
op, th = thermo_x()
for x0 in (0.5, 1e-12, 0.0):
    x = torch.zeros(1, len(sp))
    x[0, sp.index("H2O(l)")] = 0.1
    x[0, sp.index("H2O")] = 0.9 - x0
    x[0, 0] = x0
    c = th.compute("TPX->V", [torch.tensor([300.0]), torch.tensor([P]), x])
    cg = c[0, :4].sum().item()
    print(f"  x_0 = {x0:6.0e}: c_gas_total = {cg:.6e}  c_H2O(l) = {c[0, sp.index('H2O(l)')].item():.6e}"
          f"  expected {cg * 0.1 / 0.9:.6e}")

# ---------------- D17 ----------------
print("\n== D17: dG/dxi = sum_i nu_i mu_i at TP equilibrium (J/m^3 per mol/m^3 -> J/mol), / RT")
def G(th, T, Pt, c):
    return (th.compute("TV->H", [T, c]) - T * th.compute("TPV->S", [T, Pt, c])).item()


rxns = {"H2O -> H2O(l)": {"H2O": -1, "H2O(l)": 1},
        "NH3 -> NH3(s)": {"NH3": -1, "NH3(s)": 1},
        "NH3 + H2S -> NH4SH(s)": {"NH3": -1, "H2S": -1, "NH4SH(s)": 1},
        "H2O(l) -> H2O(l,p)": {"H2O(l)": -1, "H2O(l,p)": 1},
        "NH3(s) -> NH3(s,p)": {"NH3(s)": -1, "NH3(s,p)": 1}}
# the finite difference needs every reactant amount to be resolvable against the total G
# (relative step 1e-4 of the smallest amount), so each reaction is read at a state where its
# vapours are not vanishingly small
for T0, kw in [(150.0, {}), (200.0, {}), (280.0, {"xh2o": 5e-2})]:
    op, th = thermo_x(max_iter=100)
    _, x = jupiter_x(op, **kw)
    T = torch.tensor([T0])
    Pt = torch.tensor([P])
    th.forward(T, Pt, x)
    c0 = th.compute("TPX->V", [T, Pt, x])
    RT = 8.314462618 * T0
    print(f"  T = {T0:.0f} K {kw}: x =", {s: f"{x[0, i].item():.2e}" for i, s in enumerate(sp)})
    for name, nu in rxns.items():
        amts = [c0[0, sp.index(s)].item() for s in nu]
        if any(a == 0 for s, a in zip(nu, amts) if nu[s] < 0) or min(a for a in amts if a > 0) < 1e-6 * c0.sum().item():
            continue  # reactant absent or too small to resolve
        h = 1e-4 * min(a for a in amts if a > 0)
        cp_, cm_ = c0.clone(), c0.clone()
        for s, v in nu.items():
            cp_[0, sp.index(s)] += v * h
            cm_[0, sp.index(s)] -= v * h
        dG = (G(th, T, Pt, cp_) - G(th, T, Pt, cm_)) / (2 * h)
        print(f"    {name:24s} dG/(RT) = {dG / RT:+.4e}")
