"""Q346d: step-size dependence of the pseudo-adiabat (rainout) of extrapolate_dlnp. Same card and ODE oracle
as the Q346b D14 check (below); the end point 0.5 bar is reached with several step sizes and compared to a
fine RK4 oracle (dlnP = -1e-4). A scheme with no truncation error in dlnP gives a step-independent result.
Original Q346b D14 + D15 notes: ThermoX.extrapolate_dlnp, reversible (rainout=False) and pseudo (rainout=True,
src/thermo/extrapolate_ad.cpp:117-136) against an independent ODE for a dry gas + one condensable
(H2O, h2o_ideal svp, Tref = 0 so u = u0 + cv T). Per mole of dry gas, with f = p_v/P, n_v = f/(1-f),
a = dln svp / dlnT (finite difference of the re-typed svp), L = h_v - h_l (from the card's u0, cv):
  dlnT/dlnP = [R + (L/T) n_v]/(1-f) / [c_p,tot + R f a/(1-f) - n_v R a + (L/T) n_v a/(1-f)]
with c_p,tot = R[(cv_d+1) + n_v (cv_v+1) + n_l cv_l]; reversible: n_l = W - n_v (W fixed), pseudo: n_l = 0.
This follows from dS_total = 0 (reversible) and dS_gas = s_l dn_v (pseudo), with s_v - s_l = L/T.
RK4 in lnP. D15: the loop's stopping test is |s_target - s| < 10 ftol on the MOLAR entropy (J/K/mol).
"""
import math

from common import torch, version_line, kintera
import tp_oracle

print(version_line())
SC = "."
# cv_l = cv_v + 1 + gamma and u0_l = -beta T3 make the card Clausius-Clapeyron consistent with the
# liquid branch of h2o_ideal (T > 273.16 K); the run stays above 273.16 K.
CV_D, CV_V, CV_L, U0_L = 2.5, 2.5, 8.486009, -6786.6602
CARD = f"""
reference-state: {{Tref: 0., Pref: 1.0e5}}
species:
- {{name: dry, composition: {{H: 1.5, He: 0.15}}, cv_R: {CV_D}}}
- {{name: H2O, composition: {{H: 2, O: 1}}, cv_R: {CV_V}, u0_R: 0.}}
- {{name: H2O(l), composition: {{H: 2, O: 1}}, cv_R: {CV_L}, u0_R: {U0_L}}}
reactions:
- {{equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {{formula: h2o_ideal}}}}
dynamics: {{equation-of-state: {{max-iter: 50}}}}
"""
card = f"{SC}/d14.yaml"
open(card, "w").write(CARD)
R = 8.314462618
T0, P0, P1 = 300.0, 1.0e5, 5.0e4
DLNP, NSTEP = None, None


def rhs(lnT, lnP, W, pseudo):
    T, P = math.exp(lnT), math.exp(lnP)
    pv = math.exp(tp_oracle.h2o_ideal(T))
    f = pv / P
    nv = f / (1 - f)
    nl = 0.0 if pseudo else W - nv
    h = 1e-4
    a = T * (tp_oracle.h2o_ideal(T + h) - tp_oracle.h2o_ideal(T - h)) / (2 * h)
    L = R * ((CV_V + 1) * T - (U0_L + CV_L * T))
    cp = R * ((CV_D + 1) + nv * (CV_V + 1) + nl * CV_L)
    num = (R + L / T * nv) / (1 - f)
    den = cp + R * f * a / (1 - f) - nv * R * a + L / T * nv * a / (1 - f)
    return num / den


def oracle(pseudo):
    pv0 = math.exp(tp_oracle.h2o_ideal(T0))
    W = pv0 / (P0 - pv0)
    lnT, lnP = math.log(T0), math.log(P0)
    out = {}
    for k in range(NSTEP):
        k1 = rhs(lnT, lnP, W, pseudo)
        k2 = rhs(lnT + 0.5 * DLNP * k1, lnP + 0.5 * DLNP, W, pseudo)
        k3 = rhs(lnT + 0.5 * DLNP * k2, lnP + 0.5 * DLNP, W, pseudo)
        k4 = rhs(lnT + DLNP * k3, lnP + DLNP, W, pseudo)
        lnT += DLNP / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        lnP += DLNP
        out[k + 1] = math.exp(lnT)
    return out


op = kintera.ThermoOptions.from_yaml(card)
th = kintera.ThermoX(op)
th.to(torch.float64)


def kin(rainout):
    pv0 = math.exp(tp_oracle.h2o_ideal(T0))
    x = torch.tensor([[1 - pv0 / P0, pv0 / P0, 0.0]])
    T = torch.tensor([T0])
    P = torch.tensor([P0])
    out = {}
    for k in range(NSTEP):
        th.extrapolate_dlnp(T, P, x, DLNP, rainout=rainout)
        out[k + 1] = (T.item(), P.item(), x[0, 2].item())
    return out


print(f"card: {card}; start T0 = {T0} K, P0 = {P0:.0e} Pa (saturated), end P1 = {P1:.0e} Pa")
DLNP = math.log(P1 / P0) / 6931; NSTEP = 6931
o_rev, o_ps = oracle(False)[NSTEP], oracle(True)[NSTEP]
print(f"  oracle (RK4, {NSTEP} steps): reversible {o_rev:.5f} K, pseudo {o_ps:.5f} K")
print("  nstep   dlnP       T_rev-oracle[K]  T_pseudo-oracle[K]")
for n in (35, 70, 139, 277, 555):
    DLNP = math.log(P1 / P0) / n; NSTEP = n
    Tr = kin(False)[n][0]; Tp = kin(True)[n][0]
    print(f"  {n:5d}  {DLNP:+.5f}   {Tr - o_rev:+12.5f}   {Tp - o_ps:+12.5f}")
