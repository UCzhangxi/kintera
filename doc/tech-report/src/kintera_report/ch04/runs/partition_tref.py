"""Partition near Tref (@sec-ch04-equilibrate-uv): the one-vapour card (x_v 5e-2, 1e5 Pa) with a given Tref and
uv-solver, five cells started within 1 K of Tref.

    python -P partition_tref.py <Tref> <partition|kkt>
"""
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import ONE_VAPOUR, adjust, cell_from_tpx, write_card

tref, solver = float(sys.argv[1]), sys.argv[2]
card = write_card(f"tref_{int(tref)}_{solver}.yaml", ONE_VAPOUR.format(tref=tref, max_iter=50, solver=solver))
T = torch.tensor([tref - 1.0, tref - 0.5, tref, tref + 0.5, tref + 1.0])
P = torch.full_like(T, 1e5)
x = torch.zeros(T.numel(), 3)
x[:, 1] = 5e-2
x[:, 0] = 1 - 5e-2
thy, rho, y = cell_from_tpx(card, T, P, x)
d, _, T1, lrh, _ = adjust(thy, rho, y, T)
print(f"Tref {tref} solver {solver} T0 {T.tolist()}")
print(" diag", d.tolist())
print(" ln RH after", [round(v, 6) for v in lrh[:, 0].tolist()])
print(" T after", [round(v, 4) for v in T1.tolist()])
