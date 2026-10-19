"""Data of the cold-start figure (@sec-ch04-equilibrate-tp): ThermoX on tests/jupiter.yaml at 1e5 Pa, cells at
130..250 K, with max-iter 10 and 60; outer iterations and the largest remaining ln RH.

    KINTERA_REPO=<kintera checkout> python -P fig_tp_sweep.py <out.json>
"""
from pathlib import Path
import json
import sys

import torch
import kintera as kt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import VERSIONS, card_with, jupiter, jupiter_cold_cells, log_rh_x

out = {"provenance": {"sha": "0d9f67f97d841147e23283d2dcdab302238d2c45", "deck": "tests/jupiter.yaml",
                      "cells": "T = 130..250 K step 10, p = 1e5 Pa, x(H2O, NH3, H2S) = 3e-3, 3e-4, 1e-4, rest dry, "
                               "no condensate",
                      "command": "KINTERA_REPO=<kintera checkout> python -P src/kintera_report/ch04/runs/fig_tp_sweep.py "
                                 "<out.json>",
                      "device": "CPU, double", "versions": VERSIONS}}
T = torch.arange(130., 251., 10.)
P = torch.full_like(T, 1e5)
for mi in (10, 60):
    th = kt.ThermoX(kt.ThermoOptions.from_yaml(card_with(jupiter(), f"tp_{mi}.yaml", max_iter=mi)))
    x = jupiter_cold_cells(th.options.species(), T)
    d = torch.zeros(T.numel(), 1)
    th.forward(T, P, x, False, d)
    lr = log_rh_x(th, T, P, x).max(-1).values
    out[f"max_iter_{mi}"] = {"T": T.tolist(), "diag": d[:, 0].tolist(), "max_ln_rh": lr.tolist()}
json.dump(out, open(sys.argv[1], "w"), indent=1)
for mi in (10, 60):
    r = out[f"max_iter_{mi}"]
    print(f"max-iter {mi}: diag {r['diag']}")
    print(f"  max ln RH {[float(f'{v:.3g}') for v in r['max_ln_rh']]}")
