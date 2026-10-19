"""Ch. 9 source linearisation (python/atm2d/sources, python/atm2d/chemistry.py): Jacobians against FD.

(a) IndexedMassActionSource A + 2 B => C + D: tendency against k prod c^p times the coefficients, and its
    Jacobian against a central difference of the tendency.
(b) a kintera network through build_chemistry_jacobian: J = stoich @ dR/dc against a central difference of
    stoich @ rate(c) from Kinetics.forward.
(c) boundary sources: a flux Phi adds +-Phi/dz to the edge cell and nothing to J; a velocity v adds +-(v/dz) c and
    +-v/dz on the diagonal.
(d) build_source_linearization sums the terms; the charge-balance fold equals the derivative along the
    constraint c_E = sum of cations (FD with every cation and E moved together).
"""
import os
import sys
import tempfile
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera as kt, torch  # noqa: E402
import kintera.atm2d as a2  # noqa: E402
from kintera.atm2d.chemistry import build_chemistry_jacobian  # noqa: E402
from kintera.atm2d.sources import (IndexedMassActionSource, IndexedBoundaryFluxSource,  # noqa: E402
                                   IndexedBoundaryVelocitySource, IndexedFirstOrderSource)
from kintera.atm2d.sources.combine import build_source_linearization  # noqa: E402

warnings.filterwarnings("ignore", message="Sparse CSR tensor support")
print(version_line())
torch.manual_seed(9)
fails = 0


def report(name, val, tol, ok=None):
    global fails
    ok = (val <= tol) if ok is None else ok
    fails += not ok
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {'PASS' if ok else 'FAIL'}")


def state(conc, nl):
    x1f = torch.cat([torch.zeros(1), torch.cumsum(1e5 * (0.5 + torch.rand(nl)), 0)])
    return a2.AtmState2D(x1f=x1f, x2f=torch.tensor([0.0, 1.0]), temperature=torch.full((1, nl), 200.0),
                         pressure=torch.ones(1, nl), concentration=conc)


def fd_jacobian(fun, conc, rel=1e-6):
    """Central difference of fun(conc) -> (ncol, nlyr, ns) per cell: (ncol, nlyr, ns, ns)."""
    ncol, nl, ns = conc.shape
    J = torch.zeros(ncol, nl, ns, ns)
    for m in range(ns):
        h = rel * conc[..., m].abs().clamp_min(1e-30)
        cp, cm = conc.clone(), conc.clone()
        cp[..., m] += h
        cm[..., m] -= h
        J[..., :, m] = (fun(cp) - fun(cm)) / (2 * h).unsqueeze(-1)
    return J


def rel_err(J, Jfd):
    return ((J - Jfd).abs().max() / Jfd.abs().max()).item()


# (a) mass action
nl, ns = 5, 4
conc = 1e10 * (0.5 + torch.rand(1, nl, ns))
k = 3e-21 * (0.5 + torch.rand(1, nl))
src = IndexedMassActionSource(reactants=[0, 1], products=[2, 3], reactant_coefficients=[1, 2],
                              product_coefficients=[1, 1], rate_constant=k)
st = state(conc, nl)
lin = src.linearize(st)
w = k * conc[..., 0] * conc[..., 1] ** 2
ref = torch.stack([-w, -2 * w, w, w], -1)
report("(a1) mass action A + 2B => C + D: max |S - nu k c_A c_B^2| / max|S|",
       ((lin.tendency - ref).abs().max() / ref.abs().max()).item(), 1e-14)


def tend(cc, term=src):
    st.concentration = cc
    return term.linearize(st).tendency


report("(a2) mass action: max |J - FD| / max |FD| (central, h = 1e-6 c)", rel_err(lin.jacobian, fd_jacobian(tend, conc)),
       1e-7)
st.concentration = conc

# (b) kintera network
spec = {"H": {"H": 1}, "O": {"O": 1}, "H2": {"H": 2}, "OH": {"O": 1, "H": 1}, "H2O": {"H": 2, "O": 1}}
rx = [("2 H => H2", 2.0e-11, -0.5, 100.), ("OH => O + H", 3.0e-3, 0.7, 2000.),
      ("2 H + O => H2O", 4.0e-32, -1.2, 0.), ("O + H2 => OH + H", 1.0e-11, 1.0, 3160.)]
card = ("reference-state: {Tref: 300., Pref: 1.e5}\nspecies:\n"
        + "".join(f"  - {{name: {n}, composition: {{{', '.join(f'{e}: {v}' for e, v in c.items())}}}, cv_R: 2.5}}\n"
                  for n, c in spec.items())
        + "reactions:\n"
        + "".join(f"  - equation: {eq}\n    type: arrhenius\n    rate-constant: {{A: {A}, b: {b}, Ea_R: {E}}}\n"
                  for eq, A, b, E in rx))
