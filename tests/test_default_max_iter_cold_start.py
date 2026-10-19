"""Default `max-iter`: cold supersaturated starts on tests/jupiter.yaml must converge.

tests/jupiter.yaml sets no `max-iter`, so ThermoOptions uses its default. From an
all-vapour start (x_H2O 2.5e-3, x_NH3 3e-4, x_H2S 8e-5, 1 bar), ThermoX.forward at
130-200 K and ThermoY.forward at fixed (rho, U) from 130-150 K must converge (diag >= 1)
with the default, to the same state as with max-iter 200. CPU and, if present, CUDA.

Each run is its own interpreter: kintera's species registry is global.
"""

import json
import os
import subprocess
import sys

import pytest
import torch

DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jupiter.yaml")

PROBE = r"""
import json, sys, torch
torch.set_default_dtype(torch.float64)
import kintera
from kintera import ThermoOptions, ThermoX, ThermoY
deck, dev, mode, TS = sys.argv[1], torch.device(sys.argv[2]), sys.argv[3], json.loads(sys.argv[4])
op = ThermoOptions.from_yaml(deck)
if len(sys.argv) > 5:
    op.max_iter(int(sys.argv[5]))
names = kintera.species_names()
sp = [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]
n = len(TS)
x = torch.zeros(n, len(sp))
for s, v in (("H2O", 2.5e-3), ("NH3", 3e-4), ("H2S", 8e-5)):
    x[:, sp.index(s)] = v
x[:, 0] = 1 - x[:, 1:].sum(-1)
T = torch.tensor(TS)
d = torch.zeros(n, 1, device=dev)
if mode == "tp":
    th = ThermoX(op)
    th.to(dev)
    x = x.to(dev)
    th.forward(T.to(dev), torch.full((n,), 1e5, device=dev), x, diag=d)
    out = x
else:
    tx = ThermoX(op)
    y = tx.compute("X->Y", [x])
    rho = 1e5 * (tx.mu * x).sum(-1) / (8.314462618 * T)
    th = ThermoY(op)
    th.to(dev)
    y, rho = y.to(dev).contiguous(), rho.to(dev)
    U = th.compute("VT->U", (th.compute("DY->V", (rho, y)), T.to(dev)))
    th.forward(rho, U, y, False, d)
    out = th.compute("Y->X", [y])
print(json.dumps({"default_max_iter": ThermoOptions.from_yaml(deck).max_iter(),
                  "diag": d[:, 0].tolist(), "x": out.cpu().tolist()}))
"""

DEVICES = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])


def _run(tmp_path, device, mode, TS, *max_iter):
    res = subprocess.run([sys.executable, "-c", PROBE, DECK, device, mode, json.dumps(TS)]
                         + [str(m) for m in max_iter],
                         capture_output=True, text=True, check=True, cwd=tmp_path)
    # the solvers' C printf warnings may land after the JSON line
    return json.loads([l for l in res.stdout.splitlines() if l.startswith("{")][-1])


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("mode,TS", [("tp", [130.0, 150.0, 175.0, 200.0]),
                                     ("uv", [130.0, 150.0])])
def test_cold_start_converges_with_default_max_iter(tmp_path, device, mode, TS):
    ref = _run(tmp_path, device, mode, TS, 200)
    assert all(d >= 1 for d in ref["diag"]), ref["diag"]
    got = _run(tmp_path, device, mode, TS)
    failed = [T for T, d in zip(TS, got["diag"]) if d < 0]
    assert not failed, "%s: default max-iter %d fails at T0 = %s, diag %s" % (
        mode, got["default_max_iter"], failed, got["diag"])
    for xr, xg in zip(ref["x"], got["x"]):
        for a, b in zip(xr, xg):
            assert abs(a - b) <= 1e-6 * max(abs(a), 1e-12), (a, b)
