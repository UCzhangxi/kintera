"""Q346b D17 reach: a host diagnostic that computes entropy = TPV->S / (n mu) and
theta = exp(S_vol / cp_vol) on the run-time state, which holds precipitating condensates made by
coagulation. card_two_cloud_tref0.yaml has H2O(l) => H2O(l,p) and NH3(s) => NH3(s,p) coagulation.
H2O(l,p) has the same cv_R and u0_R as H2O(l) (same for NH3), so moving condensate from the
cloud copy to the precipitating copy at fixed (T, P) must leave every thermodynamic total unchanged.
Oracle: invariance. Reported: change of specific entropy and theta, and of TV->cp and TV->H (control).
"""
import os

from common import thermo_x, species, torch, version_line

CARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "card_two_cloud_tref0.yaml")
print(version_line())
print("card:", os.path.basename(CARD))
op, th = thermo_x(CARD)
sp = species(op)
print("species:", sp)
mu = th.mu


def diag(T, P, x):
    T = torch.tensor([T])
    P = torch.tensor([P])
    c = th.compute("TPX->V", [T, P, x])
    Sv = th.compute("TPV->S", [T, P, c])
    cpv = th.compute("TV->cp", [T, c])
    H = th.compute("TV->H", [T, c])
    s = (Sv / c.sum(-1) / (mu * x).sum(-1)).item()  # J/(kg K)
    return s, torch.exp(Sv / cpv).item(), cpv.item(), H.item()


print(" case                         T[K]  P[bar] x_cond   ds[J/kg/K]  dtheta[K]  theta[K]   dcp/cp     dH/H")
for vap, cl, pr, T, P, xv, xc in [("H2O", "H2O(l)", "H2O(l,p)", 280.0, 5e5, 1e-3, 1e-3),
                                  ("H2O", "H2O(l)", "H2O(l,p)", 280.0, 5e5, 1e-3, 1e-4),
                                  ("NH3", "NH3(s)", "NH3(s,p)", 140.0, 0.5e5, 1e-5, 2e-4)]:
    out = []
    for where in (cl, pr):
        x = torch.zeros(1, len(sp))
        x[0, sp.index(vap)] = xv
        x[0, sp.index(where)] = xc
        x[0, 0] = 1 - xv - xc
        out.append(diag(T, P, x))
    (s1, t1, c1, h1), (s2, t2, c2, h2) = out
    print(f" {cl + ' -> ' + pr:28s} {T:5.0f} {P / 1e5:6.1f}  {xc:.0e}  {s2 - s1:+10.4f}  {t2 - t1:+9.4f}  "
          f"{t1:8.3f}  {(c2 - c1) / c1:+.1e}  {(h2 - h1) / abs(h1):+.1e}")