path = os.path.join(tempfile.mkdtemp(), "k.yaml")
with open(path, "w") as f:
    f.write(card)
kin = kt.Kinetics(kt.KineticsOptions.from_yaml(path))
nk = len(spec)
Tk = torch.full((1, 3), 450.0)
Pk = torch.full((1, 3), 1e5)
ck = torch.tensor([2.0e-3, 5.0e-4, 1.5e-2, 3.0e-4, 8.0e-2]) * (0.5 + torch.rand(1, 3, nk))
Jk = build_chemistry_jacobian(kin, Tk, Pk, ck)


def kin_tend(cc):
    rate = kin.forward(Tk.reshape(-1), Pk.reshape(-1), cc.reshape(-1, nk))[0]
    return (rate @ kin.stoich.T).reshape(cc.shape)


report("(b) kintera network: max |stoich @ dR/dc - FD of stoich @ rate| / max |FD|",
       rel_err(Jk, fd_jacobian(kin_tend, ck)), 1e-7)

# (c) boundary sources
phi, v = 2.5e9, -0.3
flux_lo = IndexedBoundaryFluxSource(species=1, value=phi, boundary="lower")
flux_up = IndexedBoundaryFluxSource(species=1, value=phi, boundary="upper")
vel_up = IndexedBoundaryVelocitySource(species=2, value=v, boundary="upper")
dz = st.x1f[1:] - st.x1f[:-1]
lo, up, vu = flux_lo.linearize(st), flux_up.linearize(st), vel_up.linearize(st)
e = abs(lo.tendency[0, 0, 1].item() / (phi / dz[0].item()) - 1) + abs(up.tendency[0, -1, 1].item()
                                                                     / (-phi / dz[-1].item()) - 1)
e += (lo.tendency.abs().sum() - lo.tendency[0, 0, 1].abs()).item() + lo.jacobian.abs().sum().item()
report("(c1) flux source: +Phi/dz at the bottom cell, -Phi/dz at the top, zero elsewhere and zero J (rel)", e, 1e-15)
e = abs(vu.tendency[0, -1, 2].item() / (-(v / dz[-1].item()) * conc[0, -1, 2].item()) - 1)
e += rel_err(vu.jacobian, fd_jacobian(lambda cc: tend(cc, vel_up), conc))
st.concentration = conc
report("(c2) velocity source: -(v/dz) c at the top cell, and J against FD (rel)", e, 1e-7)

# (d) sum of terms and charge-balance fold: species [A+, B+, E, N]; E is produced from N at a rate set by c_E
# and lost by recombination with each cation, so every column of J depends on the electron.
ns = 4
cd = 1e8 * (0.5 + torch.rand(1, nl, ns))
cd[..., 2] = cd[..., 0] + cd[..., 1]  # a state on the constraint c_E = c_A+ + c_B+
sd = state(cd, nl)
terms = [IndexedMassActionSource(reactants=[0, 2], products=[3], reactant_coefficients=[1, 1],
                                 product_coefficients=[1], rate_constant=4e-9),
         IndexedMassActionSource(reactants=[1, 2], products=[3], reactant_coefficients=[1, 1],
                                 product_coefficients=[1], rate_constant=7e-9),
         IndexedFirstOrderSource(reactant=3, products=[0, 2], rate=1e-3)]
plain = build_source_linearization(sd, terms)
summed = [t.linearize(sd) for t in terms]
e = (plain.tendency - sum(x.tendency for x in summed)).abs().max().item() / plain.tendency.abs().max().item()
e += (plain.jacobian - sum(x.jacobian for x in summed)).abs().max().item() / plain.jacobian.abs().max().item()
report("(d1) build_source_linearization equals the sum of the terms (rel, exact up to round-off)", e, 1e-15)
folded = build_source_linearization(sd, terms, charge_balance_indices=([0, 1], 2))


def tend_d(cc):
    sd.concentration = cc
    return build_source_linearization(sd, terms).tendency


worst = 0.0
for j in (0, 1):  # move cation j and E together: dc_E/dc_j = 1 on the constraint
    h = 1e-6 * cd[..., j]
    cp, cm = cd.clone(), cd.clone()
    cp[..., j] += h
    cp[..., 2] += h
    cm[..., j] -= h
    cm[..., 2] -= h
    fd = (tend_d(cp) - tend_d(cm)) / (2 * h).unsqueeze(-1)
    worst = max(worst, ((folded.jacobian[..., :, j] - fd).abs().max() / fd.abs().max()).item())
sd.concentration = cd
report("(d2) folded cation column vs FD along c_E = sum of cations, worst rel", worst, 1e-7)
moved = (folded.jacobian[..., :, 0] - plain.jacobian[..., :, 0]).abs().max().item() / plain.jacobian.abs().max().item()
report("(d3) the fold changes the cation column (info that the test is not trivial): rel change, must EXCEED tol",
       moved, 1e-3, moved > 1e-3)
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
