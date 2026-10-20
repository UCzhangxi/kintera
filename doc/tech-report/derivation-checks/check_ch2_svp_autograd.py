"""Ch. 2 LogSVPFunc backward pass (src/thermo/log_svp.cpp), reached through the evaporation module.

LogSVPFunc::apply is the autograd path of ln K(T); its one caller is EvaporationImpl::forward
(src/kinetics/evaporation.cpp), which Python binds as kintera.Evaporation. With diff_T = diff_P = 0 its rate
constant for CH4(s,p) => CH4 is  w(T) = kappa (K(T) - c_v),  K = exp(ln p(T)) / (R T),  kappa independent of T,
so every T-derivative of w is a closed form in ln p, (ln p)' and (ln p)'' of the ideal formula.

(a) first derivative: autograd dw/dT against kappa K ((ln p)' - 1/T), and torch.autograd.gradcheck.
(a3)-(a5) step 1 (an expanded leaf gives the diagonal Jacobian), and step 3: forward_with_rate_constants with
    evolve_temperature makes the expanded temperature the leaf, so rc_ddT is per reaction; an unexpanded T passed
    to Evaporation.forward gets the sum over reactions from the backward pass of the expansion.
(b) second derivative: the backward multiplies by a derivative evaluated outside autograd, so a second
    differentiation sees (ln p)' as a constant and drops the (ln p)'' term. Predicted autograd value:
    kappa K [((ln p)' - 1/T)^2 + 1/T^2]; true value adds kappa K (ln p)''.
"""
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera as kt, torch  # noqa: E402

print(version_line())
R = kt.constants.Rgas
tmp = tempfile.mkdtemp()
fails = 0


def report(name, val, tol, ok):
    global fails
    fails += not ok
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {'PASS' if ok else 'FAIL'}")


T3, P3, beta, gamma, D, vm, d = 90.67, 11690.0, 12.87, 1.5, 2.0e-5, 30.8e-6, 1.0e-5
card = f"""
reference-state: {{Tref: 300., Pref: 1.e5}}
species:
  - {{name: dry, composition: {{H: 2}}, cv_R: 2.5}}
  - {{name: CH4, composition: {{C: 1, H: 4}}, cv_R: 3.0}}
  - {{name: "CH4(s,p)", composition: {{C: 1, H: 4}}, cv_R: 4.0, u0_R: -1166.9229}}
reactions:
  - equation: CH4(s,p) => CH4
    type: evaporation
    rate-constant: {{formula: ideal, T3: {T3}, P3: {P3}, beta: {beta}, gamma: {gamma},
                    diff_c: {D}, diff_T: 0., diff_P: 0., vm: {vm}, diameter: {d}}}
"""
path = os.path.join(tmp, "evap.yaml")
with open(path, "w") as f:
    f.write(card)
op = kt.KineticsOptions.from_yaml(path)
kin = kt.Kinetics(op)
names = op.species()
kappa = 12.0 * D * vm / d**2
cp, cv = 0.7, 0.2


def lnp(T):  # T < T3 here: solid pair, which defaults to (beta, gamma)
    t = T / T3
    return math.log(P3) + beta * (1.0 - 1.0 / t) - gamma * math.log(t)


def lnp1(T):
    t = T / T3
    return (beta / t**2 - gamma / t) / T3


def lnp2(T):
    t = T / T3
    return (-2.0 * beta / t**3 + gamma / t**2) / T3**2


evap = kt.Evaporation(op.evaporation())
stoich = kin.stoich
conc = torch.zeros(1, len(names), 1)  # (batch, species, reactions): the layout Kinetics.forward passes
conc[0, names.index("CH4"), 0] = cv
conc[0, names.index("CH4(s,p)"), 0] = cp
P = torch.tensor([1.0e5])


def w(Tt):
    """Rate constant of the evaporation reaction (per unit c_p) at temperature Tt, shape (1,)."""
    return evap.forward(Tt.view(1, 1), P, conc, {"stoich": stoich})[0, 0]


