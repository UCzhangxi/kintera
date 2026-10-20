"""Ch.3 PXS->T: the slope of entropy per volume at fixed p and x (C3-f) and the corrected Newton step (D8).

(f1) dS/dT at fixed (p, x), S per volume, equals (C_p - S)/T: central difference of TPV->S with c = TPX->V(T)
     against TV->cp and TPV->S, a dry state of tests/jupiter.yaml. (With a condensate present the identity also
     needs ds_c/dT = c_p,c/T, which a card inconsistent with its curve breaks: check_ch3_reference.py (g3).)
(f2) the update of 0d9f67f, T <- T (1 + (S_g - S)/C_p), is a fixed-point map whose derivative at the root is
     S/C_p (= s/c_p, which depends on the entropy offset): central difference of the map against S/C_p.
(f3) the correct Newton step T <- T + T (S_g - S)/(C_p - S), written here with kintera's S and C_p, recovers T from
     S(600 K) starting at Tref = 300 K.
(f4) kintera's PXS->T on the same input: EXPECTED-FAIL at 0d9f67f, row D8 of UCzhangxi/kintera#54.
Saturated parcel (tests/jupiter.yaml with the step-3 cards of C3-g, H2O only, x_H2O = 0.02, T* = 299 K, p = 1e6 Pa),
S taken along the equilibrium path (forward at every temperature):
(f5) T dS/dT = (C_eff - S) - S T d ln n_g/dT, with C_eff = (sum c) effective_cp and n_g the gas moles per mole of
     dry gas: against a central difference of S.
(f6) the frozen-slope step ln T <- ln T + (S_g - S)/(C_p - S) has the root factor phi' = 1 - T (dS/dT)/(C_p - S):
     prediction against the error ratios of the iteration started at T* + 1e-3 K.
(f7) the pin's step T <- T (1 + (S_g - S)/C_p) has the root factor 1 - T (dS/dT)/C_p, not S/C_p (which holds at
     frozen composition only): prediction against the error ratios.
(f8) kintera's PXS->T from Tref with max_iter 1..8: it alternates and does not reach T* (|phi'| > 1). EXPECTED-FAIL
     at 0d9f67f, row D8.
(f9) entropy constants: dry gas from 300 K to S(600 K), with s0_R of the dry gas 0 and 10; the first Newton step
     differs, the root does not.
(f10) the sign of phi' depends on the constants: the (f6) state with s0_R of the dry gas 10 gives C_p - S < 0 and
     T dS/dT < 0, phi' > 0, and monotone iterates: prediction against the error ratios, and the sign.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import thermo_x, species, version_line, DECK, torch  # noqa: E402
import json  # noqa: E402
import ch3_card  # noqa: E402

RES = []


def report(name, val, tol, ok, expected=None):
    if not math.isfinite(val):
        ok = False
    tag = "PASS" if ok else ("EXPECTED-FAIL" if expected else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}" + (f" ({expected})" if expected and not ok else ""))


def S_of(th, T, p, x):
    c = th.compute("TPX->V", [T, p, x])
    return th.compute("TPV->S", [T, p, c]), th.compute("TV->cp", [T, c])


SAT_PROBE = r"""
from kintera import ThermoOptions, ThermoX
torch.set_default_dtype(torch.float64)
card = sys.argv[1]
with_code = len(sys.argv) < 3
op = ThermoOptions.from_yaml(card); op.max_iter(100); op.ftol(1e-14)
th = ThermoX(op); th.to(torch.float64)
names = kintera.species_names()
sp = [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]
x0 = torch.zeros(1, len(sp)); x0[0, sp.index("H2O")] = 0.02; x0[0, 0] = 0.98
p = torch.tensor([1e6])
def eq(T0):
    T = torch.tensor([T0]); x = x0.clone(); gain = th.forward(T, p, x)
    c = th.compute("TPX->V", [T, p, x]); ng = c[..., :len(op.vapor_ids())].sum(-1)
    S = th.compute("TPV->S", [T, p, c]).item(); Cp = th.compute("TV->cp", [T, c]).item()
    ceff = (c.sum(-1) * th.effective_cp(T, p, x, gain)).item()
    return S, Cp, ceff, (ng / c[..., 0]).item(), x[0].tolist()
Ts = 299.0
S, Cp, Ceff, ng, xs = eq(Ts)
h = 1e-3
Sp, _, _, ngp, _ = eq(Ts + h); Sm, _, _, ngm, _ = eq(Ts - h)
TdSdT = Ts * (Sp - Sm) / (2 * h)
dlnng = (math.log(ngp) - math.log(ngm)) / (2 * h)
def iterate(step, n):
    T = Ts + 1e-3; err = []
    for _ in range(n):
        Sx, Cpx, _, _, _ = eq(T); T = step(T, Sx, Cpx); err.append(T - Ts)
    return err
