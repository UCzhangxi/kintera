"""Ch. 6 implicit steppers: kintera.evolve_implicit (backward Euler) and
kintera.evolve_ros2 (two-stage Rosenbrock), on A => B with k = 1 1/s.

Integrate to t = 1 with N and 2N steps; exact c_A = c0 exp(-1). The error ratio
should be ~2 (first order) and ~4 (second order) within 10 %; the atom total
c_A + c_B must be conserved to 1e-14 relative. ROS2 usage follows the bound
signature: stage 2 rate at c + k1/gamma, k1 = W^-1 S r, W = I/(gamma dt) - S J.
"""
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera as kt, torch  # noqa: E402

print(version_line())
card = """
reference-state: {Tref: 0., Pref: 1.e5}
species:
  - {name: A, composition: {H: 1}, cv_R: 1.5}
  - {name: B, composition: {H: 1}, cv_R: 1.5}
reactions:
  - equation: A => B
    type: arrhenius
    rate-constant: {A: 1., b: 0., Ea_R: 0.}
"""
path = os.path.join(tempfile.mkdtemp(), "ab.yaml")
with open(path, "w") as f:
    f.write(card)
op = kt.KineticsOptions.from_yaml(path)
kin = kt.Kinetics(op)
iA = op.species().index("A")
S = kin.stoich
T, P = torch.tensor([300.0]), torch.tensor([1.0e5])
cvol = torch.ones(1)
GAMMA = 1.0 + 1.0 / math.sqrt(2.0)
c_init = torch.zeros(1, 2)
c_init[0, iA] = 1.0
exact = math.exp(-1.0)


def rates(c):
    rate, rc_ddC, _ = kin.forward(T, P, c)
    return rate, kin.jacobian(T, c, cvol, rate, rc_ddC)


def step_be(c, dt):
    rate, jac = rates(c)
    return c + kt.evolve_implicit(rate, S, jac, dt)


def step_ros2(c, dt):
    rate1, jac = rates(c)
    W = torch.eye(2) / (GAMMA * dt) - S.matmul(jac)
    k1 = torch.linalg.solve(W, S.matmul(rate1.unsqueeze(-1))).squeeze(-1)
    rate2, _, _ = kin.forward(T, P, c + k1 / GAMMA)
    delta, _err = kt.evolve_ros2(rate1, rate2, S, jac, dt)
    return c + delta


def run(step, n):
    c = c_init.clone()
    drift = 0.0
    for _ in range(n):
        c = step(c, 1.0 / n)
        drift = max(drift, abs(c.sum().item() - 1.0))
    return abs(c[0, iA].item() - exact), drift


fails = 0
k = kin.forward_with_rate_constants(T, P, c_init)[3][0, 0].item()
print(f"rate constant k = {k:.15g} 1/s (card A = 1, unimolecular unit factor 1)")
for name, step, order, n in [("backward Euler", step_be, 2.0, 50),
                             ("ROS2", step_ros2, 4.0, 50)]:
    e1, d1 = run(step, n)
    e2, d2 = run(step, 2 * n)
    ratio = e1 / e2
    ok = abs(ratio / order - 1.0) <= 0.10
    fails += not ok
    print(f"{name}: err(N={n}) {e1:.4e}, err(N={2 * n}) {e2:.4e}; ratio measured {ratio:.4f}"
          f"  expected {order:.0f} tol 10%  {'PASS' if ok else 'FAIL'}")
    drift = max(d1, d2)
    ok = drift <= 1e-14
    fails += not ok
    print(f"{name}: atom drift max|c_A + c_B - 1| measured {drift:.2e}  tol 1e-14  "
          f"{'PASS' if ok else 'FAIL'}")
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
