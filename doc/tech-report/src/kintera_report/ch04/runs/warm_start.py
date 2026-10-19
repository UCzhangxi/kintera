"""Warm start (@sec-ch04-warm-start-failures): a cold and a warm ThermoX solve of the same five cold-start cells
of tests/jupiter.yaml with max-iter 50; iteration counts and the largest difference of the results.

    KINTERA_REPO=<kintera checkout> python -P warm_start.py
"""
import sys
from pathlib import Path
import torch
import kintera as kt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import card_with, jupiter, jupiter_cold_cells

th = kt.ThermoX(kt.ThermoOptions.from_yaml(card_with(jupiter(), "warm.yaml", max_iter=50)))
T = torch.tensor([130., 150., 175., 200., 250.])
P = torch.full_like(T, 1e5)
x0 = jupiter_cold_cells(th.options.species(), T)
xc = x0.clone()
dc = torch.zeros(T.numel(), 1)
th.forward(T, P, xc, False, dc)
xw = x0.clone()
dw = torch.zeros(T.numel(), 1)
th.forward(T, P, xw, True, dw)  # reuses the buffers left by the cold call
print("T", T.tolist())
print("diag cold", dc[:, 0].tolist())
print("diag warm", dw[:, 0].tolist())
print("max |x_cold - x_warm|", (xc - xw).abs().max().item())