worst1, worst2, worstp = 0.0, 0.0, 0.0
Ts = (70.0, 75.0, 80.0, 85.0)
print(f"kintera.Evaporation, CH4(s,p) => CH4, ideal formula beta={beta} gamma={gamma}, c_v={cv}; T in {Ts} K")
for T in Ts:
    K = math.exp(lnp(T)) / (R * T)
    assert K > cv, "the state must be subsaturated so the rate is not clamped"
    Tt = torch.tensor([T], requires_grad=True)
    (g1,) = torch.autograd.grad(w(Tt), Tt, create_graph=True)
    (g2,) = torch.autograd.grad(g1.sum(), Tt)
    a = lnp1(T) - 1.0 / T
    ref1 = kappa * K * a
    true2 = kappa * K * (a * a + 1.0 / T**2 + lnp2(T))
    pred2 = kappa * K * (a * a + 1.0 / T**2)
    e1 = abs(g1.item() / ref1 - 1)
    e2 = abs(g2.item() / pred2 - 1)
    worst1, worst2 = max(worst1, e1), max(worst2, e2)
    worstp = max(worstp, abs(g2.item() / true2 - 1))
    print(f"   T={T}: dw/dT autograd {g1.item():.10e} analytic {ref1:.10e};"
          f" d2w/dT2 autograd {g2.item():.6e} predicted(no lnp'') {pred2:.6e} true {true2:.6e}")
report("(a1) autograd dw/dT vs kappa K ((ln p)' - 1/T), worst rel", worst1, 1e-12, worst1 <= 1e-12)
Tg = torch.tensor([78.0], requires_grad=True)
ok = torch.autograd.gradcheck(lambda x: w(x), (Tg,), eps=1e-6, atol=1e-10, rtol=1e-7, raise_exception=False)
report("(a2) torch.autograd.gradcheck at 78 K (eps 1e-6, atol 1e-10, rtol 1e-7) fails (1) or not (0)", float(not ok), 0, ok)
# (a3) two reactions with an already-expanded (1, 2) temperature leaf: the gradient of reaction j lands on column j
# only, which is the diagonal Jacobian of step 1.
card2 = card + f"""  - equation: NH3(s,p) => NH3
    type: evaporation
    rate-constant: {{formula: ideal, T3: 195.4, P3: 6060., beta: 20.64, gamma: 1.43,
                    diff_c: {D}, diff_T: 0., diff_P: 0., vm: {vm}, diameter: {d}}}
"""
card2 = card2.replace("species:\n", "species:\n  - {name: NH3, composition: {N: 1, H: 3}, cv_R: 3.0}\n"
                      "  - {name: \"NH3(s,p)\", composition: {N: 1, H: 3}, cv_R: 4.0, u0_R: -2000.}\n", 1)
path2 = os.path.join(tmp, "evap2.yaml")
with open(path2, "w") as f:
    f.write(card2)
op2 = kt.KineticsOptions.from_yaml(path2)
kin2 = kt.Kinetics(op2)
n2 = op2.species()
ev2 = kt.Evaporation(op2.evaporation())
st2 = kin2.stoich
c2 = torch.zeros(1, len(n2), 2)
for col in range(2):
    c2[0, n2.index("CH4"), col] = cv
    c2[0, n2.index("NH3"), col] = 1e-3
    c2[0, n2.index("CH4(s,p)"), col] = cp
    c2[0, n2.index("NH3(s,p)"), col] = cp
T2 = torch.tensor([[78.0, 78.0]], requires_grad=True)
rc = ev2.forward(T2, P, c2, {"stoich": st2})
irx = [k for k in range(st2.size(1)) if st2[n2.index("CH4"), k] > 0][0]
(gcol,) = torch.autograd.grad(rc[0, irx], T2)
Tq = 78.0
Kq = math.exp(lnp(Tq)) / (R * Tq)
ref = kappa * Kq * (lnp1(Tq) - 1.0 / Tq)
off = gcol[0, 1 - irx].abs().item()
e3 = abs(gcol[0, irx].item() / ref - 1)
print(f"   two reactions at 78 K: d w_CH4 / d T[:, CH4 column] = {gcol[0, irx].item():.10e} (analytic {ref:.10e}),"
      f" on the other column {off:.1e}")
report("(a3) expanded leaf (step 1, diagonal Jacobian): rel error on own column + |value on the other column|", e3 + off, 1e-12,
       e3 + off <= 1e-12)
def lnp_g(T, T3_, P3_, b, g):
    t = T / T3_
    return math.log(P3_) + b * (1.0 - 1.0 / t) - g * math.log(t)


def dlnp_g(T, T3_, b, g):
    t = T / T3_
    return (b / t**2 - g / t) / T3_


