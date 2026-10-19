"""Ch. 9 coupled Newton step (python/atm2d/newton/coupled.py): Newton's method and its large-dt limit.

Problem: one column of 6 layers, species [A, B], eddy diffusion (c_diffusion), sources 2 A => B (k),
B => A (k2) and a bottom flux Phi of A. The residual of one backward-Euler step and its Jacobian are written
here independently of atm2d (dense transport matrix from matvec, sources by hand):
    G(c) = c - c0 - dt [T c + S(c)],   G'(c) = I - dt [T + dS/dc].
(e1) one iteration of newton_implicit_step (no damping, no clip, no cap) equals c0 - G'(c0)^-1 G(c0), for a
     dt below 1 and above 1 (the code divides the system by dt when dt >= 1).
(e2) undamped iterates converge quadratically: observed order p = log(G_{k+1}/G_k) / log(G_k/G_{k-1}) near 2.
(e3) with damping_factor 0.5 applied at every iteration the convergence is linear with ratio 1/2.
(e4) large dt: the converged step satisfies T c + S(c) = (c - c0)/dt, and its distance to the steady state of
     T c + S(c) = 0 falls as 1/dt (decade ratios from dt = 1e9, where the 1/dt^2 term is below 1%).
"""
import math
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera, torch  # noqa: E402,F401
import kintera.atm2d as a2  # noqa: E402
from kintera.atm2d.sources import (IndexedMassActionSource, IndexedFirstOrderSource,  # noqa: E402
                                   IndexedBoundaryFluxSource)

warnings.filterwarnings("ignore", message="Sparse CSR tensor support")
print(version_line())
fails = 0


def report(name, val, tol, ok=None):
    global fails
    ok = (val <= tol) if ok is None else ok
    fails += not ok
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {'PASS' if ok else 'FAIL'}")


nl, ns = 6, 2
k, k2, phi = 1.0e-14, 1.0e-4, 1.0e9
x1f = torch.linspace(0.0, 6.0e5, nl + 1)
dz = x1f[1:] - x1f[:-1]
kzz = torch.full((1, nl), 1.0e5)
c_init = torch.zeros(1, nl, ns)
c_init[..., 0] = 3.0e10 * torch.linspace(1.0, 0.2, nl)
c_init[..., 1] = 1.0e9
st = a2.AtmState2D(x1f=x1f, x2f=torch.tensor([0.0, 1.0]), temperature=torch.full((1, nl), 200.0),
                   pressure=torch.ones(1, nl), concentration=c_init.clone())
terms = [IndexedMassActionSource(reactants=[0], products=[1], reactant_coefficients=[2],
                                 product_coefficients=[1], rate_constant=k),
         IndexedFirstOrderSource(reactant=1, products=[0], rate=k2),
         IndexedBoundaryFluxSource(species=0, value=phi, boundary="lower")]
Tm = a2.build_transport_matrix(st, kzz, form="c_diffusion")
N = nl * ns
Td = torch.zeros(N, N)
for j in range(N):
    e = torch.zeros(N)
    e[j] = 1.0
    Td[:, j] = Tm.matvec(e.view(1, nl, ns)).reshape(-1)


def S(c):
    A, B = c[..., 0], c[..., 1]
    out = torch.stack([-2 * k * A * A + k2 * B, k * A * A - k2 * B], -1)
    out[0, 0, 0] += phi / dz[0]
    return out


def dS(c):
    A = c[0, :, 0]
    J = torch.zeros(N, N)
    for i in range(nl):
        a, b = i * ns, i * ns + 1
        J[a, a], J[a, b], J[b, a], J[b, b] = -4 * k * A[i], k2, 2 * k * A[i], -k2
    return J


def F(c):
    return (Td @ c.reshape(-1)) + S(c).reshape(-1)


def G(c, c0, dt):
    return c.reshape(-1) - c0.reshape(-1) - dt * F(c)


def hand_newton(c, c0, dt):
    Gp = torch.eye(N) - dt * (Td + dS(c))
    return (c.reshape(-1) - torch.linalg.solve(Gp, G(c, c0, dt))).view(1, nl, ns)


