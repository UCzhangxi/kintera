"""Q346b D4 (UV half of the max-iter stall, src/thermo/equilibrate_uv.h:510-553) on tests/jupiter.yaml:
ThermoY.forward from an all-vapour state at fixed (rho, U) whose temperature makes the vapours
strongly supersaturated. diag = iterations, or -(100*status + iterations) on failure.
Reference: the same call with max-iter 200; reported: |x_H2O - x_H2O(ref)| / x_H2O(ref) after the call
and the host temperature from VU->T.
Also D6: KKT vs partition UV solver on a 1-vapour card (H2O <=> H2O(l)), max relative difference.
"""
import subprocess
import sys
import tempfile

from common import thermo_x, jupiter_x, torch, version_line, kintera, DECK, WT

print(version_line())
R = 8.314462618


def uv_state(TS, P=1e5):
    op, tx = thermo_x()
    sp, x = jupiter_x(op, n=len(TS))
    y = tx.compute("X->Y", [x])
    mu = (tx.mu * x).sum(-1)
    rho = P * mu / (R * torch.tensor(TS))
    return rho, y


def run(max_iter, TS):
    op = kintera.ThermoOptions.from_yaml(DECK)
    op.max_iter(max_iter)
    th = kintera.ThermoY(op)
    th.to(torch.float64)
    rho, y = uv_state(TS)
    y = y.clone()
    V = th.compute("DY->V", (rho, y))
    U = th.compute("VT->U", (V, torch.tensor(TS)))
    d = torch.zeros(len(TS), 1)
    th.forward(rho, U, y, False, d)
    V1 = th.compute("DY->V", (rho, y))
    T1 = th.compute("VU->T", (V1, U))
    X = th.compute("Y->X", [y])
    return d[:, 0], T1, X


TS = [130.0, 150.0, 175.0, 200.0, 250.0]
_, Tref, Xref = run(200, TS)
print("\n== D4/UV: jupiter.yaml all-vapour start at T0 (1 bar), max-iter 10 / 20 / 30 vs 200")
print("  T0[K]  " + "  ".join(f"diag(mi={m:2d}) relerr_xH2O  T_host[K]" for m in (10, 20, 30)) + "   T_ref[K]")
res = {m: run(m, TS) for m in (10, 20, 30)}
for k, T0 in enumerate(TS):
    row = f"  {T0:5.0f}  "
    for m in (10, 20, 30):
        d, T1, X = res[m]
        e = abs(X[k, 1] - Xref[k, 1]) / Xref[k, 1]
        row += f"  {d[k].item():9.0f}   {e.item():9.2e}  {T1[k].item():9.3f}"
    print(row + f"   {Tref[k].item():9.3f}")

# ---- D6: KKT vs partition, own interpreter per card (global species registry)
CARD = """
reference-state: {Tref: 300.0, Pref: 1.0e5}
species:
- {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {formula: h2o_ideal}}
dynamics: {equation-of-state: {uv-solver: %s, max-iter: 50}}
"""
PROBE = r"""
import json, sys, torch
sys.path.insert(0, sys.argv[2] + "/_pyinstall")
torch.set_default_dtype(torch.float64)
from kintera import ThermoY, ThermoOptions
th = ThermoY(ThermoOptions.from_yaml(sys.argv[1]))
R = 8.314462618
out = []
for T0 in (250., 270., 290., 300., 320.):
    for xv in (1e-3, 1e-2, 5e-2):
        mu = 1.0 / th.inv_mu
        x = torch.tensor([1 - xv, xv, 0.0])
        y = (x * mu / (x * mu).sum())[1:].reshape(2, 1).clone()
        rho = torch.tensor([1e5 * (x * mu).sum().item() / (R * T0)])
        V = th.compute("DY->V", (rho, y))
        U = th.compute("VT->U", (V, torch.tensor([T0])))
        d = torch.zeros(1, 1)
        th.forward(rho, U, y, False, d)
        T1 = th.compute("VU->T", (th.compute("DY->V", (rho, y)), U)).item()
        out.append([T0, xv, d.item(), y[0, 0].item(), y[1, 0].item(), T1])
print(json.dumps(out))
"""
import json
sc = tempfile.mkdtemp(prefix="q346b_")
got = {}
for solver in ("kkt", "partition"):
    card = f"{sc}/d6_{solver}.yaml"
    open(card, "w").write(CARD % solver)
    r = subprocess.run([sys.executable, "-c", PROBE, card, WT], capture_output=True, text=True, check=True)
    got[solver] = json.loads(r.stdout.strip().splitlines()[-1])
print("\n== D6: KKT vs partition (1 vapour), 15 states T0 in 250..320 K, x_v in 1e-3..5e-2")
print("  T0[K]  x_v     diag kkt/part   y_v kkt        rel diff y_v   rel diff y_c   dT[K]")
worst = 0.0
for a, b in zip(got["kkt"], got["partition"]):
    dyv = abs(a[3] - b[3]) / max(abs(a[3]), 1e-300)
    dyc = abs(a[4] - b[4]) / max(abs(a[4]), 1e-300) if a[4] or b[4] else 0.0
    worst = max(worst, dyv, dyc)
    print(f"  {a[0]:5.0f}  {a[1]:.0e}  {a[2]:4.0f}/{b[2]:<4.0f}   {a[3]:.6e}   {dyv:.2e}       {dyc:.2e}     {a[5] - b[5]:+.1e}")
print(f"  worst relative difference: {worst:.2e}")
