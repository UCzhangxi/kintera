"""Ch.3 equation of state with condensates (TPX->V): gas concentrations from Dalton's law, condensate
concentrations as x_m p / (R T x_g).

(c1) a gas-only state and a cloudy state with x_0 > 0: sum_gas c R T = p and c_m = x_m p / (R T x_g).
(c2) the same cloudy state without species 0 (x_0 = 0, a pure vapour with its condensate): the correct result
     is unchanged in form; at 0d9f67f the cloud concentration is c_0 x_m / x_0, which is not finite when x_0 = 0.
     EXPECTED-FAIL, row D16 of UCzhangxi/kintera#54.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line  # noqa: E402
import ch3_card  # noqa: E402

R = 8.31446  # kintera Rgas (constants.h)
RES = []


def report(name, val, tol, ok, expected=None):
    if not math.isfinite(val):
        ok = False
    tag = "PASS" if ok else ("EXPECTED-FAIL" if expected else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}" + (f" ({expected})" if expected and not ok else ""))


CARD = """reference-state: {Tref: 300., Pref: 1.e5}
species:
- {name: dry, composition: {N: 1.56, O: 0.42}, cv_R: 2.5}
- {name: A, composition: {H: 2, O: 1}, cv_R: 1.5, u0_R: 0.}
- {name: A(l), composition: {H: 2, O: 1}, cv_R: 7.5, u0_R: -6786.66}
reactions:
- {equation: 'A <=> A(l)', type: nucleation, rate-constant: {formula: antoine, A: 1.5, B: 900., C: 0.}}
"""
PROBE = r"""
from kintera import ThermoOptions, ThermoX
th = ThermoX(ThermoOptions.from_yaml(sys.argv[1]))
th.to(torch.float64)
out = []
for xs in json.loads(sys.argv[2]):
    x = torch.tensor([xs], dtype=torch.float64)
    c = th.compute("TPX->V", [torch.tensor([300.0]), torch.tensor([1.0e5]), x])
    out.append(c[0].tolist())
print(json.dumps(out))
"""

if __name__ == "__main__":
    print(version_line())
    T, p = 300.0, 1.0e5
    states = [[1.0, 0.0, 0.0], [0.5, 0.4, 0.1], [0.0, 0.9, 0.1]]
    import json
    got = ch3_card.run(CARD, PROBE, json.dumps(states))
    worst_gas, worst_cloud = 0.0, 0.0
    for xs, c in zip(states[:2], got[:2]):
        xg = xs[0] + xs[1]
        worst_gas = max(worst_gas, abs((c[0] + c[1]) * R * T / p - 1))
        if xs[2] > 0:
            worst_cloud = max(worst_cloud, abs(c[2] / (xs[2] * p / (R * T * xg)) - 1))
        print(f"   x = {xs}: c = {[f'{v:.10e}' for v in c]} mol/m^3")
    report("(c1) sum_gas c R T = p, gas-only and cloudy states with x_0 > 0 (rel)", worst_gas, 1e-13, worst_gas < 1e-13)
    report("(c1) c_m = x_m p / (R T x_g), cloudy state with x_0 = 0.5 (rel)", worst_cloud, 1e-13, worst_cloud < 1e-13)
    xs, c = states[2], got[2]
    print(f"   x = {xs}: c = {c} mol/m^3 (x_0 = 0)")
    ref = xs[2] * p / (R * T * (xs[0] + xs[1]))
    gas = abs((c[0] + c[1]) * R * T / p - 1)
    report("(c2) x_0 = 0: sum_gas c R T = p (rel)", gas, 1e-13, gas < 1e-13)
    e = abs(c[2] / ref - 1) if math.isfinite(c[2]) else float("inf")
    report("(c2) x_0 = 0: c_m = x_m p / (R T x_g) (rel; non-finite at the pin)", e, 1e-13, e < 1e-13, "D16")
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "EXPECTED-FAIL")))
