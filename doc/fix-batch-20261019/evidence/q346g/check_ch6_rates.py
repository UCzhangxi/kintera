"""Ch. 6 (kinetics) numeric checks: mass action, Arrhenius units, Lindemann fall-off, detailed balance."""
import os
import sys
import math
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, WT, kintera as kt, torch  # noqa: E402

NA = 6.02214076e23
RGAS = 8.31446  # kintera's universal gas constant [J/mol/K]
TMP = tempfile.mkdtemp(prefix="ch6_")
P1 = torch.tensor([1e5])


def report(tag, what, x, tol, expected_fail=False, note=""):
    v = "PASS" if x <= tol else ("EXPECTED-FAIL" if expected_fail else "FAIL")
    print(f"[{tag}] {what}: {x:.3e} (tol {tol:.0e}) {v}{'  ' + note if note else ''}")


def load(name, text, evolve_T=False):
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write(text)
    op = kt.KineticsOptions.from_yaml(path)
    if evolve_T:
        op.evolve_temperature(True)
    return op, kt.Kinetics(op)


def species_block(spec):
    return "species:\n" + "".join(
        f"  - {{name: {n}, composition: {{{', '.join(f'{e}: {v}' for e, v in comp.items())}}}, cv_R: 2.5}}\n"
        for n, comp in spec.items())


print(version_line())

# ---- a/b. mass action, atom conservation, Arrhenius unit factor --------------------------------
SPA = {"H": {"H": 1}, "O": {"O": 1}, "H2": {"H": 2}, "OH": {"O": 1, "H": 1}, "H2O": {"H": 2, "O": 1}}
RXA = [("2 H => H2", 2, 2.0e-11, -0.5, 100.), ("OH => O + H", 1, 3.0e-3, 0.7, 2000.),
       ("2 H + O => H2O", 3, 4.0e-32, -1.2, 0.), ("O + H2 => OH + H", 2, 1.0e-11, 1.0, 3160.)]
card = "reference-state: {Tref: 300., Pref: 1.e5}\n" + species_block(SPA) + "reactions:\n" + "".join(
    f"  - equation: {eq}\n    type: arrhenius\n    rate-constant: {{A: {A}, b: {b}, Ea_R: {E}}}\n"
    for eq, _, A, b, E in RXA)
op, kin = load("a.yaml", card)
names = op.species()
T, c = torch.tensor([450.]), torch.tensor([[2.0e-3, 5.0e-4, 1.5e-2, 3.0e-4, 8.0e-2]])
rate, _, _, kf = kin.forward_with_rate_constants(T, P1, c)
orders = kin.forward_orders
pred = kf[0] * (c[0].unsqueeze(-1) ** orders).prod(0)
report("a1", "max rel |rate - k prod c^order|", ((rate[0] - pred).abs() / pred.abs()).max().item(), 1e-13)
print(f"     forward_orders == react_stoich: {torch.equal(orders, kin.react_stoich)};"
      f" order of H in '2 H => H2' = {orders[names.index('H'), 0].item():.0f}")
elem = sorted({e for comp in SPA.values() for e in comp})
atoms = torch.tensor([[float(SPA[n].get(e, 0)) for n in names] for e in elem])
report("a2", "max |atom matrix @ stoich| (exact)", (atoms @ kin.stoich).abs().max().item(), 0.0)
A_stored = list(op.arrhenius().A())
for j, (eq, n, A, b, E) in enumerate(RXA):
    fac = (NA * 1e-6) ** (n - 1)
    report("b", f"'{eq}' n={n} stored A / (A_in (N_A 1e-6)^{n - 1}) - 1",
           abs(A_stored[j] / (A * fac) - 1), 1e-12)
kA = [A * (NA * 1e-6) ** (n - 1) * (T.item() / 300.) ** b * math.exp(-E / T.item()) for _, n, A, b, E in RXA]
report("b", "max rel |k_f - A (T/300)^b exp(-Ea_R/T)|",
       max(abs(kf[0, j].item() / kA[j] - 1) for j in range(len(RXA))), 1e-13)

