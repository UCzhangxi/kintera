"""Q346b D6 follow-up: the UV partition solver (src/thermo/equilibrate_uv.h:120-244) accepts a root only
when |E - h0| <= 64 eps max(|h0|, 1) (absolute, line ~160). With energies measured from Tref, h0 ~ 0 in
cells near T = Tref, so the tolerance collapses to ~1e-14 J/m^3 and the solve reports failure
(diag = -1) and returns the INPUT state unadjusted. Scan T0 across Tref (1-vapour card, x_v = 5e-2,
supersaturated) for Tref = 300 and 250 K, partition vs kkt; residual r = ln p_v - logsvp(T_host).
"""
import json
import subprocess
import sys
import tempfile

from common import WT

CARD = """
reference-state: {Tref: %s, Pref: 1.0e5}
species:
- {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {formula: h2o_ideal}}
dynamics: {equation-of-state: {uv-solver: %s, max-iter: 50}}
"""
PROBE = r"""
import json, math, sys, torch
sys.path.insert(0, sys.argv[2] + "/_pyinstall")
sys.path.insert(0, sys.argv[3])
torch.set_default_dtype(torch.float64)
from kintera import ThermoY, ThermoOptions
import tp_oracle
th = ThermoY(ThermoOptions.from_yaml(sys.argv[1]))
R = 8.314462618
mu = 1.0 / th.inv_mu
xv = 5e-2
TS = json.loads(sys.argv[4])
x = torch.tensor([1 - xv, xv, 0.0])
y = (x * mu / (x * mu).sum())[1:].reshape(2, 1).expand(2, len(TS)).clone()
rho = 1e5 * (x * mu).sum() / (R * torch.tensor(TS))
V = th.compute("DY->V", (rho, y))
U = th.compute("VT->U", (V, torch.tensor(TS)))
d = torch.zeros(len(TS), 1)
th.forward(rho, U, y, False, d)
V1 = th.compute("DY->V", (rho, y))
T1 = th.compute("VU->T", (V1, U))
out = []
for k in range(len(TS)):
    c = V1[k] / mu
    r = math.log((c[1] * R * T1[k]).item()) - tp_oracle.h2o_ideal(T1[k].item())
    out.append([TS[k], d[k].item(), T1[k].item(), (c[2] / (c[1] + c[2])).item(), r, U[k].item()])
print(json.dumps(out))
"""
sc = tempfile.mkdtemp(prefix="q346b_")
here = __file__.rsplit("/", 1)[0]
for tref in (300.0, 250.0):
    offs = [-1.0, -0.1, -0.03, -0.01, -1e-3, 0.0, 1e-3, 0.01, 0.03, 0.1, 1.0]
    TS = [tref + o for o in offs]
    got = {}
    for solver in ("kkt", "partition"):
        card = f"{sc}/d6t_{solver}_{tref:.0f}.yaml"
        open(card, "w").write(CARD % (tref, solver))
        r = subprocess.run([sys.executable, "-c", PROBE, card, WT, here, json.dumps(TS)],
                           capture_output=True, text=True, check=True)
        got[solver] = json.loads(r.stdout.strip().splitlines()[-1])
    print(f"\n== Tref = {tref:.0f} K, x_v = 5e-2 (supersaturated at all T0 below)")
    print("  T0-Tref[K]  U[J/m3]     | kkt: diag  T_host    cond/tot   r        | partition: diag  T_host    cond/tot   r")
    for a, b in zip(got["kkt"], got["partition"]):
        print(f"  {a[0] - tref:+9.3f}  {a[5]:+10.3e}  | {a[1]:4.0f}  {a[2]:8.3f}  {a[3]:.3e}  {a[4]:+.1e} "
              f"| {b[1]:4.0f}  {b[2]:8.3f}  {b[3]:.3e}  {b[4]:+.1e}")
