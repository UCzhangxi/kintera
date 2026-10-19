"""Q346b D12: ThermoY.forward (src/thermo/thermo_y.cpp:347-356) hands the UV solver u0 + cv0*T
energies built from constant cv_R, while VT->U / VU->T use the H2 rotational cp when
`use-h2-cp: true`. Check: a supersaturated H2 + vapour parcel at fixed (rho, U). After forward,
the host recovers T from VU->T with the same U; the vapour must then sit on its saturation curve.
Residual r = ln(p_vap) - logsvp(T) after forward; expected 0 to ~ftol.
Control: identical deck with use-h2-cp off.
Each card runs in its own interpreter (kintera's species registry is global).
"""
import json
import subprocess
import sys
import tempfile

from common import WT

CARD = """
reference-state: {Tref: 300.0, Pref: 1.0e5%(h2)s}
species:
- {name: H2, composition: {H: 2}, cv_R: 2.5}
- {name: %(v)s, composition: %(comp)s, cv_R: 2.5, u0_R: 0.}
- {name: %(v)s(c), composition: %(comp)s, cv_R: 9.0, u0_R: %(u0)s}
reactions:
- {equation: '%(v)s <=> %(v)s(c)', type: nucleation, rate-constant: {formula: %(f)s}}
dynamics: {equation-of-state: {max-iter: 50}}
"""

PROBE = r"""
import json, sys, math, torch
sys.path.insert(0, sys.argv[2] + "/_pyinstall")
torch.set_default_dtype(torch.float64)
from kintera import ThermoY, ThermoOptions
sys.path.insert(0, sys.argv[3])
import tp_oracle
th = ThermoY(ThermoOptions.from_yaml(sys.argv[1]))
T0, P0, xv, f = float(sys.argv[4]), 1e5, float(sys.argv[5]), sys.argv[6]
svp = getattr(tp_oracle, f)
R = 8.314462618
mu = 1.0 / th.inv_mu
# mole fractions H2 / vapour / cloud -> mass fractions
x = torch.tensor([1 - xv, xv, 0.0])
y = x * mu / (x * mu).sum()
rho = torch.tensor([P0 * (x * mu).sum().item() / (R * T0)])
yfrac = y[1:].reshape(2, 1).clone()
V = th.compute("DY->V", (rho, yfrac))
U = th.compute("VT->U", (V, torch.tensor([T0])))
d = torch.zeros(1, 1)
th.forward(rho, U, yfrac, False, d)
V1 = th.compute("DY->V", (rho, yfrac))
T1 = th.compute("VU->T", (V1, U)).item()
c = V1[0] / mu
pv = (c[1] * R * T1).item()
r = math.log(pv) - svp(T1)
print(json.dumps({"diag": d.item(), "T1": T1, "cloud_frac": (c[2] / (c[1] + c[2])).item(), "r": r}))
"""


SC = tempfile.mkdtemp(prefix="q346b_")


def run(h2, v, comp, u0, f, T0, xv):
    card = f"{SC}/{v}_{h2 or 'off'}.yaml"
    h2s = f", use-h2-cp: true, h2-cp-mode: {h2}" if h2 else ""
    open(card, "w").write(CARD % dict(h2=h2s, v=v, comp=comp, u0=u0, f=f))
    here = __file__.rsplit("/", 1)[0]
    res = subprocess.run([sys.executable, "-c", PROBE, card, WT, here, str(T0), str(xv), f],
                         capture_output=True, text=True)
    if res.returncode:
        return {"error": res.stderr.strip().splitlines()[-1]}
    return json.loads(res.stdout.strip().splitlines()[-1])


print("vapour  T0[K]  x_vap   h2-cp        diag   T_after[K]   cloud/total   r=ln p - logsvp")
for v, comp, u0, f, T0, xv in [("H2O", "{H: 2, O: 1}", -3430., "h2o_ideal", 300.0, 0.05),
                               ("NH3", "{N: 1, H: 3}", -5520., "nh3_ideal", 160.0, 0.02),
                               ("NH3", "{N: 1, H: 3}", -5520., "nh3_ideal", 120.0, 0.002)]:
    for h2 in (None, "normal", "equilibrium"):
        o = run(h2, v, comp, u0, f, T0, xv)
        if "error" in o:
            print(f"{v:6s} {T0:6.0f}  {xv:.3f}  {str(h2):11s}  ERROR {o['error']}")
            continue
        print(f"{v:6s} {T0:6.0f}  {xv:.3f}  {str(h2):11s} {o['diag']:5.0f}  {o['T1']:10.4f}   "
              f"{o['cloud_frac']:10.4e}   {o['r']:+.3e}")