# ---- c. Lindemann fall-off ------------------------------------------------------------------------
SPO = {"N2": {"N": 2}, "O2": {"O": 2}, "O": {"O": 1}, "O3": {"O": 3}}
k0in, kinfin, Tc = (6.0e-34, -2.4, 0.), (3.0e-12, 0.3, 50.), 250.
card = "reference-state: {Tref: 300., Pref: 1.e5}\n" + species_block(SPO) + f"""reactions:
  - equation: O + O2 (+M) => O3 (+M)
    type: falloff
    low-P-rate-constant: {{A: {k0in[0]}, b: {k0in[1]}, Ea_R: {k0in[2]}}}
    high-P-rate-constant: {{A: {kinfin[0]}, b: {kinfin[1]}, Ea_R: {kinfin[2]}}}
    efficiencies: {{N2: 0.4}}
"""
op, kin = load("c.yaml", card)
names = op.species()
k0 = k0in[0] * (NA * 1e-6) ** 2 * (Tc / 300.) ** k0in[1] * math.exp(-k0in[2] / Tc)
kinf = kinfin[0] * (NA * 1e-6) * (Tc / 300.) ** kinfin[1] * math.exp(-kinfin[2] / Tc)
frac = {"N2": 0.78, "O2": 0.21, "O": 0.004, "O3": 0.006}
eff = {"N2": 0.4}
worst, lim = 0.0, {}
for lPr in range(-6, 7):
    Meff = 10. ** lPr * kinf / k0
    ntot = Meff / sum(frac[n] * eff.get(n, 1.) for n in names)
    cc = torch.tensor([[frac[n] * ntot for n in names]])
    k = kin.forward_with_rate_constants(torch.tensor([Tc]), P1, cc)[3][0, 0].item()
    worst = max(worst, abs(k / (k0 * Meff / (1 + k0 * Meff / kinf)) - 1))
    lim[lPr] = (k / (k0 * Meff), k / kinf)
report("c1", "max rel |k - k0 M/(1 + k0 M/kinf)|, Pr = 1e-6..1e6", worst, 1e-12)
report("c2", "low-P limit |k/(k0 M) - 1| at Pr=1e-6", abs(lim[-6][0] - 1), 2e-6)
report("c3", "high-P limit |k/kinf - 1| at Pr=1e6", abs(lim[6][1] - 1), 2e-6)

# ---- d. detailed balance with NASA-9 species (independent K_c) -------------------------------------
nasa9 = {}
with open(os.path.join(WT, "data", "nasa9.dat")) as f:
    lines = [ln for ln in f if not ln.startswith("#")]
for i in range(0, len(lines) - 4, 5):
    v = [float(x) for x in " ".join(lines[i + 1:i + 5]).split()]
    nasa9[lines[i].strip()] = (v[0:7] + v[8:10], v[10:17] + v[18:20])


def g_RT(name, T):
    a = nasa9[name][0 if T < 1000. else 1]
    h = -a[0] / T**2 + a[1] * math.log(T) / T + a[2] + a[3] * T / 2 + a[4] * T**2 / 3 + a[5] * T**3 / 4 \
        + a[6] * T**4 / 5 + a[7] / T
    s = -a[0] / (2 * T**2) - a[1] / T + a[2] * math.log(T) + a[3] * T + a[4] * T**2 / 2 + a[5] * T**3 / 3 \
        + a[6] * T**4 / 4 + a[8]
    return h - s


RXD = [({"O": 1, "O2": 1}, {"O3": 1}, 1.7e-14, -2.4, 0.), ({"O": 1, "O3": 1}, {"O2": 2}, 8.0e-12, 0., 2060.)]


def Kc(r, T):
    nu = {s: -v for s, v in r[0].items()}
    for s, v in r[1].items():
        nu[s] = nu.get(s, 0) + v
    return math.exp(-sum(v * g_RT(s, T) for s, v in nu.items()) + sum(nu.values()) * math.log(1e5 / (RGAS * T)))


