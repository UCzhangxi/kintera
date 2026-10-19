"""Ch. 9 atomic-budget trim below a hog total of 1: corrected rule against the pinned code (K9 limit).

The corrected rule (eq-ch09-conservation-trim, budget_theory.trim) divides by sum_H A; project_atomic_budget at the
pin divides by max(1, sum_H A) (eq-ch09-conservation-code). Defect row K9 of UCzhangxi/kintera#54 documents this;
the code lines below are EXPECTED-FAIL until that fix lands, and are expected to PASS after it.
(y1) the K9 case of check_ch9_atm2d.py line d': species [A (C1) 0.5, B (C2) 0.005, N2 fixed], budget 0.3.
     Corrected rule: total after = 0.3. Code: 0.51 - 0.21 * 0.5 = 0.405, the limit formula.
(y2) units: the corrected rule commutes with a change of concentration unit (trim(s c) = s trim(c)); the floor at 1
     does not, so the code's result depends on the unit.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera, torch  # noqa: E402,F401
from kintera.atm2d.conservation import project_atomic_budget  # noqa: E402
from budget_theory import trim  # noqa: E402

print(version_line())
fails = 0
xfails = 0


def report(name, val, tol, expected_fail=False, ok=None):
    global fails, xfails
    ok = (val <= tol) if ok is None else ok
    xfails += (not ok) and expected_fail
    tag = "PASS" if ok else ("EXPECTED-FAIL" if expected_fail else "FAIL")
    fails += (not ok) and (not expected_fail)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}")


cnt = {"C": torch.tensor([1.0, 2.0, 0.0])}
fixed = torch.tensor([False, False, True])
small = torch.tensor([[[0.5, 0.005, 1.0]]])
B = torch.tensor([[[0.3]]])
th = trim(small, cnt, fixed, {"C": B})
co = project_atomic_budget(small, atom_counts=cnt, fixed_mask=fixed, budget={"C": B})
tt, tc = (th * cnt["C"]).sum().item(), (co * cnt["C"]).sum().item()
print(f"   (y1) hog total 0.5, excess 0.21: corrected rule total_after = {tt:.6f}, code total_after = {tc:.6f}, "
      f"limit formula 0.51 - 0.21 * 0.5 = {0.51 - 0.21 * 0.5:.6f}")
report("(y1) corrected rule meets the budget: |total_after / 0.3 - 1|", abs(tt / 0.3 - 1), 1e-13)
report("(y1) corrected rule: no hog negative (min c)", max(0.0, -th.min().item()), 0.0)
report("(y1) code equals the limit formula eq-ch09-conservation-code: |total_after - 0.405| / 0.405",
       abs(tc - 0.405) / 0.405, 1e-13)
report("(y1) code meets the budget: |total_after / 0.3 - 1| (K9, UCzhangxi/kintera#54)", abs(tc / 0.3 - 1), 1e-13,
       expected_fail=True)

worst_t, worst_c = 0.0, 0.0
for s in (1e-3, 1e3, 1e6):
    ts = trim(s * small, cnt, fixed, {"C": s * B})
    cs = project_atomic_budget(s * small, atom_counts=cnt, fixed_mask=fixed, budget={"C": s * B})
    worst_t = max(worst_t, ((ts - s * th).abs().max() / (s * th).abs().max()).item())
    worst_c = max(worst_c, ((cs - s * co).abs().max() / (s * co).abs().max()).item())
    print(f"   (y2) unit scale s = {s:.0e}: total_after / (s budget) corrected {(ts * cnt['C']).sum().item() / (s * 0.3):.6f},"
          f" code {(cs * cnt['C']).sum().item() / (s * 0.3):.6f}")
report("(y2) corrected rule is unit-independent: max rel |trim(s c) - s trim(c)|", worst_t, 1e-13)
report("(y2) code is unit-independent: max rel |code(s c) - s code(c)| (K9, UCzhangxi/kintera#54)", worst_c, 1e-13,
       expected_fail=True)
print((f"ALL PASS, {xfails} EXPECTED-FAIL" if xfails else "ALL PASS") if fails == 0 else f"{fails} FAIL")
