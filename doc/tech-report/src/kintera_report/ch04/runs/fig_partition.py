"""Data of the partition figure (@sec-ch04-equilibrate-uv): uv-solver partition against kkt for the one-vapour
card (x_v 5e-2, 1e5 Pa, Tref 300 K), cells started at 297..303 K.

    python -P fig_partition.py <out.json>
"""
from pathlib import Path
import json
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import ONE_VAPOUR, VERSIONS, adjust, cell_from_tpx, write_card

out = {"provenance": {"sha": "e357792d50639d68e9090b542edf038d2b029aa2",
                      "deck": "ONE_VAPOUR card of src/kintera_report/ch04/runs/common.py: dry, H2O, H2O(l); h2o_ideal; "
                              "Tref 300 K; max-iter 50",
                      "cells": "start T = 297..303 K step 0.25, p = 1e5 Pa, x_v = 5e-2",
                      "command": "python -P src/kintera_report/ch04/runs/fig_partition.py <out.json>",
                      "device": "CPU, double", "versions": VERSIONS}}
T = torch.arange(297., 303.001, 0.25)
P = torch.full_like(T, 1e5)
x = torch.zeros(T.numel(), 3)
x[:, 1] = 5e-2
x[:, 0] = 1 - 5e-2
for s in ("partition", "kkt"):
    card = write_card(f"part_{s}.yaml", ONE_VAPOUR.format(tref=300., max_iter=50, solver=s))
    thy, rho, y = cell_from_tpx(card, T, P, x)
    d, _, T1, lrh, _ = adjust(thy, rho, y, T)
    out[s] = {"T0": T.tolist(), "diag": d.tolist(), "ln_rh": lrh[:, 0].tolist(), "T_after": T1.tolist()}
json.dump(out, open(sys.argv[1], "w"), indent=1)
for s in ("partition", "kkt"):
    print(s, "ln RH range", min(out[s]["ln_rh"]), max(out[s]["ln_rh"]), "diag", sorted(set(out[s]["diag"])))
