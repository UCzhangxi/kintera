"""Ch.3 condensate entropy from zero reaction Gibbs energy (C3-e), its copies (D64) and the NASA-9 gas
entropy (K6).

Partial molar quantities at fixed (T, p): h_n = dH/dc_n (H is linear in c) and s_n = dS/dc_n by a central
difference of TPV->S; for the gases the mixing terms drop out of the sum (sum_k c_k d ln x_k / dc_n = 0), so s_n
is the species entropy including its own mixing term.
(e1) every nucleation reaction of tests/jupiter.yaml at a saturated state: sum_n nu_n (h_n - T s_n) / (R T) = 0.
(e2) D64: a condensate copy made by coagulation (H2O(l,p), NH3(s,p)), in no nucleation reaction, has the entropy
     of its source. At 0d9f67f the pseudo-inverse gives it 0. EXPECTED-FAIL, row D64 of UCzhangxi/kintera#54.
(e3) K6: with use-nasa9-cp the gas entropy satisfies T (ds/dT)_p = cp, the cp that TV->cp returns. At 0d9f67f the
     entropy keeps the constant cp. EXPECTED-FAIL, row K6. Flag off: PASS.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import thermo_x, species, version_line, kintera, torch  # noqa: E402
import ch3_card  # noqa: E402

R = 8.31446  # kintera Rgas (constants.h)
RES = []


def report(name, val, tol, ok, expected=None):
    if not math.isfinite(val):
        ok = False
    tag = "PASS" if ok else ("EXPECTED-FAIL" if expected else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}" + (f" ({expected})" if expected and not ok else ""))


def lsvp(t, b, g, b_s, g_s, T3, P3):
    bb, gg = (b, g) if t > T3 else (b_s, g_s)
    x = t / T3
    return (1 - 1 / x) * bb - gg * math.log(x) + math.log(P3)


def h2o_ideal(t):  # src/vapors/vapor_functions.h
    return lsvp(t, 24.845, 4.986009, 22.98, 0.52, 273.16, 611.7)


def nh3_ideal(t):
    return lsvp(t, 20.08, 5.62, 20.64, 1.43, 195.4, 6060.0)


def nh3_h2s_lewis(t):
    return (14.82 - 4705.0 / t) * math.log(10.0) + 2.0 * math.log(101325.0)


def partial(th, T, p, c, n):
    """(h_n, s_n) at fixed T, p: exact H difference over one unit, central difference of S."""
    e = torch.zeros_like(c)
    e[0, n] = 1.0
    h = (th.compute("TV->H", [T, c + e]) - th.compute("TV->H", [T, c])).item()
    d = 1e-6 * max(c[0, n].item(), 1.0)
    s = ((th.compute("TPV->S", [T, p, c + d * e]) - th.compute("TPV->S", [T, p, c - d * e])) / (2 * d)).item()
    return h, s


def check_saturation(op, th, sp):
    worst = 0.0
    cases = [("H2O", None, "H2O(l)", h2o_ideal, (250.0, 280.0, 300.0)),
             ("NH3", None, "NH3(s)", nh3_ideal, (150.0, 180.0, 220.0)),
             ("NH3", "H2S", "NH4SH(s)", nh3_h2s_lewis, (200.0, 240.0))]
    for g1, g2, cond, lnk, Ts in cases:
        for T0 in Ts:
            T = torch.tensor([T0])
            c = torch.zeros(1, len(sp))
            if g2 is None:
                ps = math.exp(lnk(T0))
                c[0, sp.index(g1)] = ps / (R * T0)
            else:  # equal partial pressures whose product is K
                ps = 2 * math.exp(0.5 * lnk(T0))
                c[0, sp.index(g1)] = c[0, sp.index(g2)] = 0.5 * ps / (R * T0)
            c[0, sp.index(cond)] = 1.0
            p = torch.tensor([ps])
            dg = 0.0
            for name, nu in ((g1, -1.0), (g2, -1.0), (cond, 1.0)):
                if name is None:
                    continue
                h, s = partial(th, T, p, c, sp.index(name))
                dg += nu * (h - T0 * s)
            e = abs(dg) / (R * T0)
            worst = max(worst, e)
            print(f"   {cond:9s} T={T0:6.1f} K, p={ps:.6e} Pa: sum nu (h - T s)/(R T) = {dg / (R * T0):+.3e}")
    report("(e1) nucleation reactions at saturation: |sum_n nu_n (h_n - T s_n)|/(R T), worst", worst, 1e-6,
           worst < 1e-6)


def check_copies(op, th, sp):
    worst, lines = 0.0, []
    for vap, src, cp_, T0, P0 in (("H2O", "H2O(l)", "H2O(l,p)", 280.0, 5.0e5), ("NH3", "NH3(s)", "NH3(s,p)", 140.0, 0.5e5)):
        T, p = torch.tensor([T0]), torch.tensor([P0])
        x = torch.zeros(1, len(sp))
        x[0, sp.index(vap)] = 1e-3
        x[0, sp.index(src)] = 1e-3
        x[0, sp.index(cp_)] = 1e-3
        x[0, 0] = 1.0 - x.sum()
        c = th.compute("TPX->V", [T, p, x])
        _, s_src = partial(th, T, p, c, sp.index(src))
        _, s_cp = partial(th, T, p, c, sp.index(cp_))
        e = abs(s_cp / s_src - 1)
        worst = max(worst, e)
        print(f"   {cp_}: s/R = {s_cp / R:.6f}, source {src}: s/R = {s_src / R:.6f} (T={T0} K, p={P0:.1e} Pa)")
    report("(e2) coagulation copy entropy equals its source's, worst rel", worst, 1e-9, worst < 1e-9, "D64")


CARD = """reference-state: {Tref: 300.0, Pref: 1.0e5%s}
species:
- {name: H2, composition: {H: 2}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 3.0, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: H2O <=> H2O(l), type: nucleation, rate-constant: {formula: h2o_ideal}}
"""
PROBE = r"""
from kintera import ThermoX, ThermoOptions
torch.set_default_dtype(torch.float64)
T = torch.tensor([250.0, 300.0, 400.0, 600.0, 900.0]); eps = 1e-5
p = 1e5 * torch.ones_like(T)
tx = ThermoX(ThermoOptions.from_yaml(sys.argv[1]))
c = torch.zeros(T.shape + (3,)); c[..., 1] = 1.0
S = lambda t: tx.compute("TPV->S", [t, p, c])
Tp, Tm = T * (1 + eps), T * (1 - eps)
print(json.dumps({"cp": tx.compute("TV->cp", [T, c]).tolist(), "Tdsdt": (T * (S(Tp) - S(Tm)) / (Tp - Tm)).tolist()}))
"""


def check_k6():
    for flag, tag in (("", None), (", use-nasa9-cp: true", "K6")):
        got = ch3_card.run(CARD % flag, PROBE)
        e = max(abs(a / b - 1) for a, b in zip(got["Tdsdt"], got["cp"]))
        print(f"   H2O gas{flag or ' (constant cp)'}: cp = {[round(v, 6) for v in got['cp']]}, "
              f"T ds/dT = {[round(v, 6) for v in got['Tdsdt']]} J/(mol K) at 250-900 K")
        name = "(e3) T (ds/dT)_p = cp for H2O gas, " + ("use-nasa9-cp on" if tag else "flag off") + ", worst rel"
        report(name, e, 1e-6, e < 1e-6, tag)


if __name__ == "__main__":
    print(version_line())
    op, th = thermo_x()
    sp = species(op)
    check_saturation(op, th, sp)
    check_copies(op, th, sp)
    check_k6()
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "EXPECTED-FAIL")))