def code(c0, dt, iters, damping=1.0, trigger=1.0, record=None):
    """newton_implicit_step with clip and cap off; `record` collects every iterate through the
    concentration_postprocess hook, which returns it unchanged."""
    st.concentration = c0.clone()
    hook = None if record is None else (lambda c: (record.append(c.clone()), c)[1])
    r = a2.newton_implicit_step(st, dt, kzz=kzz, source_terms=terms, transport_form="c_diffusion",
                                max_iterations=iters, convergence_tol=0.0, damping_factor=damping,
                                damping_trigger=trigger, clip_negative=False, mass_conservation_cap=False,
                                concentration_postprocess=hook)
    return r.concentration


# (e1)
worst = 0.0
for dt in (0.5, 1.0e3):
    c1 = code(c_init, dt, 1)
    ref = hand_newton(c_init, c_init, dt)
    worst = max(worst, ((c1 - ref).abs().max() / ref.abs().max()).item())
report("(e1) one code iteration vs c0 - G'(c0)^-1 G(c0), dt = 0.5 and 1e3, max rel", worst, 1e-12)

# (e2) quadratic convergence
dt = 1.0e5
scale = c_init.abs().max().item()
its = []
code(c_init, dt, 8, record=its)
res = [G(c_init, c_init, dt).abs().max().item() / scale] + [G(c, c_init, dt).abs().max().item() / scale for c in its]
print("   undamped, dt = 1e5: max|G(c^k)| / max c0 for k = 0..8: " + ", ".join(f"{r:.2e}" for r in res))
orders = [math.log(res[i + 1] / res[i]) / math.log(res[i] / res[i - 1]) for i in range(1, len(res) - 1)
          if res[i + 1] > 1e-12 and res[i] < 1.0]
print("   observed orders p_k once max|G| < 1 and while max|G| > 1e-12: " + ", ".join(f"{p:.3f}" for p in orders))
report("(e2) observed order of the last two estimates, max |p - 2|", max(abs(p - 2) for p in orders[-2:]), 0.1)

# (e3) damped: theta = 0.5 at every iteration (damping_trigger = 0)
itd = []
code(c_init, dt, 14, damping=0.5, trigger=0.0, record=itd)
resd = [G(c, c_init, dt).abs().max().item() for c in itd]
ratios = [resd[i + 1] / resd[i] for i in range(len(resd) - 1)]
print("   damped theta = 0.5: ratios max|G_{k+1}|/max|G_k| = " + ", ".join(f"{r:.4f}" for r in ratios))
report("(e3) damped iteration is linear with ratio 1/2: |last ratio - 0.5|", abs(ratios[-1] - 0.5), 0.01)

# (e4) large dt and the steady state
cs = c_init.clone()
for _ in range(60):  # Newton on F(c) = 0, by hand
    cs = (cs.reshape(-1) - torch.linalg.solve(Td + dS(cs), F(cs))).view(1, nl, ns)
print(f"   steady state by hand: max|F(c*)| / max|T c*| = {F(cs).abs().max() / (Td @ cs.reshape(-1)).abs().max():.1e}")
dists, ident = [], 0.0
for dt in (1.0e9, 1.0e10, 1.0e11):
    c = code(c_init, dt, 40)
    ident = max(ident, ((F(c) - (c - c_init).reshape(-1) / dt).abs().max() / F(c).abs().max()).item())
    dists.append(((c - cs).abs().max() / cs.abs().max()).item())
print("   max|c(dt) - c*| / max c* for dt = 1e9, 1e10, 1e11: " + ", ".join(f"{d:.3e}" for d in dists))
report("(e4a) converged step: |T c + S(c) - (c - c0)/dt| / |T c + S(c)|, worst", ident, 1e-9)
r1, r2 = dists[0] / dists[1], dists[1] / dists[2]
d8 = ((code(c_init, 1.0e8, 40) - cs).abs().max() / cs.abs().max()).item()
print(f"   (info) at dt = 1e8 the distance is {d8:.3e}: the O(1/dt^2) term is still a few per cent there, so the"
      " decade ratios are taken from 1e9 on")
report("(e4b) distance to the steady state falls as 1/dt: max |ratio per decade - 10| / 10",
       max(abs(r1 - 10), abs(r2 - 10)) / 10, 0.05)
print("ALL PASS" if fails == 0 else f"{fails} FAIL")
