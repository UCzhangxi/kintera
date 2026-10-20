"""Ch.3 PXS->T: the slope of entropy per volume at fixed p and x (C3-f) and the corrected Newton step (D8).

(f1) dS/dT at fixed (p, x), S per volume, equals (C_p - S)/T: central difference of TPV->S with c = TPX->V(T)
     against TV->cp and TPV->S, a dry state of tests/jupiter.yaml. (With a condensate present the identity also
     needs ds_c/dT = c_p,c/T, which a card inconsistent with its curve breaks: check_ch3_reference.py (g3).)
(f2) the update of 0d9f67f, T <- T (1 + (S_g - S)/C_p), is a fixed-point map whose derivative at the root is
     S/C_p (= s/c_p, which depends on the entropy offset): central difference of the map against S/C_p.
(f3) the correct Newton step T <- T + T (S_g - S)/(C_p - S), written here with kintera's S and C_p, recovers T from
     S(600 K) starting at Tref = 300 K.
(f4) kintera's PXS->T on the same input: EXPECTED-FAIL at 0d9f67f, row D8 of UCzhangxi/kintera#54.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import thermo_x, species, version_line, torch  # noqa: E402

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
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "EXPECTED-FAIL")))
