"""Ch. 9 Ros2 embedded error estimate (python/atm2d/rosenbrock.py): error = |c1 - y2|.

Derivation: c1 - y2 = dt^2 (F/2 - gamma L) f + O(dt^3), with F the exact Jacobian, L the one the step uses,
f = f(c0); and the local error of c1 itself is O(dt^3).
(r1) linear decay dc/dt = -c with L = s F, s = 1 and 1/2: error / (dt^2 |(1/2 - gamma s)| c0) -> 1, with a
     deviation that falls as dt (first-order correction).
(r2) nonlinear dc/dt = -c^2, c0 = 1, exact L = -2c: error / (dt^2 |F f| |1/2 - gamma|) -> 1.
(r3) the estimate is one order larger than the true local error of c1: |c1 - c_exact| falls by ~1000 per decade of
     dt, the estimate by ~100, and the estimate exceeds the true error.
"""
import math
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera, torch  # noqa: E402,F401
import kintera.atm2d as a2  # noqa: E402
from kintera.atm2d.rosenbrock import GAMMA  # noqa: E402
from kintera.atm2d.sources import LocalSourceLinearization  # noqa: E402

warnings.filterwarnings("ignore", message="Sparse CSR tensor support")
print(version_line())
fails = 0


def report(name, val, tol, ok=None):
    global fails
    ok = (val <= tol) if ok is None else ok
    fails += not ok
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {'PASS' if ok else 'FAIL'}")


class Decay:
    def __init__(self, s):
        self.s = s

    def linearize(self, st):
        return LocalSourceLinearization(tendency=-st.concentration.clone(), jacobian=-self.s * torch.ones(1, 1, 1, 1))


class Square:
    def linearize(self, st):
        c = st.concentration
        return LocalSourceLinearization(tendency=-(c * c), jacobian=(-2.0 * c).view(1, 1, 1, 1))


def step(dt, term):
    st = a2.AtmState2D(x1f=torch.tensor([0.0, 1.0]), x2f=torch.tensor([0.0, 1.0]),
                       temperature=torch.full((1, 1), 200.0), pressure=torch.ones(1, 1),
                       concentration=torch.ones(1, 1, 1))
    r = a2.rosenbrock2_step(st, dt, kzz=torch.zeros(1, 1), source_terms=[term])
    return r.concentration.item(), float(torch.as_tensor(r.error).max())


dts = [1e-2, 1e-3, 1e-4]
for s in (1.0, 0.5):
    pred = [dt * dt * abs(0.5 - GAMMA * s) for dt in dts]  # F = -1, f = -1, so |F f| = 1
    dev = [abs(step(dt, Decay(s))[1] / p - 1) for dt, p in zip(dts, pred)]
    print(f"   L = {s} F: |error / prediction - 1| at dt = 1e-2, 1e-3, 1e-4: " + ", ".join(f"{d:.3e}" for d in dev)
          + f"; per-decade ratios {dev[0] / dev[1]:.3f}, {dev[1] / dev[2]:.3f}")
    report(f"(r1) L = {s} F: |error / (dt^2 |1/2 - gamma s|) - 1| at dt = 1e-4", dev[-1], 1e-3)
    report(f"(r1) L = {s} F: deviation falls as dt, max |ratio per decade - 10| / 10",
           max(abs(dev[0] / dev[1] - 10), abs(dev[1] / dev[2] - 10)) / 10, 0.05)
dev = [abs(step(dt, Square())[1] / (dt * dt * 2.0 * abs(0.5 - GAMMA)) - 1) for dt in dts]
print("   dc/dt = -c^2: |error / prediction - 1| at dt = 1e-2, 1e-3, 1e-4: " + ", ".join(f"{d:.3e}" for d in dev))
report("(r2) dc/dt = -c^2, exact L: |error / (dt^2 |F f| |1/2 - gamma|) - 1| at dt = 1e-4", dev[-1], 1e-3)
dts3 = [1e-1, 1e-2, 1e-3]
true = [abs(step(dt, Square())[0] - 1.0 / (1.0 + dt)) for dt in dts3]
est = [step(dt, Square())[1] for dt in dts3]
print("   dc/dt = -c^2: true |c1 - 1/(1+dt)| " + ", ".join(f"{t:.3e}" for t in true)
      + "; estimate " + ", ".join(f"{e:.3e}" for e in est))
rt, re_ = true[1] / true[2], est[1] / est[2]
print(f"   per-decade ratios dt 1e-2 -> 1e-3: true error {rt:.1f} (order 3 gives 1000), estimate {re_:.1f} (order 2 gives 100)")
report("(r3) true local error is O(dt^3): |log10(ratio) - 3|", abs(math.log10(rt) - 3), 0.05)
report("(r3) estimate is O(dt^2): |log10(ratio) - 2|", abs(math.log10(re_) - 2), 0.05)
report("(r3) estimate exceeds the true error at every dt (violations)", float(sum(e <= t for e, t in zip(est, true))), 0.0)
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
