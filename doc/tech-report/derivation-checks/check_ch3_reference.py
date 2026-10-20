"""Ch.3 reference state (C3-a) and the condensate card's latent heat against its saturation curve (C3-g).

(a1) u_n/R = (u0_n - cv_n Tref) + cv_n T, h = u + R T for gases, h = u for condensates (TV->H, one species at a
     time, tests/jupiter.yaml).
(a2) gas entropy s/R = s0 + (cv+1) ln(T/Tref) - ln(p/Pref) for a pure gas (TPV->S).
(a4) with use-nasa9-cp the energy is referenced to 300 K: u(300)/R = u* + c* (300 - Tref), which is u* only when
     Tref = 300 K (H2O card with u0_R 1000, cv_R 3, Tref 300 and 250 K).
(a3) enthalpy and energy latent heat: l = h_v - h_c (ThermoX TV->H) and L = u_v - u_c (ThermoY VT->U) differ by
     R T, one mole of gas removed by vapour -> condensate.
(g1) the card latent heat l_card(T) = h_v - h_c against the curve's l_svp(T) = R T^2 d ln K/dT (a central
     difference of kintera's ln K), on the branch where each test cloud forms: H2O(l) on the liquid branch
     (280-320 K), NH3(s) on the solid branch (150-190 K). The cards of tests/jupiter.yaml at 0d9f67f do not
     satisfy C3-g: EXPECTED-FAIL, row K8 of UCzhangxi/kintera#54.
(g2) the same with the card values the derivation requires (cv_c = cv_v + 1 + gamma, u0 at Tref from beta T3),
     which are the values of the K8 fix: PASS.
(g3) step 4 of C3-g: the condensate entropy solved from saturation has T ds_c/dT = c_p,c (a constant-cv substance)
     only when the card matches its curve: jupiter.yaml EXPECTED-FAIL (K8), corrected cards PASS.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import thermo_x, species, version_line, DECK, kintera, torch  # noqa: E402
import ch3_card  # noqa: E402

R = 8.31446  # kintera Rgas (constants.h)
RES = []


def report(name, val, tol, ok, expected=None):
    if not math.isfinite(val):
        ok = False
    tag = "PASS" if ok else ("EXPECTED-FAIL" if expected else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}" + (f" ({expected})" if expected and not ok else ""))


def check_offsets():
    op, th = thermo_x()
    sp = species(op)
    ngas = len(op.vapor_ids())
    # the cards are read from the deck, so the line holds for whatever cards the build ships; a line parser for the
    # two fields, as in ch3_card.fixed_deck, keeps the check to kintera's own dependencies
    names = ("H2O", "H2O(l)", "NH3(s)")
    cv = {n: 2.5 for n in names}
    u0 = {n: 0.0 for n in names}
    cur = None
    with open(DECK) as f:
        for line in f:
            s_ = line.strip()
            if s_.startswith("- name:"):
                cur = s_.split(":", 1)[1].strip()
            elif cur in names and s_.startswith("cv_R:"):
                cv[cur] = float(s_.split(":", 1)[1])
            elif cur in names and s_.startswith("u0_R:"):
                u0[cur] = float(s_.split(":", 1)[1])
    worst = 0.0
    for name in cv:
        for T0 in (200.0, 300.0, 400.0):
            c = torch.zeros(1, len(sp))
            c[0, sp.index(name)] = 1.0
            h = th.compute("TV->H", [torch.tensor([T0]), c]).item() / R
            gas = sp.index(name) < ngas
            ref = (u0[name] - cv[name] * 300.0) + cv[name] * T0 + (T0 if gas else 0.0)
            worst = max(worst, abs(h - ref) / abs(ref))
    report("(a1) h/R = (u0 - cv Tref) + cv T (+ T for a gas), H2O, H2O(l), NH3(s) at 200-400 K (rel)", worst, 1e-13,
           worst < 1e-13)
    worst = 0.0
    for T0, p0 in ((250.0, 1e3), (300.0, 1e5), (350.0, 3e5)):
        c = torch.zeros(1, len(sp))
        c[0, sp.index("H2O")] = p0 / (R * T0)
        s = th.compute("TPV->S", [torch.tensor([T0]), torch.tensor([p0]), c]).item() / (c.sum().item() * R)
        ref = 3.5 * math.log(T0 / 300.0) - math.log(p0 / 1e5)
        worst = max(worst, abs(s - ref))
    report("(a2) pure H2O gas s/R = (cv+1) ln(T/Tref) - ln(p/Pref) (abs)", worst, 1e-12, worst < 1e-12)
    opy = kintera.ThermoOptions.from_yaml(DECK)
    ty = kintera.ThermoY(opy)
    ty.to(torch.float64)
    mu = th.buffer("mu")
    worst = 0.0
    for T0 in (250.0, 300.0, 350.0):
        T = torch.tensor([T0])
        cv_, cc_ = torch.zeros(1, len(sp)), torch.zeros(1, len(sp))
        cv_[0, sp.index("H2O")] = 1.0
        cc_[0, sp.index("H2O(l)")] = 1.0
        lat_h = (th.compute("TV->H", [T, cv_]) - th.compute("TV->H", [T, cc_])).item()
        lat_u = (ty.compute("VT->U", [cv_ * mu, T]) - ty.compute("VT->U", [cc_ * mu, T])).item()
        worst = max(worst, abs(lat_h - lat_u - R * T0) / lat_h)
        print(f"   T={T0} K: l = h_v - h_c = {lat_h:.6f} J/mol, L = u_v - u_c = {lat_u:.6f} J/mol, l - L = "
              f"{lat_h - lat_u:.6f} (R T = {R * T0:.6f})")
    report("(a3) l - L = R T for H2O -> H2O(l) (rel to l)", worst, 1e-12, worst < 1e-12)


PROBE = r"""
from kintera import ThermoOptions, ThermoX
op = ThermoOptions.from_yaml(sys.argv[1])
th = ThermoX(op); th.to(torch.float64)
names = kintera.species_names()
sp = [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]
ngas = len(op.vapor_ids()); R = 8.31446
def lnk(T):
    c = torch.zeros(len(T), len(sp)); c[:, 1:ngas] = (1.0 / (R * T)).unsqueeze(-1); c[:, 0] = 1.0
    return -kintera.relative_humidity(T, c, th.buffer("stoich"), op.nucleation(), ngas).log()