FITS = {"CH4": (T3, P3, beta, gamma), "NH3": (195.4, 6060.0, 20.64, 1.43)}


def own_dwdT(gas, T, cgas):
    """d w_r/dT of one evaporation reaction alone: kappa K (L' - 1/T) if subsaturated, else 0 (rate clamped)."""
    T3_, P3_, b, g = FITS[gas]
    K = math.exp(lnp_g(T, T3_, P3_, b, g)) / (R * T)
    return kappa * K * (dlnp_g(T, T3_, b, g) - 1.0 / T) if K > cgas else 0.0


# (a4) the kinetics path: forward_with_rate_constants expands T and makes the expanded copy the autograd leaf
# (temp1), so rc_ddT holds each reaction's own dk_r/dT in its own column; nothing is summed.
op2.evolve_temperature(True)
kin2e = kt.Kinetics(op2)
col = {"CH4": irx, "NH3": 1 - irx}
worst4 = 0.0
for Tq, cnh3 in ((78.0, 1e-3), (150.0, 1e-3)):
    cc = torch.zeros(1, len(n2))
    cc[0, n2.index("CH4")] = cv
    cc[0, n2.index("NH3")] = cnh3
    cc[0, n2.index("CH4(s,p)")] = cp
    cc[0, n2.index("NH3(s,p)")] = cp
    out = kin2e.forward_with_rate_constants(torch.tensor([Tq]), P, cc)
    rcT = out[2][0]
    own = {gname: own_dwdT(gname, Tq, cc[0, n2.index(gname)].item()) for gname in col}
    for gname, j in col.items():
        ref_ = own[gname]
        e = abs(rcT[j].item() - ref_) / max(abs(ref_), 1e-300) if ref_ != 0 else abs(rcT[j].item())
        worst4 = max(worst4, e)
    print(f"   T={Tq}: rc_ddT [CH4 column, NH3 column] = [{rcT[col['CH4']].item():.6e}, {rcT[col['NH3']].item():.6e}];"
          f" own derivatives [{own['CH4']:.6e}, {own['NH3']:.6e}]; their sum {own['CH4'] + own['NH3']:.6e}")
report("(a4) forward_with_rate_constants rc_ddT: each column is its own reaction's dk_r/dT, worst rel (abs if 0)",
       worst4, 1e-12, worst4 <= 1e-12)

# (a5) an unexpanded T with requires_grad, passed to Evaporation.forward, which expands it itself: the gradient of
# sum_r g_r w_r with respect to the one cell temperature is sum_r g_r dw_r/dT (backward of the expansion).
Tq = 150.0
cu = torch.zeros(1, len(n2))
cu[0, n2.index("CH4")] = cv
cu[0, n2.index("NH3")] = 1e-3
cu[0, n2.index("CH4(s,p)")] = cp
cu[0, n2.index("NH3(s,p)")] = cp
Tu = torch.tensor([Tq], requires_grad=True)
wu = ev2.forward(Tu, P, cu, {"stoich": st2})
gw = torch.zeros(2)
gw[col["CH4"]], gw[col["NH3"]] = 1.0, 2.0
(gsum,) = torch.autograd.grad((wu[0] * gw).sum(), Tu)
refsum = 1.0 * own_dwdT("CH4", Tq, cv) + 2.0 * own_dwdT("NH3", Tq, 1e-3)
e5 = abs(gsum.item() / refsum - 1)
print(f"   unexpanded T = {Tq} K through Evaporation.forward: d(w_CH4 + 2 w_NH3)/dT = {gsum.item():.10e},"
      f" sum of own derivatives {refsum:.10e}")
report("(a5) unexpanded T: gradient is the weighted sum over reactions, rel", e5, 1e-12, e5 <= 1e-12)

report("(b1) autograd d2w/dT2 vs prediction without (ln p)'', worst rel", worst2, 1e-12, worst2 <= 1e-12)
report("(b2) |autograd d2w/dT2 / true - 1|, must EXCEED tol (the dropped (ln p)'' term)", worstp, 1e-2,
       worstp >= 1e-2)
ok2 = torch.autograd.gradgradcheck(lambda x: w(x), (Tg,), eps=1e-6, atol=1e-10, rtol=1e-7,
                                   raise_exception=False)
report("(b3) torch.autograd.gradgradcheck passes (1) or not (0); step 4 predicts 0", float(ok2), 0, not ok2)
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
