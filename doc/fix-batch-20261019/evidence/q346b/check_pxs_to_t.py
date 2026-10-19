"""Q346b D8: ThermoX "PXS->T" (src/thermo/thermo_x.cpp:287-318) inverts S(T) at fixed P with
the update T <- T (1 + (S* - S(T)) / cp_frozen), where cp_frozen = "TV->cp" (no latent term).

Oracle: build an equilibrium state at a known T*, take its entropy S*, ask PXS->T for T, compare.
Also replays the same iteration in Python to log the trajectory, and evaluates the contraction factor
1 - cp_eff/cp_frozen with cp_eff = T dS/dT along the equilibrium path (centred finite difference).
The fixed-point iteration converges only if |1 - cp_eff/cp_frozen| < 1.

Run from any scratch dir (on failure kintera writes thermo_x_entropy_to_temp_<time>.pt into cwd).
"""
import warnings

from common import thermo_x, jupiter_x, torch, version_line

print(version_line())
P = 1.0e5


def equil_entropy(th, x, T):
    """Equilibrate x at (T, P) and return total volumetric entropy and cp."""
    xx = x.clone()
    t = torch.tensor([T])
    p = torch.tensor([P])
    th.forward(t, p, xx)
    conc = th.compute("TPX->V", [t, p, xx])
    return (th.compute("TPV->S", [t, p, conc]).item(),
            th.compute("TV->cp", [t, conc]).item())


for case, kw in [("jupiter (H2O 2.5e-3, NH3 3e-4, H2S 8e-5)", {}),
                 ("H2O-rich (H2O 5e-2)", {"xh2o": 5e-2})]:
    print(f"\n== {case}")
    print("  T*[K]  T(PXS->T, max-iter 10)  T(max-iter 100)  warn10  cp_eff/cp  1-cp_eff/cp")
    for Tstar in [150.0, 200.0, 250.0, 280.0, 300.0, 320.0]:
        op, th = thermo_x(max_iter=200)
        _, x = jupiter_x(op, **kw)
        Sstar, cp = equil_entropy(th, x, Tstar)
        dT = 0.01
        Sp, _ = equil_entropy(th, x, Tstar + dT)
        Sm, _ = equil_entropy(th, x, Tstar - dT)
        cp_eff = Tstar * (Sp - Sm) / (2 * dT)
        res = []
        for mi in (10, 100):
            op2, th2 = thermo_x(max_iter=mi)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                T = th2.compute("PXS->T", [torch.tensor([P]), x.clone(), torch.tensor([Sstar])])
            res.append((T.item(), len(w)))
        print(f"  {Tstar:5.0f}  {res[0][0]:22.6f}  {res[1][0]:15.6f}  {res[0][1]:6d}  "
              f"{cp_eff / cp:9.3f}  {1 - cp_eff / cp:10.3f}")