out = {}
for vap, cond, j, Ts in json.loads(sys.argv[2]):
    T = torch.tensor(Ts); h = 1e-3
    slope = (lnk(T + h)[:, j] - lnk(T - h)[:, j]) / (2 * h)
    cv_ = torch.zeros(len(Ts), len(sp)); cv_[:, sp.index(vap)] = 1.0
    cc_ = torch.zeros(len(Ts), len(sp)); cc_[:, sp.index(cond)] = 1.0
    lc = th.compute("TV->H", [T, cv_]) - th.compute("TV->H", [T, cc_])
    cd = torch.zeros(len(Ts), len(sp)); cd[:, 0] = 1.0
    cs = cd.clone(); cs[:, sp.index(cond)] = 1.0
    P = torch.full((len(Ts),), 1.0e5); e = 1e-4
    Sc = lambda t: th.compute("TPV->S", [t, P, cs]) - th.compute("TPV->S", [t, P, cd])
    tdsdt = T * (Sc(T + e) - Sc(T - e)) / (2 * e)
    out[cond] = {"l_card": lc.tolist(), "l_svp": (R * T * T * slope).tolist(), "Tdsdt": tdsdt.tolist(),
                 "cp": (th.compute("TV->cp", [T, cs]) - th.compute("TV->cp", [T, cd])).tolist()}
print(json.dumps(out))
"""
CASES = [["H2O", "H2O(l)", 0, [280.0, 290.0, 300.0, 310.0, 320.0]],
         ["NH3", "NH3(s)", 1, [150.0, 160.0, 170.0, 180.0, 190.0]]]


def check_cards():
    import json
    with open(DECK) as f:
        deck = f.read()
    for label, text, tag in (("tests/jupiter.yaml", deck, "K8"), ("corrected cards", ch3_card.fixed_deck(deck), None)):
        got = ch3_card.run(text, PROBE, json.dumps(CASES))
        worst = 0.0
        for cond, r in got.items():
            ratios = [a / b for a, b in zip(r["l_card"], r["l_svp"])]
            worst = max(worst, max(abs(q - 1) if math.isfinite(q) else math.inf for q in ratios))
            print(f"   {label}: {cond} l_card/l_svp = {', '.join(f'{q:.6f}' for q in ratios)}")
        name = f"(g{1 if tag else 2}) {label}: |l_card/l_svp - 1| on the forming branch, worst"
        report(name, worst, 1e-6, worst < 1e-6, tag)
        worst = 0.0
        for cond, r in got.items():
            q = [a / b for a, b in zip(r["Tdsdt"], r["cp"])]
            worst = max(worst, max(abs(v - 1) if math.isfinite(v) else math.inf for v in q))
            print(f"   {label}: {cond} T ds_c/dT / c_p,c = {', '.join(f'{v:.6f}' for v in q)}")
        report(f"(g3) {label}: solved condensate entropy has T ds_c/dT = c_p,c, worst rel", worst, 1e-6,
               worst < 1e-6, tag)


E4_CARD = """reference-state: {Tref: %s, Pref: 1.0e5, use-nasa9-cp: true}
species:
- {name: H2, composition: {H: 2}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 3.0, u0_R: 1000.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: H2O <=> H2O(l), type: nucleation, rate-constant: {formula: h2o_ideal}}
"""
E4_PROBE = r"""
from kintera import ThermoOptions, ThermoX
torch.set_default_dtype(torch.float64)
op = ThermoOptions.from_yaml(sys.argv[1]); th = ThermoX(op); th.to(torch.float64)
c = torch.zeros(1, 3); c[0, 1] = 1.0
u = lambda T0: th.compute("TV->H", [torch.tensor([T0]), c]).item() / 8.31446 - T0
print(json.dumps({"u300": u(300.0), "uTref": u(op.Tref())}))
"""


def check_nasa9_reference():
    worst = 0.0
    for tref in (300.0, 250.0):
        got = ch3_card.run(E4_CARD % tref, E4_PROBE)
        ref = 1000.0 + 3.0 * (300.0 - tref)
        worst = max(worst, abs(got["u300"] - ref))
        print(f"   use-nasa9-cp, Tref = {tref} K: u(300 K)/R = {got['u300']:.6f} (u* + c* (300 - Tref) = {ref:.6f}),"
              f" u(Tref)/R = {got['uTref']:.6f}")
    report("(a4) u(300 K)/R = u* + c* (300 K - Tref) under use-nasa9-cp, Tref 300 and 250 K (abs)", worst, 1e-9,
           worst < 1e-9)


if __name__ == "__main__":
    print(version_line())
    check_offsets()
    check_nasa9_reference()
    check_cards()
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "EXPECTED-FAIL")))
