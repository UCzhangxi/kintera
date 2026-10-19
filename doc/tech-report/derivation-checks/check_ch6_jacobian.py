"""Ch. 6 temperature-feedback Jacobian at fixed internal energy.

A + B => C (Arrhenius A 1e-11 molecule cm s, b 0.5, Ea_R 800 K), cv_R 1.5/1.5/2.5,
u0_R 1000/2000/-5000, Tref 0, evolve_temperature on; T = 400 K, c = (2, 3, 1).
Reference: central finite difference of r(c, T(c)), T(c) solved from
U = sum_i c_i R (u0_i + cv_i T) = U0, step 1e-6 c_j. The fixed-T difference is
printed to show that the feedback term matters.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera as kt, torch  # noqa: E402

print(version_line())
R = kt.constants.Rgas
card = """
reference-state: {Tref: 0., Pref: 1.e5}
species:
  - {name: A, composition: {H: 1}, cv_R: 1.5, u0_R: 1000.}
  - {name: B, composition: {O: 1}, cv_R: 1.5, u0_R: 2000.}
  - {name: C, composition: {H: 1, O: 1}, cv_R: 2.5, u0_R: -5000.}
reactions:
  - equation: A + B => C
    type: arrhenius
    rate-constant: {A: 1.e-11, b: 0.5, Ea_R: 800.}
"""
path = os.path.join(tempfile.mkdtemp(), "a.yaml")
with open(path, "w") as f:
    f.write(card)
op = kt.KineticsOptions.from_yaml(path)
op.evolve_temperature(True)
kin = kt.Kinetics(op)
names = op.species()
u0 = torch.tensor([{"A": 1000.0, "B": 2000.0, "C": -5000.0}[n] for n in names])
cv = torch.tensor([{"A": 1.5, "B": 1.5, "C": 2.5}[n] for n in names])
c0 = torch.tensor([[{"A": 2.0, "B": 3.0, "C": 1.0}[n] for n in names]])
T0 = torch.tensor([400.0])
p = torch.tensor([1.0e5])
U0 = (c0[0] * R * (u0 + cv * T0)).sum()

rate, rc_ddC, rc_ddT, kf = kin.forward_with_rate_constants(T0, p, c0)
cvol = (c0[0] * cv * R).sum().reshape(1)
jac = kin.jacobian(T0, c0, cvol, rate, rc_ddC, rc_ddT, kf)


def r_fixed_u(c):
    T = (U0 - (c[0] * R * u0).sum()) / (c[0] * R * cv).sum()
    return kin.forward(T.reshape(1), p, c)[0][0, 0]


def r_fixed_t(c):
    return kin.forward(T0, p, c)[0][0, 0]


tol = 1e-8
worst = 0.0
for j, n in enumerate(names):
    h = 1e-6 * c0[0, j].item()
    cp, cm = c0.clone(), c0.clone()
    cp[0, j] += h
    cm[0, j] -= h
    fd_u = ((r_fixed_u(cp) - r_fixed_u(cm)) / (2 * h)).item()
    fd_t = ((r_fixed_t(cp) - r_fixed_t(cm)) / (2 * h)).item()
    J = jac[0, 0, j].item()
    err = abs(J - fd_u) / abs(fd_u)
    worst = max(worst, err)
    print(f"  dr/dc_{n}: jacobian {J:.10e}  FD(fixed U) {fd_u:.10e}  rel err {err:.2e}"
          f"  | FD(fixed T) {fd_t:.10e}  (feedback share {abs(fd_u - fd_t) / abs(fd_u):.2e})")
tag = "PASS" if worst <= tol else "FAIL"
print(f"T-feedback Jacobian vs fixed-U FD, worst rel err: measured {worst:.3e}  tol {tol:.0e}  {tag}")
