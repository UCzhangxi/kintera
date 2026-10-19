"""Q346d: condensate entropy of a precipitating copy X(p) that has no nucleation reaction of its own
(tests/jupiter.yaml: H2O(l,p) and NH3(s,p) have the same cv_R and u0_R as H2O(l) and NH3(s)).
eval_entropy_R (src/thermo/eval_uhs.cpp:443-455) solves the condensate entropies with a pseudo-inverse of the
nucleation stoichiometry block, so a copy in no nucleation reaction gets s = 0.
Oracle: invariance. Moving condensate from X to X(p) at fixed (T, P) must leave every total unchanged.
Reported: (s_X - s_X(p))/R = -dS_vol/(R c_m) (gas concentrations are identical in both states), change of molar and specific entropy, theta = exp(S_vol/cp_vol),
and the controls TV->cp and TV->H.
"""
from common import thermo_x, species, torch, version_line

print(version_line())
print("deck: tests/jupiter.yaml")
op, th = thermo_x()
sp = species(op)
print("species:", sp)
mu = th.mu
stoich = th.stoich


def diag(T, P, x):
    T = torch.tensor([T])
    P = torch.tensor([P])
    c = th.compute("TPX->V", [T, P, x])
    Sv = th.compute("TPV->S", [T, P, c])
    cpv = th.compute("TV->cp", [T, c])
    H = th.compute("TV->H", [T, c])
    sbar = (Sv / c.sum(-1)).item()                         # J/(mol K)
    s_kg = sbar / (mu * x).sum(-1).item()                  # J/(kg K)
    return sbar, s_kg, torch.exp(Sv / cpv).item(), cpv.item(), H.item(), Sv.item(), c[0]



print(" case                       T[K] P[bar] x_cond  (s_X-s_X(p))/R  dsbar[J/mol/K] ds[J/kg/K] dtheta[K]  dcp/cp   dH/H")
for vap, cl, pr, T, P, xv, xc in [("H2O", "H2O(l)", "H2O(l,p)", 280.0, 5e5, 1e-3, 1e-3),
                                  ("H2O", "H2O(l)", "H2O(l,p)", 280.0, 5e5, 1e-3, 1e-4),
                                  ("NH3", "NH3(s)", "NH3(s,p)", 140.0, 0.5e5, 1e-5, 2e-4)]:
    out = []
    for where in (cl, pr):
        x = torch.zeros(1, len(sp))
        x[0, sp.index(vap)] = xv
        x[0, sp.index(where)] = xc
        x[0, 0] = 1 - x[0, 1:].sum()
        out.append(diag(T, P, x))
    (a1, s1, t1, c1, h1, S1, cc1), (a2, s2, t2, c2, h2, S2, cc2) = out
    dsR = -(S2 - S1) / (8.31446261815324 * cc2[sp.index(pr)].item())
    print(f" {cl + ' -> ' + pr:26s} {T:4.0f} {P / 1e5:5.1f}  {xc:.0e}  {dsR:+14.4f}  "
          f"{a2 - a1:+12.5f}  {s2 - s1:+10.4f}  {t2 - t1:+9.4f}  "
          f"{(c2 - c1) / c1:+.1e}  {(h2 - h1) / abs(h1):+.1e}")
