"""Ch.3 condensate entropy: d(H - T S)/d(xi) at fixed T, p for vapour -> condensate equals -R T ln RH."""
import math

from common import thermo_x, species, jupiter_x, version_line, kintera, torch

R = 8.31446  # kintera Rgas (constants.h)


def gibbs(th, T, p, c):
    return th.compute("TV->H", [T, c]) - T * th.compute("TPV->S", [T, p, c])


if __name__ == "__main__":
    print(version_line())
    op, th = thermo_x(max_iter=100)
    sp = species(op)
    ngas = len(op.vapor_ids())
    iv, ic = sp.index("H2O"), sp.index("H2O(l)")
    stoich = th.buffer("stoich")
    worst = 0.0
    # (T, p, liquid mole fraction): sub- and supersaturated states with liquid present
    for T0, p0, xl in ((300., 1e5, 1e-3), (290., 2e5, 1e-3), (310., 5e4, 1e-4), (285., 1e5, 5e-4)):
        _, x = jupiter_x(op, xh2o=2.5e-2 if T0 < 300 else 3e-3)
        x[:, ic] = xl
        x[:, 0] = 0.0
        x[:, 0] = 1.0 - x.sum(-1)
        T, p = torch.tensor([T0]), torch.tensor([p0])
        c = th.compute("TPX->V", [T, p, x])
        rh = kintera.relative_humidity(T, c, stoich, op.nucleation(), ngas)[0, 0].item()
        d = 1e-6 * c[0, iv].item()
        cp_, cm_ = c.clone(), c.clone()
        cp_[0, iv] -= d; cp_[0, ic] += d
        cm_[0, iv] += d; cm_[0, ic] -= d
        dG = ((gibbs(th, T, p, cp_) - gibbs(th, T, p, cm_)) / (2 * d)).item()
        ref = -R * T0 * math.log(rh)
        err = abs(dG - ref) / (R * T0)
        worst = max(worst, err)
        print(f"   T={T0:.0f} K p={p0:.0e} Pa RH={rh:.6f}: dG/dxi = {dG:.6f} J/mol, "
              f"-R T ln RH = {ref:.6f} J/mol, |diff|/(R T) = {err:.2e}")
    tag = "PASS" if worst < 1e-6 else "FAIL"
    print(f"3e d(H - T S)/dxi vs -R T ln RH, worst |diff|/(R T): measured {worst:.3e}  tol 1e-06  {tag}")
