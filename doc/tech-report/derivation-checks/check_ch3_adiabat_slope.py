"""Ch.3 moist adiabat (C3-h): the entropy slope along the saturated path and the order of the rain-out step.

(h1) step 2: for a closed parcel (fixed element amounts, here per mole of the inert dry gas) at fixed p, an
     equilibrium change has dH = T dS, which needs dh_n = T ds_n for every species. Central differences of the
     equilibrium H and S (ThermoX.forward, then TV->H, TPV->S) at a saturated state at 280 K, 10 bar. With the
     cards of tests/jupiter.yaml the solved condensate entropies do not satisfy T ds_c/dT = c_p,c (C3-g), so the
     identity fails: EXPECTED-FAIL, row K8 of UCzhangxi/kintera#54. With the corrected cards: PASS.
(h2) per mole of mixture, dh/dT = c_p,eff, the quantity effective_cp returns (tests/jupiter.yaml).
(h4) what effective_cp is when the number of moles changes: where NH4SH forms (NH3 = H2S = 5e-3 in dry gas,
     170-240 K, 1e5 Pa) it equals (1/n) dH/dT for the closed parcel (H and n per mole of dry gas), not d(H/n)/dT.
(h3) the rain-out branch (rainout=True) evaluates the removed condensate's entropy at the end of each step, a
     rectangle rule, so it is first order in d ln p: total d ln p = -0.2 in N = 4, 8, 16, 32 steps against
     N = 512; the observed order is log2 of successive error ratios (tolerance 0.15 on the order).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import thermo_x, jupiter_x, species, version_line, DECK, torch  # noqa: E402
import ch3_card  # noqa: E402

RES = []


def report(name, val, tol, ok, expected=None):
    if not math.isfinite(val):
        ok = False
    tag = "PASS" if ok else ("EXPECTED-FAIL" if expected else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.2g}  {tag}" + (f" ({expected})" if expected and not ok else ""))


PROBE = r"""
from kintera import ThermoOptions, ThermoX
torch.set_default_dtype(torch.float64)
op = ThermoOptions.from_yaml(sys.argv[1]); op.ftol(1e-14); op.max_iter(100)
th = ThermoX(op); th.to(torch.float64)
x0 = torch.tensor([json.loads(sys.argv[2])])
p = torch.tensor([1e6])
def state(T0):
    T = torch.tensor([T0]); x = x0.clone(); th.forward(T, p, x)
    c = th.compute("TPX->V", [T, p, x]); nd = c[..., 0]; n = c.sum(-1)
    H = th.compute("TV->H", [T, c]); S = th.compute("TPV->S", [T, p, c])
    return (H / nd).item(), (S / nd).item(), (H / n).item()
dT = 1e-2
Hp, Sp, hp = state(280.0 + dT); Hm, Sm, hm = state(280.0 - dT)
print(json.dumps({"dH": (Hp - Hm) / (2 * dT), "TdS": 280.0 * (Sp - Sm) / (2 * dT), "dh": (hp - hm) / (2 * dT)}))
"""


def check_slope():
    op, th = thermo_x(ftol=1e-14, max_iter=100)
    sp, x0 = jupiter_x(op)
    T, p = torch.tensor([280.0]), torch.tensor([1e6])
    x = x0.clone()
    gain = th.forward(T, p, x)
    cpe = th.effective_cp(T, p, x, gain).item()
    with open(DECK) as f:
        deck = f.read()
    for label, text, tag in (("tests/jupiter.yaml", deck, "K8"), ("corrected cards", ch3_card.fixed_deck(deck), None)):
        got = ch3_card.run(text, PROBE, json.dumps(x0[0].tolist()))
        e = abs(got["TdS"] / got["dH"] - 1)
        print(f"   {label}, 280 K, 1e6 Pa, per mole of dry gas: dH/dT = {got['dH']:.10f}, T dS/dT = {got['TdS']:.10f}"
              f" J/(mol K); per mole of mixture dh/dT = {got['dh']:.10f}")
        report(f"(h1) closed parcel at fixed p, {label}: T dS/dT vs dH/dT (rel)", e, 1e-5, e < 1e-5, tag)
        if tag:
            e = abs(got["dh"] / cpe - 1)
            print(f"   effective_cp = {cpe:.10f} J/(mol K)")
            report("(h2) per mole: dh/dT along the equilibrium path vs effective_cp (rel)", e, 1e-5, e < 1e-5)


def rainout(N):
    op, th = thermo_x(ftol=1e-12, max_iter=100)
    sp, x = jupiter_x(op, xh2o=2.5e-2)
    T, p = torch.tensor([300.0]), torch.tensor([1e6])
    th.forward(T, p, x)
    for _ in range(N):
        th.extrapolate_dlnp(T, p, x, -0.2 / N, 0.0, True)
    return T.item()


def check_order():
    ref = rainout(512)
    Ns = [4, 8, 16, 32]
    errs = [abs(rainout(N) - ref) for N in Ns]
    orders = [math.log2(errs[i] / errs[i + 1]) for i in range(len(errs) - 1)]
    print("   rain-out, d ln p = -0.2 from 300 K, 1e6 Pa: |T_N - T_512| = " + ", ".join(f"{e:.4e}" for e in errs)
          + " K for N = 4, 8, 16, 32; observed orders " + ", ".join(f"{q:.3f}" for q in orders))
    worst = max(abs(q - 1) for q in orders)
    report("(h3) rain-out step is first order in d ln p: max |observed order - 1|", worst, 0.15, worst < 0.15)


def check_moles():
    op, th = thermo_x(ftol=1e-14, max_iter=100)
    sp = species(op)
    x0 = torch.zeros(1, len(sp))
    x0[0, sp.index("NH3")] = 5e-3
    x0[0, sp.index("H2S")] = 5e-3
    x0[0, 0] = 1.0 - 1e-2
    p = torch.tensor([1e5])

    def state(T0):
        T = torch.tensor([T0])
        x = x0.clone()
        gain = th.forward(T, p, x)
        c = th.compute("TPX->V", [T, p, x])
        H = th.compute("TV->H", [T, c])
        return (H / c[..., 0]).item(), (c.sum(-1) / c[..., 0]).item(), (H / c.sum(-1)).item(), \
            th.effective_cp(T, p, x, gain).item(), x[0, sp.index("NH4SH(s)")].item()

    worst, other = 0.0, 0.0
    dT = 1e-2
    for T0 in (170.0, 190.0, 210.0, 230.0, 240.0):
        Hp, np_, hp, _, _ = state(T0 + dT)
        Hm, nm, hm, _, _ = state(T0 - dT)
        _, n0, _, cpe, xs = state(T0)
        one_n = (Hp - Hm) / (2 * dT) / n0
        dhbar = (hp - hm) / (2 * dT)
        worst = max(worst, abs(cpe / one_n - 1))
        other = max(other, abs(cpe / dhbar - 1))
        print(f"   T={T0:.0f} K: x_NH4SH = {xs:.3e}, effective_cp = {cpe:.8f}, (1/n) dH/dT = {one_n:.8f}, "
              f"d(H/n)/dT = {dhbar:.8f} J/(mol K)")
    print(f"   |effective_cp / d(H/n)/dT - 1| up to {other:.3e} (n changes)")
    report("(h4) effective_cp vs (1/n) dH/dT where NH4SH forms, worst rel", worst, 1e-6, worst < 1e-6)


if __name__ == "__main__":
    print(version_line())
    check_slope()
    check_moles()
    check_order()
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "EXPECTED-FAIL")))
