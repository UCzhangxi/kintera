"""Fixed-energy cold start (@sec-ch04-equilibrate-uv): tests/jupiter.yaml with uv-solver kkt and a given max-iter,
the five cold-start cells at 1e5 Pa; diagnostic and the largest ln RH at the temperature read back by the host.

    KINTERA_REPO=<kintera checkout> python -P uv_coldstart.py <max-iter>
"""
from pathlib import Path
import sys

import torch
import kintera as kt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import adjust, card_with, cell_from_tpx, jupiter, jupiter_cold_cells

mi = int(sys.argv[1])
card = card_with(jupiter(), f"uvc_{mi}.yaml", max_iter=mi, uv_solver="kkt")
names = kt.ThermoX(kt.ThermoOptions.from_yaml(card)).options.species()
T = torch.tensor([130., 150., 175., 200., 250.])
P = torch.full_like(T, 1e5)
thy, rho, y = cell_from_tpx(card, T, P, jupiter_cold_cells(names, T))
d, _, T1, lrh, _ = adjust(thy, rho, y, T)
print(f"max-iter {mi} diag {d.tolist()}")
print(" max ln RH at the host temperature", [float(f"{v:.3g}") for v in lrh.max(-1).values.tolist()])
