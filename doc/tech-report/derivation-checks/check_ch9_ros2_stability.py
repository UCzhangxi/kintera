"""Ch. 9 Ros2 stability function (python/atm2d/rosenbrock.py), on dc/dt = lambda c with the exact Jacobian.

One rosenbrock2_step of size dt multiplies c by R(z), z = lambda dt, with
    R(z) = (1 + (1 - 2 gamma) z + (gamma^2 - 2 gamma + 1/2) z^2) / (1 - gamma z)^2 .
(s1) the code's R against the formula, gamma = GAMMA = 1 + 1/sqrt 2, for z from -1e-2 to -1e6 (clip off); the
     tolerance is absolute (16 eps with c0 = 1), because c1 is formed by cancelling O(c0) terms when R is small.
(s2) L-stability: R(-1e12) equals the formula's tail (1 + sqrt 2) / (gamma^2 x) to round-off, so R(-inf) = 0.
(s3) 0 < R(-x) <= 1 on x in [0, 1e8]: decaying modes decay monotonically and keep their sign.
(s4) the other root gamma = 1 - 1/sqrt 2 (module constant patched for this line only): still R(-inf) = 0, but R < 0
     for x > 1 + sqrt 2, as the formula says.
(s5) a gamma off both roots, 1/2: R(-inf) = (gamma^2 - 2 gamma + 1/2) / gamma^2 = -1, no damping of stiff modes.
"""
import math
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera, torch  # noqa: E402,F401
import kintera.atm2d as a2  # noqa: E402
import kintera.atm2d.rosenbrock as ros  # noqa: E402
from kintera.atm2d.sources import LocalSourceLinearization  # noqa: E402

warnings.filterwarnings("ignore", message="Sparse CSR tensor support")
print(version_line())
fails = 0
S2 = math.sqrt(2.0)


def report(name, val, tol, ok=None):
    global fails
    ok = (val <= tol) if ok is None else ok
    fails += not ok
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {'PASS' if ok else 'FAIL'}")


class Linear:
    def __init__(self, lam):
        self.lam = lam

    def linearize(self, st):
        return LocalSourceLinearization(tendency=self.lam * st.concentration.clone(),
                                        jacobian=self.lam * torch.ones(1, 1, 1, 1))


def R_code(z):
    st = a2.AtmState2D(x1f=torch.tensor([0.0, 1.0]), x2f=torch.tensor([0.0, 1.0]),
                       temperature=torch.full((1, 1), 200.0), pressure=torch.ones(1, 1),
                       concentration=torch.ones(1, 1, 1))
    r = a2.rosenbrock2_step(st, 1.0, kzz=torch.zeros(1, 1), source_terms=[Linear(z)], clip_negative=False)
    return r.concentration.item()


def R_formula(z, g):
    return (1 + (1 - 2 * g) * z + (g * g - 2 * g + 0.5) * z * z) / (1 - g * z) ** 2


g = ros.GAMMA
print(f"GAMMA = {g!r}, 1 + 1/sqrt 2 = {1 + 1 / S2!r}")
zs = [-1e-2, -0.1, -1.0, -1 - S2, -10.0, -1e3, -1e6]
# Tolerance: c1 = c0 + (3/(2 gamma)) k1 + (1/(2 gamma)) k2 is a sum of O(c0) terms that cancel when R is small, so
# its round-off is absolute, a few eps * c0 (c0 = 1), not relative to R; 16 eps allows for the two solves and the sum.
EPS16 = 16 * torch.finfo(torch.float64).eps
worst = max(abs(R_code(z) - R_formula(z, g)) for z in zs)
print("   R(z) code: " + ", ".join(f"z={z:.3g}: {R_code(z):.10e}" for z in zs))
report("(s1) code R(z) vs formula, gamma = GAMMA, worst |difference| (c0 = 1; absolute, 16 eps)", worst, EPS16)
lim = (1 + S2) / g**2
xs = [1e6, 1e9, 1e12]
print("   x R(-x): " + ", ".join(f"x={x:.0e}: {R_code(-x) * x:.10f}" for x in xs) + f"; limit (1+sqrt2)/gamma^2 = {lim:.10f}"
      " (info: at large x the product carries x times the absolute round-off of R)")
r12 = R_code(-1e12)
report("(s2) L-stability: |R(-1e12) - R_formula(-1e12)| (formula value (1+sqrt2)/(gamma^2 1e12) = 8.3e-13)",
       abs(r12 - R_formula(-1e12, g)), EPS16)
report("(s2) L-stability: |R(-1e12)|, must be below 1e-11 (R(-inf) = 0)", abs(r12), 1e-11)
grid = [0.0] + [10 ** (k / 4) for k in range(-16, 33)]
vals = [R_code(-x) for x in grid]
print(f"   R(-x) on {len(grid)} points x in [0, 1e8]: min {min(vals):.3e}, max {max(vals):.15f}")
report("(s3) 0 < R(-x) <= 1 on x in [0, 1e8]: number of violations", float(sum(not (0 < v <= 1 + 1e-15) for v in vals)),
       0.0)

ros.GAMMA = 1 - 1 / S2
try:
    gm = ros.GAMMA
    neg = [(x, R_code(-x), R_formula(-x, gm)) for x in (1.0, 2.0, 1 + S2 + 0.5, 10.0, 1e3)]
    print("   gamma = 1 - 1/sqrt2: " + ", ".join(f"x={x:.3g}: R={rc:.6e} (formula {rf:.6e})" for x, rc, rf in neg))
    bad = sum((rc < 0) != (x > 1 + S2) for x, rc, _ in neg) + sum(abs(rc - rf) > EPS16 for _, rc, rf in neg)
    tail = abs(R_code(-1e12))
    report("(s4) gamma = 1 - 1/sqrt2: sign of R changes at x = 1 + sqrt2 and matches the formula (mismatches)",
           float(bad), 0.0)
    report("(s4) gamma = 1 - 1/sqrt2: |R(-1e12)| (L-stable too)", tail, 1e-9)
    ros.GAMMA = 0.5
    rinf = R_code(-1e12)
    report("(s5) gamma = 1/2: |R(-1e12) - (-1)|, the formula's R(-inf) for a gamma off both roots", abs(rinf + 1), 1e-9)
finally:
    ros.GAMMA = g
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
