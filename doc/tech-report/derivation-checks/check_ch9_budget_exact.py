"""Ch. 9 atomic-budget trim (python/atm2d/conservation/atomic.py): when is the budget met exactly?

Derivation (eq-ch09-conservation-exact): proportional removal over the hogs removes exactly the excess X, and
the clip at zero is inactive, iff X <= sum over hogs of A_n. These cases all have hog totals far above 1, where
project_atomic_budget coincides with the corrected rule (budget_theory.trim); the case below 1 is
check_ch9_budget_below1.py.
(x1) X < sum_H A: total after equals the budget; code and corrected rule agree.
(x2) X = sum_H A: every hog reaches zero and the total equals the budget.
(x3) X > sum_H A: every hog is zero, the non-hogs are unchanged, and the total stays above the budget.
(x4) one non-fixed species holds the element (N_e = 1): no hog, nothing trimmed although over budget.
(x5) two elements processed in turn: every budget is met, the result depends on the element order, and the first
     element processed ends strictly below its budget.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera, torch  # noqa: E402,F401
from kintera.atm2d.conservation import project_atomic_budget  # noqa: E402
from budget_theory import trim  # noqa: E402

print(version_line())
torch.manual_seed(9)
fails = 0


def report(name, val, tol, ok=None):
    global fails
    ok = (val <= tol) if ok is None else ok
    fails += not ok
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {'PASS' if ok else 'FAIL'}")


def total(c, counts):
    return (c * counts).sum(-1, keepdim=True)


# species [A (C1), B (C2), D (C1), N2 fixed]; hogs: A (largest share)
cnt = {"C": torch.tensor([1.0, 2.0, 1.0, 0.0])}
fixed = torch.tensor([False, False, False, True])
conc = torch.stack([6e10 * (1 + 0.2 * torch.rand(1, 4)), 1e9 * (1 + torch.rand(1, 4)), 2e9 * (1 + torch.rand(1, 4)),
                    torch.full((1, 4), 1e12)], -1)
A = conc * cnt["C"] * (~fixed)
hog = A > A.sum(-1, keepdim=True) / 3
sumH = torch.where(hog, A, torch.zeros_like(A)).sum(-1, keepdim=True)
cur = total(conc, cnt["C"])
print(f"   4 cells: hog total sum_H A / cell total = {(sumH / cur).min().item():.4f}..{(sumH / cur).max().item():.4f};"
      f" sum_H A >= {sumH.min().item():.3e}")

bud = cur - 0.5 * sumH  # X = sum_H A / 2
out = project_atomic_budget(conc, atom_counts=cnt, fixed_mask=fixed, budget={"C": bud})
th = trim(conc, cnt, fixed, {"C": bud})
report("(x1) X = sum_H A / 2: max |total_after / budget - 1|", (total(out, cnt["C"]) / bud - 1).abs().max().item(), 1e-13)
report("(x1) code vs corrected rule, max rel", ((out - th).abs().max() / conc.abs().max()).item(), 1e-15)

bud = cur - sumH  # X = sum_H A exactly
out = project_atomic_budget(conc, atom_counts=cnt, fixed_mask=fixed, budget={"C": bud})
e = (total(out, cnt["C"]) / bud - 1).abs().max().item()
hz = torch.where(hog, out, torch.zeros_like(out)).abs().max().item() / conc.max().item()
report("(x2) X = sum_H A: |total_after / budget - 1| + max hog left / max c", e + hz, 1e-13)

bud = 0.5 * (cur - sumH)  # X > sum_H A: the non-hogs alone exceed the budget
out = project_atomic_budget(conc, atom_counts=cnt, fixed_mask=fixed, budget={"C": bud})
hz = torch.where(hog, out, torch.zeros_like(out)).abs().max().item()
nonhog_change = torch.where(~hog, out - conc, torch.zeros_like(out)).abs().max().item()
over = (total(out, cnt["C"]) / bud).min().item()
print(f"   (x3) total_after / budget = {over:.6f} (> 1: budget not met), hogs left {hz:.1e}, non-hog change {nonhog_change:.1e}")
report("(x3) X > sum_H A: hogs zero and non-hogs unchanged (max abs)", hz + nonhog_change, 0.0)
report("(x3) X > sum_H A: total_after stays above the budget (min ratio - 1), must be > 0", over - 1, 0.0, over > 1)

c1 = torch.tensor([[[5.0e10, 1.0e12]]])
cnt1 = {"C": torch.tensor([1.0, 0.0])}
out = project_atomic_budget(c1, atom_counts=cnt1, fixed_mask=torch.tensor([False, True]),
                            budget={"C": torch.tensor([[[1.0e10]]])})
report("(x4) N_e = 1, five times over budget: species changed (max abs change)", (out - c1).abs().max().item(), 0.0)

# (x5) species [CO, CO2, C2, O2, N2 fixed]; elements C and O, both over budget
cnt2 = {"C": torch.tensor([1.0, 1.0, 2.0, 0.0, 0.0]), "O": torch.tensor([1.0, 2.0, 0.0, 2.0, 0.0])}
fx = torch.tensor([False, False, False, False, True])
c5 = torch.tensor([[[4e10, 3e10, 5e9, 1e10, 1e12]]])
budget = {e: 0.7 * total(c5, v) for e, v in cnt2.items()}
co = project_atomic_budget(c5, atom_counts=cnt2, fixed_mask=fx, budget=budget)
oc = project_atomic_budget(c5, atom_counts={"O": cnt2["O"], "C": cnt2["C"]}, fixed_mask=fx, budget=budget)
ratios = {k: {e: (total(r, v) / budget[e]).item() for e, v in cnt2.items()} for k, r in (("C,O", co), ("O,C", oc))}
for k, r in ratios.items():
    print(f"   (x5) order {k}: total/budget  C {r['C']:.6f}  O {r['O']:.6f}")
viol = sum(v > 1 + 1e-13 for r in ratios.values() for v in r.values())
report("(x5) every budget met in both orders (violations above 1 + 1e-13)", float(viol), 0.0)
diff = ((co - oc).abs().max() / c5.max()).item()
report("(x5) the result depends on the element order: max |c(C,O) - c(O,C)| / max c, must EXCEED tol", diff, 1e-6,
       diff > 1e-6)
first_below = 1 - ratios["C,O"]["C"]
report("(x5) order C,O: the first element (C) ends strictly below its budget, 1 - total/budget, must EXCEED tol",
       first_below, 1e-6, first_below > 1e-6)
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
