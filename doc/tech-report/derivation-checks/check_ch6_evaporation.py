"""Ch. 6 evaporation checks (src/kinetics/evaporation.cpp).

(a) one product, CH4(s,p) => CH4, formula ideal, T = 80 K: the kinetic rate is
    kappa c_p max(K - c_v, 0), kappa = 12 D vm / d^2, K = svp/(R T).
(b) two products, X(s) => A + B: the rate constant is kappa x with the closed-form
    extent x solving (c1 + x)(c2 + x) = K, K = svp/(R T)^2.
"""
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera as kt, torch  # noqa: E402

print(version_line())
R = kt.constants.Rgas
tmp = tempfile.mkdtemp()
fails = 0


def report(name, val, tol, ok, expected_fail=False):
    global fails
    tag = "PASS" if ok else ("EXPECTED-FAIL" if expected_fail else "FAIL")
    fails += (not ok) and (not expected_fail)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}")


def card(text, name):
    path = os.path.join(tmp, name)
    with open(path, "w") as f:
        f.write(text)
    return path


def logsvp_ideal(T, T3, P3, beta, gamma):
    return math.log(P3) + beta * (1.0 - T3 / T) - gamma * math.log(T / T3)


# ---------------- (a) one product ----------------
T3, P3, beta, D, vm, d = 90.67, 11690.0, 12.87, 2.0e-5, 30.8e-6, 1.0e-5
one = f"""
reference-state: {{Tref: 0., Pref: 1.e5}}
species:
  - {{name: dry, composition: {{H: 2}}, cv_R: 2.5}}
  - {{name: CH4, composition: {{C: 1, H: 4}}, cv_R: 3.0}}
  - {{name: "CH4(s)", composition: {{C: 1, H: 4}}, cv_R: 4.0, u0_R: -1166.9229}}
  - {{name: "CH4(s,p)", composition: {{C: 1, H: 4}}, cv_R: 4.0, u0_R: -1166.9229}}
reactions:
  - equation: CH4(s) => CH4(s,p)
    type: coagulation
    rate-constant: {{A: 0., b: 0, Ea_R: 0.}}
  - equation: CH4(s,p) => CH4
    type: evaporation
    rate-constant: {{formula: ideal, T3: {T3}, P3: {P3}, beta: {beta}, gamma: 0.,
                    diff_c: {D}, diff_T: 0., diff_P: 0., vm: {vm}, diameter: {d}}}
"""
op = kt.KineticsOptions.from_yaml(card(one, "one.yaml"))
kin = kt.Kinetics(op)
names = op.species()
T = 80.0
K = math.exp(logsvp_ideal(T, T3, P3, beta, 0.0)) / (R * T)
kappa = 12.0 * D * vm / d**2
cp = 0.7
print(f"(a) T = {T} K, K = {K:.6e} mol/m^3, kappa = {kappa:.6e} 1/s, c_p = {cp}")


def evap_rate(cv):
    c = torch.zeros(1, len(names))
    c[0, names.index("CH4")] = cv
    c[0, names.index("CH4(s,p)")] = cp
    rate = kin.forward(torch.tensor([T]), torch.tensor([1.0e5]), c)[0]
    return rate[0, 1].item()


r = evap_rate(0.5 * K)
ref = kappa * cp * (K - 0.5 * K)
report("(a1) c_v = 0.5K: |rate - kappa c_p (K - c_v)|/ref", abs(r - ref) / ref, 1e-10,
       abs(r - ref) <= 1e-10 * ref)
r = evap_rate(K)
report("(a2) c_v = K: |rate| / (kappa c_p K)", abs(r) / (kappa * cp * K), 1e-12,
       abs(r) < 1e-12 * kappa * cp * K)
r = evap_rate(1.5 * K)
report("(a3) c_v = 1.5K: |rate| (must be exactly 0)", abs(r), 0.0, r == 0.0)

# ---------------- (b) two products ----------------
T3b, P3b, betab, gammab = 200.0, 100.0, 10.0, 1.0
two = f"""
reference-state: {{Tref: 0., Pref: 1.e5}}
species:
  - {{name: dry, composition: {{H: 2}}, cv_R: 2.5}}
  - {{name: NH3, composition: {{N: 1, H: 3}}, cv_R: 3.0}}
  - {{name: H2S, composition: {{H: 2, S: 1}}, cv_R: 3.0}}
  - {{name: "NH4SH(s)", composition: {{N: 1, H: 5, S: 1}}, cv_R: 9.0, u0_R: -5000.}}
reactions:
  - equation: NH4SH(s) => NH3 + H2S
    type: evaporation
    rate-constant: {{formula: ideal, T3: {T3b}, P3: {P3b}, beta: {betab}, gamma: {gammab},
                    diff_c: {D}, diff_T: 0., diff_P: 0., vm: {vm}, diameter: {d}}}
"""
op2 = kt.KineticsOptions.from_yaml(card(two, "two.yaml"))
kin2 = kt.Kinetics(op2)
n2 = op2.species()
worst = 0.0
for T, c1, c2 in [(200.0, 1e-3, 2e-3), (190.0, 1e-6, 5e-2), (210.0, 0.0, 1e-2),
                  (205.0, 3e-2, 1e-8)]:
    K2 = math.exp(logsvp_ideal(T, T3b, P3b, betab, gammab)) / (R * T) ** 2
    c = torch.zeros(1, len(n2))
    c[0, n2.index("NH3")] = c1
    c[0, n2.index("H2S")] = c2
    c[0, n2.index("NH4SH(s)")] = cp
    rate = kin2.forward(torch.tensor([T]), torch.tensor([1.0e5]), c)[0][0, 0].item()
    x = rate / (kappa * cp)
    res = abs((c1 + x) * (c2 + x) - K2) / K2
    worst = max(worst, res)
    print(f"    T = {T}, c1 = {c1:.1e}, c2 = {c2:.1e}: K = {K2:.6e}, x = {x:.6e}, "
          f"|(c1+x)(c2+x) - K|/K = {res:.2e}")
report("(b) two-product extent, worst |(c1+x)(c2+x) - K|/K", worst, 1e-12, worst <= 1e-12)
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
