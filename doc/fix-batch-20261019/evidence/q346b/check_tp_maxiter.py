"""Q346b: does ThermoX.forward (equilibrate_tp) reach equilibrium on tests/jupiter.yaml
with the default eos max-iter (10)? Compare against the brute-force oracle tp_oracle.py.

Run: python check_tp_maxiter.py (from a scratch dir; see README.md)
"""
import numpy as np

from common import kintera, thermo_x, jupiter_x, torch, version_line
import tp_oracle

print(version_line())
P = 1.0e5
TS = [130.0, 150.0, 175.0, 200.0, 250.0]
ORDER = ["dry", "H2O", "NH3", "H2S", "H2O(l)", "NH3(s)", "NH4SH(s)"]

for mi in [10, 50]:
    op, th = thermo_x(max_iter=mi)
    sp, x = jupiter_x(op, n=len(TS))
    T = torch.tensor(TS)
    Pt = torch.full((len(TS),), P)
    d = torch.zeros(len(TS), 1)
    xx = x.clone()
    th.forward(T, Pt, xx, diag=d)
    print(f"\nmax-iter = {mi}")
    print(" T[K]   diag    x_H2O        x_NH3        x_H2S       "
          "max r_j(active)  oracle x_H2O  oracle x_NH3  oracle x_H2S")
    for k, T0 in enumerate(TS):
        n = np.array([float(xx[k, sp.index(s)]) for s in ORDER])
        r = tp_oracle.residuals(n, T0, P)
        act = n[4:] > 0
        rmax = np.max(np.abs(r[act]), initial=0.0)
        rpos = np.max(r[~act], initial=-np.inf)
        n0 = np.array([float(x[k, sp.index(s)]) for s in ORDER])
        o = tp_oracle.solve(n0, T0, P)
        on = o[1]
        print(f"{T0:5.0f} {d[k].item():7.0f}  {n[1]:.4e}  {n[2]:.4e}  {n[3]:.4e}  "
              f"{max(rmax, rpos if np.isfinite(rpos) else 0):12.3e}   "
              f"{on[1]:.4e}    {on[2]:.4e}    {on[3]:.4e}")
