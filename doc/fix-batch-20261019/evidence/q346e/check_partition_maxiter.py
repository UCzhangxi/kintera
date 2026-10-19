"""Q346e: does the YAML `max-iter` cap the partition method's temperature search?

The partition loop runs `while (... iterations < *max_iter)` (src/thermo/equilibrate_uv.h:201) and on
success writes diag = iterations (line 229). Scan a one-vapour card (Tref = 0)
over start temperatures and vapour amounts with uv-solver: partition at max-iter 3, 5, 10 (default) and
50; print diag per cell (n >= 1 success after n passes, -1 failure).
"""
import json
import tempfile
import subprocess
import sys

from common import WT

CARD = """
reference-state: {Tref: 0., Pref: 1.0e5}
species:
- {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {formula: h2o_ideal}}
dynamics: {equation-of-state: {uv-solver: partition, max-iter: %d}}
"""
PROBE = r"""
import json, sys, torch
sys.path.insert(0, sys.argv[2] + "/_pyinstall")
torch.set_default_dtype(torch.float64)
from kintera import ThermoY, ThermoOptions
th = ThermoY(ThermoOptions.from_yaml(sys.argv[1]))
R = 8.314462618
mu = 1.0 / th.inv_mu
cells = json.loads(sys.argv[3])
x = torch.tensor([[1 - xv, xv, 0.0] for _, xv in cells])
TS = torch.tensor([t for t, _ in cells])
y = (x * mu / (x * mu).sum(-1, keepdim=True))[:, 1:].T.contiguous()
rho = 1e5 * (x * mu).sum(-1) / (R * TS)
V = th.compute("DY->V", (rho, y))
U = th.compute("VT->U", (V, TS))
d = torch.zeros(len(cells), 1)
th.forward(rho, U, y, False, d)
print(json.dumps(d[:, 0].tolist()))
"""
sc = tempfile.mkdtemp(prefix="q346e_")
cells = [(t, xv) for xv in (1e-3, 1e-2, 5e-2) for t in (200., 250., 280., 300., 320.)]
res = {}
for mi in (3, 5, 10, 50):
    card = f"{sc}/part_mi{mi}.yaml"
    open(card, "w").write(CARD % mi)
    r = subprocess.run([sys.executable, "-c", PROBE, card, WT, json.dumps(cells)],
                       capture_output=True, text=True, check=True, cwd=sc)
    res[mi] = json.loads(r.stdout.strip().splitlines()[-1])
print("uv-solver partition, Tref 0, 1 bar; diag per cell (n = passes on success, -1 = failed)")
print("  x_v      T0[K] | max-iter 3   5   10   50")
for k, (t, xv) in enumerate(cells):
    print(f"  {xv:.0e}  {t:6.1f} |   " + "  ".join(f"{res[mi][k]:4.0f}" for mi in (3, 5, 10, 50)))
for mi in (3, 5, 10, 50):
    print(f"max-iter {mi}: {sum(v < 0 for v in res[mi])} of {len(cells)} cells failed")