eqn = lambda r: " + ".join(r[0]) + " <=> " + " + ".join(f"{v} {s}" if v > 1 else s for s, v in r[1].items())
card = "reference-state: {Tref: 300., Pref: 1.e5}\n" + species_block(SPO) + "reactions:\n" + "".join(
    f"  - equation: {eqn(r)}\n    type: arrhenius\n    rate-constant: {{A: {r[2]}, b: {r[3]}, Ea_R: {r[4]}}}\n"
    for r in RXD)
op, kin = load("d.yaml", card, evolve_T=True)
names, nr = op.species(), len(RXD)
for Td in (300., 1500.):
    K1, K2 = Kc(RXD[0], Td), Kc(RXD[1], Td)
    cO = 1e-30 if Td < 1000 else 1e-6  # c_O2 = K1 K2 c_O^2, c_O3 = K1 c_O c_O2 satisfy both equilibria
    cd = {"N2": 1.0, "O": cO, "O2": K1 * K2 * cO**2, "O3": K1 * cO * K1 * K2 * cO**2}
    cc = torch.tensor([[cd[n] for n in names]])
    rate, _, rcT, kf = kin.forward_with_rate_constants(torch.tensor([Td]), P1, cc)
    rf, rr = rate[0, :nr], rate[0, nr:]
    report("d1", f"T={Td:.0f} max |r_f - r_r|/r_f per reaction", ((rf - rr).abs() / rf).max().item(), 1e-10)
    report("d1", f"T={Td:.0f} max |stoich @ rate| / max r_f",
           ((kin.stoich @ rate[0]).abs().max() / rf.max()).item(), 1e-10)
    for j, r in enumerate(RXD):
        kr = rr[j].item() / math.prod(cd[s] ** v for s, v in r[1].items())
        report("d1", f"T={Td:.0f} R{j + 1} K_c code (k_f/k_r) = {kf[0, j].item() / kr:.6e} vs ours {Kc(r, Td):.6e}; rel",
               abs(kf[0, j].item() / kr / Kc(r, Td) - 1), 1e-10)

# d2: rc_ddT of the reverse column vs finite difference of k_r(T) = k_f(T)/K_c(T)
Td, cc = 300., torch.tensor([[{"N2": 1.0, "O2": 0.2, "O": 1e-8, "O3": 1e-6}[n] for n in names]])
h = Td * 1e-5
kr_of = lambda T: (kin.forward(torch.tensor([T]), P1, cc)[0][0, nr] / cc[0, names.index("O3")]).item()
kf_of = lambda T: kin.forward_with_rate_constants(torch.tensor([T]), P1, cc)[3][0, 0].item()
rcT = kin.forward_with_rate_constants(torch.tensor([Td]), P1, cc)[2]
if rcT is None:
    print("[d2] SKIP: rc_ddT is None even with evolve_temperature(True)")
else:
    dkf_fd, dkr_fd = (kf_of(Td + h) - kf_of(Td - h)) / (2 * h), (kr_of(Td + h) - kr_of(Td - h)) / (2 * h)
    report("d2", "forward column rc_ddT vs FD dk_f/dT, rel", abs(rcT[0, 0].item() / dkf_fd - 1), 1e-6)
    K, dlnK = Kc(RXD[0], Td), (math.log(Kc(RXD[0], Td + h)) - math.log(Kc(RXD[0], Td - h))) / (2 * h)
    true = dkf_fd / K - kf_of(Td) / K * dlnK
    code = rcT[0, nr].item()
    print(f"     reverse R1: code rc_ddT = {code:.6e}, FD dk_r/dT = {dkr_fd:.6e}, analytic d(k_f/K_c)/dT = {true:.6e}")
    print(f"     predicted code - true = dk_f/dT - d(k_f/K_c)/dT = {dkf_fd - true:.6e}; observed {code - dkr_fd:.6e}")
    report("d2", "reverse column rc_ddT vs FD dk_r/dT, rel", abs(code / dkr_fd - 1), 1e-6, expected_fail=True,
           note="(reverse column is a copy of dk_f/dT: no 1/K_c, no van 't Hoff term)")
    report("d2", "observed defect vs predicted (dk_f/dT - dk_r/dT), rel",
           abs((code - dkr_fd) / (dkf_fd - true) - 1), 1e-5)
