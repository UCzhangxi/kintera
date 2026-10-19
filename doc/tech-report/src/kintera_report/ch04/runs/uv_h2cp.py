"""use-h2-cp (@sec-ch04-equilibrate-uv): with the rotational heat capacity of H2 on, the state returned by
ThermoY.forward is off saturation at the temperature the host reads back.

    python -P uv_h2cp.py <nh3_160|nh3_120|h2o_300> <on|off>
"""
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import adjust, cell_from_tpx, write_card

CARD = """reference-state: {{Tref: 0., Pref: 1.e5{h2}}}
dynamics: {{equation-of-state: {{max-iter: 50}}}}
species:
  - {{name: H2, composition: {{H: 2}}, cv_R: 2.5}}
  - {{name: {v}, composition: {comp}, cv_R: 2.5, u0_R: 0.}}
  - {{name: {c}, composition: {comp}, cv_R: 9.0, u0_R: {u0}}}
reactions:
  - {{equation: {v} <=> {c}, type: nucleation, rate-constant: {{formula: {f}}}}}
"""
case, h2 = sys.argv[1], sys.argv[2] == "on"
v, c, comp, u0, f, T0, xv = {
    "nh3_160": ("NH3", "NH3(s)", "{N: 1, H: 3}", -5520., "nh3_ideal", 160., 1e-3),
    "nh3_120": ("NH3", "NH3(s)", "{N: 1, H: 3}", -5520., "nh3_ideal", 120., 1e-3),
    "h2o_300": ("H2O", "H2O(l)", "{H: 2, O: 1}", -3430., "h2o_ideal", 300., 5e-2)}[case]
card = write_card(f"h2cp_{case}_{sys.argv[2]}.yaml",
                  CARD.format(h2=", use-h2-cp: true" if h2 else "", v=v, c=c, comp=comp, u0=u0, f=f))
T = torch.tensor([T0])
P = torch.tensor([1e5])
x = torch.tensor([[1 - xv, xv, 0.]])
thy, rho, y = cell_from_tpx(card, T, P, x)
d, _, T1, lrh, _ = adjust(thy, rho, y, T)
print(f"{case} use-h2-cp={sys.argv[2]} diag {d.tolist()} T_after {T1.item():.4f} ln RH at that T {lrh[0, 0].item():+.3e}")
