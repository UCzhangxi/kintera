"""What the gain matrix holds after a solve (@sec-ch04-warm-start-failures): ThermoX at fixed T, p and ThermoY at
fixed U, V (kkt and partition), on the one-vapour card at 1e5 Pa started at 300 K; converged and non-converged cells.

    python -P gain_zeros.py
"""
import sys
from pathlib import Path
import torch
import kintera as kt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import ONE_VAPOUR, adjust, cell_from_tpx, write_card

T = torch.tensor([300.])
P = torch.tensor([1e5])
x = torch.tensor([[1 - 5e-2, 5e-2, 0.]])
for mi in (50, 1):
    card = write_card(f"g_tp_{mi}.yaml", ONE_VAPOUR.format(tref=300., max_iter=mi, solver="kkt"))
    th = kt.ThermoX(kt.ThermoOptions.from_yaml(card))
    xx = x.clone()
    d = torch.zeros(1, 1)
    g = th.forward(T, P, xx, False, d)
    print(f"ThermoX max-iter {mi}: diag {d[0, 0].item():.0f}, gain {g.flatten().tolist()}")
for s, mi in (("kkt", 50), ("kkt", 1), ("partition", 50)):
    card = write_card(f"g_uv_{s}_{mi}.yaml", ONE_VAPOUR.format(tref=0., max_iter=mi, solver=s))
    thy, rho, y = cell_from_tpx(card, T, P, x)
    d, g, _, lrh, _ = adjust(thy, rho, y, T)
    print(f"ThermoY {s} max-iter {mi}: diag {d[0].item():.0f}, gain {g.flatten().tolist()}, ln RH {lrh[0, 0].item():+.1e}")