frozen = iterate(lambda T, Sx, Cpx: math.exp(math.log(T) + (S - Sx) / (Cpx - Sx)), 3)
pin = iterate(lambda T, Sx, Cpx: T * (1 + (S - Sx) / Cpx), 3)
codes = []
for k in range(1, 9) if with_code else ():
    o = ThermoOptions.from_yaml(card); o.max_iter(k); o.ftol(1e-14)
    t = ThermoX(o); t.to(torch.float64)
    codes.append(t.compute("PXS->T", [p, x0.clone(), torch.tensor([S])]).item() - Ts)
print(json.dumps({"S": S, "Cp": Cp, "Ceff": Ceff, "TdSdT": TdSdT, "dlnng": dlnng, "xg": sum(xs[:len(op.vapor_ids())]),
                  "frozen": frozen, "pin": pin, "code": codes}))
"""

CONST_PROBE = r"""
from kintera import ThermoOptions, ThermoX
torch.set_default_dtype(torch.float64)
op = ThermoOptions.from_yaml(sys.argv[1]); th = ThermoX(op); th.to(torch.float64)
names = kintera.species_names()
sp = [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]
x = torch.zeros(1, len(sp)); x[0, 0] = 1.0; p = torch.tensor([1e5])
def SC(T0):
    T = torch.tensor([T0]); c = th.compute("TPX->V", [T, p, x])
    return th.compute("TPV->S", [T, p, c]).item(), th.compute("TV->cp", [T, c]).item()
Sg = SC(600.0)[0]; T = 300.0; steps = []
for _ in range(10):
    S, Cp = SC(T); T = T + T * (Sg - S) / (Cp - S); steps.append(T)
