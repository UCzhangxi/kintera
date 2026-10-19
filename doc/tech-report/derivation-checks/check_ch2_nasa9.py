"""Ch. 2 NASA-9 integration constants and the join at Tmid (data/nasa9.dat, src/thermo/nasa9.hpp).

(n1) b1 and b2 are fixed by tabulated enthalpy and entropy at a reference temperature: in the NASA-9 convention
     h(298.15 K) is the standard enthalpy of formation and s(298.15 K) the third-law standard entropy at 1 bar.
     The table's h and s at 298.15 K are compared with CODATA key values (Cox, Wagman and Medvedev, CODATA Key
     Values for Thermodynamics, 1989): H2O(g) dfH = -241.826 kJ/mol, S = 188.835 J/(mol K); H2 dfH = 0,
     S = 130.680; O2 dfH = 0, S = 205.152; CO2(g) dfH = -393.51, S = 213.785.
(n2) continuity at Tmid = 1000 K is a property of the data: the jumps of cp/R, h/R and s/R between the two ranges
     at 1000 K (info lines, H2, H2O, CH4, NH3, and the worst over all 293 species).
(n3) the code does not enforce it: kintera's g/RT jumps across 1000 K by exactly the table's jump (low range just
     below, high range at 1000 K, the mask T < Tmid).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera, torch  # noqa: E402
from kintera import nasa9_gibbs_rt  # noqa: E402

print(version_line())
R = 8.31446  # kintera Rgas (constants.h); the table's own R differs by about 1e-6 relative
fails = 0


def report(name, val, tol, ok=None):
    global fails
    ok = (val <= tol) if ok is None else ok
    fails += not ok
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {'PASS' if ok else 'FAIL'}")


path = os.path.join(os.path.dirname(kintera.__file__), "data", "nasa9.dat")
lines = [ln.strip() for ln in open(path) if ln.strip() and not ln.startswith("#")]
table = {}
k = 0
while k < len(lines):
    table[lines[k]] = [float(v) for v in " ".join(lines[k + 1:k + 5]).split()]
    k += 5
print(f"   {len(table)} species parsed from data/nasa9.dat")


def cp_r(a, T):
    return a[0] / T**2 + a[1] / T + a[2] + a[3] * T + a[4] * T**2 + a[5] * T**3 + a[6] * T**4


def h_r(a, T):  # h/R [K]
    return (-a[0] / T + a[1] * math.log(T) + a[2] * T + a[3] * T**2 / 2 + a[4] * T**3 / 3 + a[5] * T**4 / 4
            + a[6] * T**5 / 5 + a[8])


def s_r(a, T):
    return (-a[0] / (2 * T**2) - a[1] / T + a[2] * math.log(T) + a[3] * T + a[4] * T**2 / 2 + a[5] * T**3 / 3
            + a[6] * T**4 / 4 + a[9])


ref = {"H2O": (-241.826, 188.835), "H2": (0.0, 130.680), "O2": (0.0, 205.152), "CO2": (-393.51, 213.785)}
eh, es = 0.0, 0.0
for n, (dfh, s0) in ref.items():
    lo = table[n][:10]
    h298 = R * h_r(lo, 298.15) / 1e3
    s298 = R * s_r(lo, 298.15)
    eh, es = max(eh, abs(h298 - dfh)), max(es, abs(s298 - s0))
    print(f"   {n}: table h(298.15) = {h298:.4f} kJ/mol (CODATA {dfh}), s(298.15) = {s298:.4f} J/(mol K) (CODATA {s0})")
report("(n1) table h(298.15 K) vs CODATA dfH, worst abs [kJ/mol]", eh, 0.1)
report("(n1) table s(298.15 K) vs CODATA S, worst abs [J/(mol K)]", es, 0.05)

T = 1000.0
jumps = {}
for n, c in table.items():
    lo, hi = c[:10], c[10:]
    if not any(lo) or not any(hi):
        continue
    jumps[n] = (cp_r(hi, T) - cp_r(lo, T), h_r(hi, T) - h_r(lo, T), s_r(hi, T) - s_r(lo, T))
for n in ("H2", "H2O", "CH4", "NH3"):
    j = jumps[n]
    print(f"   (n2) {n}: jump high - low at 1000 K: cp/R {j[0]:+.3e}, h/R {j[1]:+.3e} K, s/R {j[2]:+.3e}")
for q, lab in enumerate(("cp/R", "h/R [K]", "s/R")):
    worst = max(jumps, key=lambda n: abs(jumps[n][q]))
    print(f"   (n2) worst |jump| of {lab} over {len(jumps)} species: {abs(jumps[worst][q]):.3e} ({worst})")

big = sorted((n for n in jumps if abs(jumps[n][1]) > 1.0), key=lambda n: -abs(jumps[n][1]))
print(f"   (n2) species whose h/R jumps by more than 1 K at 1000 K: {len(big)} of {len(jumps)}: "
      + ", ".join(f"{n} ({jumps[n][1]:+.3e} K)" for n in big))
names = ["H2", "H2O", "CH4", "NH3"]
d = 1e-7
gb = nasa9_gibbs_rt(torch.tensor([T - d]), names)[0]
ga = nasa9_gibbs_rt(torch.tensor([T]), names)[0]
worst = 0.0
for i, n in enumerate(names):
    lo, hi = table[n][:10], table[n][10:]
    tab_jump = (h_r(hi, T) / T - s_r(hi, T)) - (h_r(lo, T - d) / (T - d) - s_r(lo, T - d))
    code_jump = (ga[i] - gb[i]).item()
    worst = max(worst, abs(code_jump - tab_jump))
    print(f"   (n3) {n}: kintera g/RT(1000) - g/RT(1000 - 1e-7) = {code_jump:+.6e}, table (high at 1000, low at"
          f" 1000 - 1e-7) = {tab_jump:+.6e}")
report("(n3) kintera's g/RT jump across 1000 K equals the table's range jump (no blending), worst abs", worst, 1e-10)
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
