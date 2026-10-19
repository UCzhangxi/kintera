"""Q346e: what does a misspelled named saturation formula do?

nucleation.cpp:68-103 accepts any `formula` string; only `ideal` and `antoine` are parsed inline
(log_svp.cpp:21-26). Build ThermoX and ThermoY from a card whose formula is a typo of h2o_ideal and
call forward on a supersaturated cell; report whether construction or forward raises, crashes, or
returns silently (and the result).
"""
import subprocess
import tempfile
import sys

from common import WT

CARD = """
reference-state: {Tref: 0., Pref: 1.0e5}
species:
- {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {formula: %s}}
"""
PROBE = r"""
import sys, torch
sys.path.insert(0, sys.argv[2] + "/_pyinstall")
torch.set_default_dtype(torch.float64)
from kintera import ThermoX, ThermoOptions
op = ThermoOptions.from_yaml(sys.argv[1])
print("options built", flush=True)
th = ThermoX(op)
print("ThermoX built", flush=True)
x = torch.tensor([[0.95, 0.05, 0.0]])
T = torch.tensor([300.0]); p = torch.tensor([1e5])
d = torch.zeros(1, 1)
out = th.forward(T, p, x, False, d)
print("forward returned:", [f"{v:.4e}" for v in out.flatten().tolist()], "diag =", d.item(), flush=True)
"""
sc = tempfile.mkdtemp(prefix="q346e_")
for name in ("h2o_ideal", "h2o_idael"):
    card = f"{sc}/formula_{name}.yaml"
    open(card, "w").write(CARD % name)
    r = subprocess.run([sys.executable, "-c", PROBE, card, WT], capture_output=True, text=True, cwd=sc)
    err = [l for l in r.stderr.strip().splitlines() if l.strip()]
    print(f"== formula: {name}  (exit code {r.returncode})")
    for l in r.stdout.strip().splitlines():
        if not l.startswith("["):
            print("   " + l)
    if err:
        print("   stderr last line: " + err[-1][:200])