S300, Cp300 = SC(300.0)
print(json.dumps({"steps": steps, "S300": S300, "CpmS300": Cp300 - S300}))
"""


DRY = "  - name: dry\n    composition: {H: 1.5, He: 0.15}\n    cv_R: 2.5"


def check_saturated():
    with open(DECK) as f:
        deck = f.read()
    got = ch3_card.run(ch3_card.fixed_deck(deck), SAT_PROBE)
    S, Cp, Ceff, TdS = got["S"], got["Cp"], got["Ceff"], got["TdSdT"]
    form = (Ceff - S) - S * 299.0 * got["dlnng"]
    print(f"   saturated state 299 K, 1e6 Pa, x_H2O 0.02: x_g = {got['xg']:.6f}, S = {S:.2f}, C_p = {Cp:.2f}, "
          f"C_eff = {Ceff:.2f} J/(K m^3)")
    print(f"   T dS/dT: central difference {TdS:.6f}, (C_eff - S) - S T dln n_g/dT = {form:.6f}, C_eff - S = {Ceff - S:.2f}")
    e = abs(form / TdS - 1)
    report("(f5) saturated T dS/dT vs (C_eff - S) - S T d ln n_g/dT (rel)", e, 1e-6, e < 1e-6)
    phi = 1 - TdS / (Cp - S)
    r = [got["frozen"][i + 1] / got["frozen"][i] for i in range(2)]
    print(f"   frozen ln T step: predicted phi' = {phi:.6f}, error ratios {r[0]:.6f}, {r[1]:.6f}")
    e = max(abs(q - phi) for q in r)
    report("(f6) frozen-slope step: root factor 1 - T (dS/dT)/(C_p - S) vs iteration (abs)", e, 1e-3, e < 1e-3)
    phip = 1 - TdS / Cp
    r = [got["pin"][i + 1] / got["pin"][i] for i in range(2)]
    print(f"   pin step: predicted 1 - T (dS/dT)/C_p = {phip:.6f} (S/C_p = {S / Cp:.6f}), error ratios {r[0]:.6f}, "
          f"{r[1]:.6f}")
    e = max(abs(q - phip) for q in r)
    report("(f7) pin step: root factor 1 - T (dS/dT)/C_p vs iteration (abs)", e, 1e-3, e < 1e-3)
    print("   kintera PXS->T from Tref, max_iter 1..8: T - T* = " + ", ".join(f"{v:+.1f}" for v in got["code"]) + " K")
    e = abs(got["code"][-1])
    report("(f8) kintera PXS->T in the saturated parcel after 8 passes, |T - T*| (K)", e, 1e-6, e < 1e-6, "D8")
    d1 = ch3_card.run(deck, CONST_PROBE)
    assert DRY in deck
    d2 = ch3_card.run(deck.replace(DRY, DRY + "\n    s0_R: 10.", 1), CONST_PROBE)
    print(f"   dry gas, s0_R 0: first step {d1['steps'][0]:.3f} K, S(300) = {d1['S300']:.1f}, C_p - S = "
          f"{d1['CpmS300']:.1f}; s0_R 10: first step {d2['steps'][0]:.3f} K, S(300) = {d2['S300']:.1f}, C_p - S = "
          f"{d2['CpmS300']:.1f} J/(K m^3)")
    e = max(abs(d1["steps"][-1] - 600.0), abs(d2["steps"][-1] - 600.0))
    report("(f9) the root does not depend on s0_R: both runs end at 600 K, max |T - 600| (K)", e, 1e-9, e < 1e-9)
    e = abs(d2["steps"][0] - d1["steps"][0])
    report("(f9) the iterates do: first steps differ (K), must EXCEED tol", e, 1.0, e > 1.0)
    g = ch3_card.run(ch3_card.fixed_deck(deck.replace(DRY, DRY + "\n    s0_R: 10.", 1)), SAT_PROBE, "nocode")
    S, Cp, TdS = g["S"], g["Cp"], g["TdSdT"]
    phi = 1 - TdS / (Cp - S)
    r = [g["frozen"][i + 1] / g["frozen"][i] for i in range(2)]
    print(f"   same state, dry s0_R 10: C_p - S = {Cp - S:.0f}, T dS/dT = {TdS:.0f} J/(K m^3), ratio "
          f"{TdS / (Cp - S):.6f}; phi' = {phi:.6f}, error ratios {r[0]:.6f}, {r[1]:.6f}")
    e = max(abs(q - phi) for q in r)
    report("(f10) s0_R 10: root factor 1 - T (dS/dT)/(C_p - S) vs iteration (abs)", e, 1e-3, e < 1e-3)
    report("(f10) s0_R 10: phi' > 0 with C_p - S < 0, monotone iterates, must EXCEED tol", phi, 0.0,
           phi > 0 and Cp - S < 0 and min(r) > 0)


if __name__ == "__main__":
    print(version_line())
    op, th = thermo_x()
    sp = species(op)
    dry = torch.zeros(1, len(sp))
    dry[0, 0] = 1.0
    p = torch.tensor([1e5])
    worst = 0.0
    for x in (dry,):
        for T0 in (250.0, 400.0, 600.0):
            T = torch.tensor([T0])
            dT = 1e-3
            fd = ((S_of(th, T + dT, p, x)[0] - S_of(th, T - dT, p, x)[0]) / (2 * dT)).item()
            S, cp = S_of(th, T, p, x)
            ref = ((cp - S) / T).item()
            worst = max(worst, abs(fd / ref - 1))
    report("(f1) dS/dT|_(p,x) vs (C_p - S)/T, dry state, 250-600 K (rel)", worst, 1e-7, worst < 1e-7)

    Tg = torch.tensor([600.0])
    Sg, _ = S_of(th, Tg, p, dry)

    def pin_map(T):
        S, cp = S_of(th, T, p, dry)
        return T * (1 + (Sg - S) / cp)

    h = 1e-3
    gp = ((pin_map(Tg + h) - pin_map(Tg - h)) / (2 * h)).item()
    S, cp = S_of(th, Tg, p, dry)
    print(f"   at 600 K: S = {S.item():.6f}, C_p = {cp.item():.6f} J/(K m^3); pin map derivative {gp:.10f},"
          f" S/C_p = {(S / cp).item():.10f}")
    e = abs(gp - (S / cp).item())
    report("(f2) derivative of the pin's fixed-point map at the root vs S/C_p (abs)", e, 1e-7, e < 1e-7)

    T = torch.tensor([op.Tref()])
    hist = []
    for _ in range(op.max_iter()):
        S, cp = S_of(th, T, p, dry)
        T = T + T * (Sg - S) / (cp - S)
        hist.append(T.item())
    print("   correct Newton from Tref: " + ", ".join(f"{t:.9f}" for t in hist[:6]) + " K ...")
    e = abs(hist[-1] - 600.0)
    report(f"(f3) correct Newton step, {op.max_iter()} iterations from Tref, |T - 600| (K)", e, 1e-9, e < 1e-9)
    Tb = th.compute("PXS->T", [p, dry, Sg]).item()
    print(f"   kintera PXS->T: {Tb:.10f} K")
    e = abs(Tb - 600.0)
    report("(f4) kintera PXS->T from the same S, |T - 600| (K)", e, 1e-6, e < 1e-6, "D8")
    check_saturated()
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "EXPECTED-FAIL")))
