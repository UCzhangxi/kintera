"""Ch. 2 LogSVPFunc backward pass (src/thermo/log_svp.cpp), reached through the evaporation module.

LogSVPFunc::apply is the autograd path of ln K(T); its one caller is EvaporationImpl::forward
(src/kinetics/evaporation.cpp), which Python binds as kintera.Evaporation. With diff_T = diff_P = 0 its rate
constant for CH4(s,p) => CH4 is  w(T) = kappa (K(T) - c_v),  K = exp(ln p(T)) / (R T),  kappa independent of T,
so every T-derivative of w is a closed form in ln p, (ln p)' and (ln p)'' of the ideal formula.

(a) first derivative: autograd dw/dT against kappa K ((ln p)' - 1/T), and torch.autograd.gradcheck.
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
report("(a2) torch.autograd.gradcheck at 78 K (eps 1e-6, rtol 1e-7) fails (1) or not (0)", float(not ok), 0, ok)
# (a3) two reactions, temperature expanded to one column per reaction (the layout Kinetics.forward uses):
# the gradient of reaction j lands on column j only.
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
report("(a3) per-column gradient: rel error on own column + |value on the other column|", e3 + off, 1e-12,
       e3 + off <= 1e-12)
report("(b1) autograd d2w/dT2 vs prediction without (ln p)'', worst rel", worst2, 1e-12, worst2 <= 1e-12)
report("(b2) |autograd d2w/dT2 / true - 1|, must EXCEED tol (the dropped (ln p)'' term)", worstp, 1e-2,
       worstp >= 1e-2)
ok2 = torch.autograd.gradgradcheck(lambda x: w(x), (Tg,), eps=1e-6, atol=1e-10, rtol=1e-7,
                                   raise_exception=False)
report("(b3) torch.autograd.gradgradcheck passes (1) or not (0); step 3 predicts 0", float(ok2), 0, not ok2)
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
