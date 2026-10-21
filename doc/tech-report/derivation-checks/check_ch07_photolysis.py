"""Ch. 7 (photochemistry) numeric checks: photolysis rate quadrature, cross-section interpolation in T,
actinic-flux helpers, PhotoChem rates and Jacobian, channel element balance, shared wavelength grid."""
import atexit
import os
import shutil
import sys
import tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, WT, kintera as kt, torch  # noqa: E402

TMP = tempfile.mkdtemp(prefix="ch07_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
ERRORS = []  # FAIL lines and blocks that raised; the exit status is their number


def report(tag, what, x, tol, expected_fail=False, note=""):
    v = "PASS" if x <= tol else ("EXPECTED-FAIL" if expected_fail else "FAIL")
    if v == "FAIL":
        ERRORS.append(tag)
    print(f"[{tag}] {what}: {x:.3e} (tol {tol:.0e}) {v}{'  ' + note if note else ''}")


def load(name, text):
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write(text)
    op = kt.PhotoChemOptions.from_yaml(path)
    return op, kt.PhotoChem(op)


sys.stdout.reconfigure(line_buffering=True)
print(version_line())

# ---- synthetic deck: one branched reaction on a non-uniform grid, two temperature slabs ------------
SP = {"H2O": {"H": 2, "O": 1}, "OH": {"O": 1, "H": 1}, "H": {"H": 1}, "H2": {"H": 2}, "O": {"O": 1}}
lam = np.array([100., 115., 150., 160., 200.])                 # nm, non-uniform
s200 = np.array([[9e-18, 5e-18, 1e-18], [8e-18, 4e-18, 2e-18], [6e-18, 3e-18, 1.5e-18],
                 [5e-18, 2e-18, 1e-18], [2e-18, 1e-18, 0.2e-18]])  # columns: branch 0, 1, 2
s300 = s200 * np.array([1.0, 1.5, 0.5])
TGRID = (200., 300.)


def block(T, s):
    rows = "".join(f"          - [{l}, {a:.6e}, {b:.6e}, {c:.6e}]\n" for l, (a, b, c) in zip(lam, s))
    return f"      - format: YAML\n        temperature: {T}\n        data:\n{rows}"


card = ("reference-state: {Tref: 300., Pref: 1.e5}\nspecies:\n" + "".join(
    f"  - {{name: {n}, composition: {{{', '.join(f'{e}: {v}' for e, v in c.items())}}}, cv_R: 2.5}}\n"
    for n, c in SP.items()) + "reactions:\n  - equation: H2O => OH + H\n    type: photolysis\n"
    "    branches: [\"OH:1 H:1\", \"H2:1 O:1\"]\n    cross-section:\n" + block(TGRID[0], s200) + block(TGRID[1], s300))
op, pc = load("a.yaml", card)
ph = pc.module("photolysis")
names = list(op.species())
wave = ph.buffer("wavelength")


def sigma_T(T):  # numpy oracle: linear in T, held at the end slab outside [200, 300]
    w = np.clip((T - TGRID[0]) / (TGRID[1] - TGRID[0]), 0.0, 1.0)
    return (1 - w) * s200 + w * s300


# a. J = int sigma_d F dlambda, trapezoid with non-uniform spacing, branch 0 excluded
Ts = np.array([250., 180., 340.])
F = 1e14 * (1.0 + 0.3 * np.sin(lam / 17.0))                       # photons cm^-2 s^-1 nm^-1
ph.update_xs_diss_stacked(torch.tensor(Ts))
J = ph.forward(torch.tensor(Ts), torch.tensor(F)).numpy()[:, 0]
Jref = np.array([np.sum(0.5 * np.diff(lam) * ((sd := sigma_T(T)[:, 1:].sum(1) * F)[1:] + sd[:-1])) for T in Ts])
report("a1", "max rel |J - trapezoid(sum_{b>=1} sigma_b F)| at T = 250, 180, 340 K",
       np.max(np.abs(J / Jref - 1)), 1e-13)
Jwith0 = np.array([np.trapezoid(sigma_T(T).sum(1) * F, lam) for T in Ts])
print(f"[a2] J / J(branch 0 included) = {J[0] / Jwith0[0]:.4f}: branch 0 does not count towards J INFO")
# b. units: sigma [cm^2] x F [cm^-2 s^-1 nm^-1] x dlambda [nm] = s^-1; SI re-evaluation must agree
J_si = np.trapezoid(sigma_T(250.)[:, 1:].sum(1) * 1e-4 * F * 1e4 * 1e9, lam * 1e-9)
report("b", "rel |J(cgs, nm) - J(SI: area m2, flux per m2 per s per m of wavelength, wavelength m)|", abs(J[0] / J_si - 1), 1e-13)
# c. T interpolation: linear inside, constant outside (no extrapolation)
for T in (230., 150., 450.):
    xs = ph.interp_cross_section(0, wave, torch.tensor([T])).numpy().reshape(len(lam), 3)
    report("c", f"max |sigma(T={T:.0f}) - linear-in-T clamped oracle| / max sigma",
           np.abs(xs - sigma_T(T)).max() / s300.max(), 1e-14)
# d. actinic-flux helpers
src = torch.tensor([90., 130., 170., 210.])
fsrc = torch.tensor([1e13, 4e13, 2e13, 3e13])
fi = kt.interpolate_actinic_flux(src, fsrc, torch.tensor([85., 100., 155., 205., 230.])).numpy()
report("d1", "max rel |interpolate_actinic_flux - np.interp (linear, held at ends)|",
       np.max(np.abs(fi / np.interp([85., 100., 155., 205., 230.], src.numpy(), fsrc.numpy()) - 1)), 1e-14)
fs = kt.create_solar_flux(torch.tensor(lam), 2e14).numpy()
report("d2", "max rel |create_solar_flux - F_peak exp(-((l-500)/200)^2)|",
       np.max(np.abs(fs / (2e14 * np.exp(-((lam - 500) / 200) ** 2)) - 1)), 1e-14)
# e. PhotoChem rate r = J c_A and its Jacobian against a central finite difference
c = torch.tensor([[2.0e-2, 1e-4, 3e-4, 5e-5, 1e-6]])
T1 = torch.tensor([250.])
ph.update_xs_diss_stacked(T1)
r = pc.forward(T1, c, torch.tensor(F))
report("e1", "rel |r - J c_H2O|", abs(r[0, 0].item() / (Jref[0] * c[0, names.index("H2O")].item()) - 1), 1e-13)
jac = pc.jacobian(c, r)[0].numpy()  # (nreaction, nspecies)
fd = np.zeros(len(names))
for m in range(len(names)):
    h = 1e-6 * c[0, m].item()
    cp, cm = c.clone(), c.clone()
    cp[0, m] += h
    cm[0, m] -= h
    fd[m] = (pc.forward(T1, cp, torch.tensor(F))[0, 0] - pc.forward(T1, cm, torch.tensor(F))[0, 0]).item() / (2 * h)
report("e2", "max |dr/dc (jacobian) - central FD| / |dr/dc_H2O|", np.abs(jac[0] - fd).max() / abs(fd[0]), 1e-8)
# f. element balance: each branch versus PhotoChem.stoich (built from the equation only)
elem = sorted({e for cc in SP.values() for e in cc})
A = np.array([[SP[n].get(e, 0) for n in names] for e in elem])
S = pc.stoich.numpy()
report("f1", "max |atoms @ stoich| for 'H2O => OH + H'", np.abs(A @ S).max(), 0.0)
bst = [np.array([dict(b).get(n, 0.0) for n in names]) for b in op.photolysis().branches()[0]]
react = bst[0]
report("f2", "max |atoms @ (branch_b - reactant)| over branches 1, 2", max(np.abs(A @ (b - react)).max() for b in bst[1:]),
       0.0)
J2 = np.trapezoid(sigma_T(250.)[:, 2] * F, lam)
print(f"[f3] channel 2 (H2 + O) carries {J2 / Jref[0]:.3f} of J but PhotoChem.stoich books it as OH + H"
      f" (S7-1, quantified) INFO")

# ---- g. in-tree deck data/ch4_photolysis.yaml: equation stoichiometry and element balance --------------
import yaml  # noqa: E402
# the deck has no reference-state (PhotoChemOptions.from_yaml returns None on it), so its equation and branches
# are copied verbatim into a minimal deck with inline YAML cross sections; only the stoichiometry is tested
d4 = yaml.safe_load(open(os.path.join(WT, "data", "ch4_photolysis.yaml")))
rx4 = d4["reactions"][0]
comp4 = {s["name"]: s["composition"] for s in d4["species"]}
card4 = ("reference-state: {Tref: 300., Pref: 1.e5}\nspecies:\n" + "".join(
    f"  - {{name: '{n}', composition: {{{', '.join(f'{e}: {v}' for e, v in c.items())}}}, cv_R: 2.5}}\n"
    for n, c in comp4.items()) + f"reactions:\n  - equation: {rx4['equation']}\n    type: photolysis\n"
    f"    branches: {[str(b) for b in rx4['branches']]}\n    cross-section:\n      - format: YAML\n        data:\n"
    # column 0 is the total absorption (5e-18), at least the sum of the five channels (K18 convention)
    + "".join(f"          - [{l}, 5.e-18, 1.e-18, 1.e-18, 1.e-18, 1.e-18, 1.e-18]\n" for l in (100., 120., 140.)))
op4, pc4 = load("ch4.yaml", card4)
n4 = list(op4.species())
A4 = np.array([[comp4[n].get(e, 0) for n in n4] for e in ("C", "H", "N")])
S4 = pc4.stoich.numpy()
bal = A4 @ S4[:, 0]
report("g", "max |atoms @ stoich| of 'CH4 => CH4 + CH3 + ...' (C, H) = "
       f"({bal[0]:.0f}, {bal[1]:.0f}); stoich[CH4] = {S4[n4.index('CH4'), 0]:.0f}",
       np.abs(bal).max(), 0.0, expected_fail=True, note="(S7-1)")
b4 = [np.array([dict(b).get(n, 0.0) for n in n4]) for b in op4.photolysis().branches()[0]]
report("g2", "max |atoms @ (branch_b - CH4)| over the four product branches of the same deck",
       max(np.abs(A4 @ (b - b4[0])).max() for b in b4[2:]), 0.0)

# ---- h. in-tree deck data/chapman_cycle.yaml: second reaction on its own wavelength grid ---------------
opc = kt.PhotoChemOptions.from_yaml(os.path.join(WT, "data", "chapman_cycle.yaml"))
pcc = kt.PhotoChem(opc)
phc = pcc.module("photolysis")
wc = phc.buffer("wavelength").numpy()
Tc = torch.tensor([250.])
phc.update_xs_diss_stacked(Tc)
Jc = phc.forward(Tc, torch.full((len(wc),), 1e13)).numpy()[0]
# O3 table as written in the deck (oracle: its own wavelength column)
deck = yaml.safe_load(open(os.path.join(WT, "data", "chapman_cycle.yaml")))
ph_rx = [rx for rx in deck["reactions"] if rx.get("type") == "photolysis"]
rows = np.array(ph_rx[1]["cross-section"][0]["data"], dtype=float)
Jo3 = np.trapezoid(rows[:, 1] * 1e13, rows[:, 0])
print(f"[h0] module grid {wc.min():.0f}-{wc.max():.0f} nm; '{ph_rx[1]['equation']}' table "
      f"{rows[0, 0]:.0f}-{rows[-1, 0]:.0f} nm INFO")
report("h", f"rel |J({ph_rx[1]['equation']}) - trapezoid on its own grid| (code {Jc[1]:.4e}, oracle {Jo3:.4e} s^-1)",
       abs(Jc[1] / Jo3 - 1), 1e-12, expected_fail=True, note="(S7-2)")

# ---- i. DISORT hand-off: Beer-Lambert direct beam, 4 pi factor, layer order ------------------------------
# column 0 holds O2 in its top cell only; column 1 holds no absorber at all, so every one of its cells sees the
# unattenuated beam whichever end of the column the solver lets the beam in (i1 does not depend on the order)
try:
    sp = list(opc.species())
    idx = {n: i for i, n in enumerate(sp)}
    nlyr, ncol, mu0 = 4, 2, 0.5
    x1f = torch.linspace(0.0, 4.0e5, nlyr + 1)                   # height grows with index
    x2f = torch.linspace(0.0, 1.0e5, ncol + 1)
    conc = torch.zeros(ncol, nlyr, len(sp))
    conc[0, -1, idx["O2"]] = 1.0e12                              # column 0: absorber in the TOP cell only [cm^-3]
    st = kt.AtmState2D(x1f=x1f, x2f=x2f, temperature=torch.full((ncol, nlyr), 250.),
                       pressure=torch.logspace(5.0, 2.0, nlyr).unsqueeze(0).expand(ncol, nlyr),
                       concentration=conc)
    F0 = 1.0e12
    rt = kt.compute_actinic_flux_disort(pcc, st, torch.full((len(wc), ncol), F0), mu0=mu0,
                                        concentration_unit="molecules_cm3")
    k = int(np.argmin(np.abs(wc - 150.)))
    tau = rt.optical_depth[0, :, k].numpy()
    af = rt.actinic_flux[k, 0, :].numpy()
    af_clear = rt.actinic_flux[k, 1, :].numpy()
    report("i1", "max rel |actinic flux - F0| over the cells of the absorber-free column "
           "(4 pi J_mean = beam flux, no mu0 factor)", np.max(np.abs(af_clear / F0 - 1)), 1e-6)
    # oracle: sun above the top; cells below the absorber see F0 exp(-tau_top/mu0), the top cell sees the
    # level average 0.5 (1 + exp(-tau/mu0)) F0
    ref = np.array([np.exp(-tau[-1] / mu0)] * (nlyr - 1) + [0.5 * (1 + np.exp(-tau[-1] / mu0))]) * F0
    print(f"[i0] tau of top cell at 150 nm = {tau[-1]:.3f}; actinic flux bottom->top / F0 = "
          f"{np.array2string(af / F0, precision=4)}; oracle {np.array2string(ref / F0, precision=4)} INFO")
    report("i2", "max rel |actinic flux - Beer-Lambert from the top| (absorber in top cell)",
           np.max(np.abs(af / ref - 1)), 1e-6, expected_fail=True, note="(S7-3)")
except Exception as exc:  # pragma: no cover
    ERRORS.append("i")
    print(f"[i] DISORT hand-off not run: {type(exc).__name__}: {exc} ERROR")

# ---- i3. optical depth from the total absorption (column 0 = total, columns 1.. = channels) --------------
# a KINETICS7 absorber with total 1e-18 cm^2 and channels 3e-19 + 2e-19 (non-dissociating part 5e-19);
# the optical depth must be n sigma_total dz, with sigma_total = column 0 of the file; tolerance 1e-6 because the
# KINETICS7 reader parses its values as float (relative resolution about 6e-8)
def kin7(path, blocks, waves_A):  # header: equation, then nwave pairs (Angstrom, cm^2), 7 pairs per line
    with open(path, "w") as f:
        for eq, sig in blocks:
            f.write(f"{eq:<60s}{1:4d}{len(waves_A):4d}{len(waves_A):4d}{300.0:6.1f}\n")
            line = ""
            for m, w in enumerate(waves_A):
                line += f"{w:7.1f}{sig:10.3e}"
                if (m + 1) % 7 == 0 or m == len(waves_A) - 1:
                    f.write(line + "\n")
                    line = ""


try:
    sig_tot, n7, dz7 = 1.0e-18, 1.0e13, 1.0e5                    # cm^2, cm^-3, cm
    kin7(os.path.join(TMP, "A.kin7"), [("A:1", sig_tot), ("B:1", 3.0e-19), ("C:1", 2.0e-19)],
         [1000., 1500., 2000., 2500., 3000., 3500., 4000.])
    card7 = ("reference-state: {Tref: 300., Pref: 1.e5}\nspecies:\n"
             "  - {name: A, composition: {H: 1}, cv_R: 2.5}\n  - {name: B, composition: {H: 2}, cv_R: 2.5}\n"
             "  - {name: C, composition: {H: 3}, cv_R: 2.5}\nreactions:\n  - equation: A => B + C\n"
             "    type: photolysis\n    branches: [\"B:1\", \"C:1\"]\n"
             "    cross-section: [{format: KINETICS7, filename: A.kin7}]\n")
    cwd = os.getcwd()
    os.chdir(TMP)                                                # the deck names its file relative to here
    try:
        op7, pc7 = load("k7.yaml", card7)
    finally:
        os.chdir(cwd)
    w7 = pc7.module("photolysis").buffer("wavelength")
    conc7 = torch.zeros(1, 1, 3)
    conc7[0, 0, list(op7.species()).index("A")] = n7
    st7 = kt.AtmState2D(x1f=torch.tensor([0.0, dz7]), x2f=torch.tensor([0.0, 1.0]),
                        temperature=torch.full((1, 1), 250.), pressure=torch.full((1, 1), 1.0e4), concentration=conc7)
    rt7 = kt.compute_actinic_flux_disort(pc7, st7, torch.full((w7.numel(), 1), 1.0e12),
                                         concentration_unit="molecules_cm3")
    tau7 = rt7.optical_depth[0, 0, :].numpy()
    report("i3", f"max rel |optical depth - n sigma_total dz| for a KINETICS7 absorber, total 1e-18, channels "
           f"3e-19 + 2e-19 (code {tau7.max():.4f}, oracle {n7 * sig_tot * dz7:.4f})",
           np.max(np.abs(tau7 / (n7 * sig_tot * dz7) - 1)), 1e-6, expected_fail=True, note="(S7-4)")
except Exception as exc:  # pragma: no cover
    ERRORS.append("i3")
    print(f"[i3] optical depth from the total absorption not run: {type(exc).__name__}: {exc} ERROR")

sys.exit(len(ERRORS))
