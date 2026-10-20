"""Ch. 6 temperature-feedback Jacobian at fixed internal energy.

A + B => C (Arrhenius A 1e-11 molecule cm s, b 0.5, Ea_R 800 K), cv_R 1.5/1.5/2.5,
u0_R 1000/2000/-5000, Tref 0, evolve_temperature on; T = 400 K, c = (2, 3, 1).
Reference: central finite difference of r(c, T(c)), T(c) solved from
U = sum_i c_i R (u0_i + cv_i T) = U0, step 1e-6 c_j. The fixed-T difference is
printed to show that the feedback term matters. A second card, O + O2 <=> O3, checks the
forward and reverse columns of a reversible reaction; the reverse column is EXPECTED-FAIL at the pin (D65).
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
fails = int(tag == "FAIL")

# Reversible reaction O + O2 <=> O3 (K_c from the NASA-9 data of the species, as in check_ch6_rates.py [d]),
# cv_R 2.5/2.5/3.5, u0_R 0/0/-1000, Tref 0; T = 300 K, c = (1e-3, 0.2, 0.1), step 1e-5 c_j. The reverse column's feedback term uses rc_ddT, which at
# the pin is a copy of dk_f/dT (D65), so that column is expected to fail. K_c (NASA-9) and the card's u0/cv are not
# one consistent thermodynamics; that is harmless, because the reference differentiates the code's own forward with T
# solved from the card's U, so the check tests the implemented formula, not the thermodynamics of ozone.
card = """
reference-state: {Tref: 0., Pref: 1.e5}
species:
  - {name: O, composition: {O: 1}, cv_R: 2.5, u0_R: 0.}
  - {name: O2, composition: {O: 2}, cv_R: 2.5, u0_R: 0.}
  - {name: O3, composition: {O: 3}, cv_R: 3.5, u0_R: -1000.}
reactions:
  - equation: O + O2 <=> O3
    type: arrhenius
    rate-constant: {A: 1.7e-14, b: -2.4, Ea_R: 0.}
"""
path = os.path.join(tempfile.mkdtemp(), "r.yaml")
with open(path, "w") as f:
    f.write(card)
op = kt.KineticsOptions.from_yaml(path)
op.evolve_temperature(True)
kin = kt.Kinetics(op)
names = op.species()
u0 = torch.tensor([{"O": 0.0, "O2": 0.0, "O3": -1000.0}[n] for n in names])
cv = torch.tensor([{"O": 2.5, "O2": 2.5, "O3": 3.5}[n] for n in names])
c0 = torch.tensor([[{"O": 1e-3, "O2": 0.2, "O3": 0.1}[n] for n in names]])
T0 = torch.tensor([300.0])
U0 = (c0[0] * R * (u0 + cv * T0)).sum()
rate, rc_ddC, rc_ddT, kf = kin.forward_with_rate_constants(T0, p, c0)
cvol = (c0[0] * cv * R).sum().reshape(1)
jac = kin.jacobian(T0, c0, cvol, rate, rc_ddC, rc_ddT, kf)


def col_fixed_u(c, k):
    T = (U0 - (c[0] * R * u0).sum()) / (c[0] * R * cv).sum()
    return kin.forward(T.reshape(1), p, c)[0][0, k]


for k, what in ((0, "forward"), (1, "reverse")):
    worst = 0.0
    for j, n in enumerate(names):
        h = 1e-5 * c0[0, j].item()  # c_O3 enters the forward column only through T: a larger step keeps T above round-off
        cp, cm = c0.clone(), c0.clone()
        cp[0, j] += h
        cm[0, j] -= h
        fd_u = ((col_fixed_u(cp, k) - col_fixed_u(cm, k)) / (2 * h)).item()
        J = jac[0, k, j].item()
        err = abs(J - fd_u) / abs(fd_u)
        worst = max(worst, err)
        print(f"  {what} dr/dc_{n}: jacobian {J:.10e}  FD(fixed U) {fd_u:.10e}  rel err {err:.2e}")
    tag = "PASS" if worst <= tol else ("EXPECTED-FAIL" if k == 1 else "FAIL")
    fails += int(tag == "FAIL")
    note = "  (D65: reverse rc_ddT is a copy of dk_f/dT)" if k == 1 else ""
    print(f"reversible O + O2 <=> O3, {what} column T-feedback Jacobian vs fixed-U FD, worst rel err: "
          f"measured {worst:.3e}  tol {tol:.0e}  {tag}{note}")
sys.exit(1 if fails else 0)  # a FAIL line also fails the process; EXPECTED-FAIL does not
