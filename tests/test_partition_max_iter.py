"""uv-solver partition: the temperature search must not be capped by `max-iter`.

One vapour (H2O, Tref = 0, 1 bar), forced `uv-solver: partition`, 15 cells over start
temperature and vapour amount. The bracketed Newton search needs at most 5 passes here, so
with `max-iter: 50` every cell converges; with `max-iter: 3` the same cells must converge
too (diag >= 1) and land on the same temperature, on CPU and, if present, CUDA.

Each card runs in its own interpreter: kintera's species registry is global.
"""

import json
import subprocess
import sys

import pytest
import torch

CARD = """
reference-state: {Tref: 0., Pref: 1.0e5}
species:
- {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {formula: h2o_ideal}}
dynamics: {equation-of-state: {uv-solver: partition, max-iter: %d}}
"""

PROBE = r"""
import json, sys, torch
torch.set_default_dtype(torch.float64)
from kintera import ThermoY, ThermoOptions
th = ThermoY(ThermoOptions.from_yaml(sys.argv[1]))
dev = torch.device(sys.argv[2])
th.to(dev)
R = 8.314462618
mu = (1.0 / th.inv_mu).cpu()
cells = [(t, xv) for xv in (1e-3, 1e-2, 5e-2) for t in (200., 250., 280., 300., 320.)]
x = torch.tensor([[1 - xv, xv, 0.0] for _, xv in cells])
T0 = torch.tensor([t for t, _ in cells])
y = (x * mu / (x * mu).sum(-1, keepdim=True))[:, 1:].T.contiguous().to(dev)
rho = (1e5 * (x * mu).sum(-1) / (R * T0)).to(dev)
U = th.compute("VT->U", (th.compute("DY->V", (rho, y)), T0.to(dev)))
d = torch.zeros(len(cells), 1, device=dev)
th.forward(rho, U, y, False, d)
T1 = th.compute("VU->T", (th.compute("DY->V", (rho, y)), U))
print(json.dumps({"diag": d[:, 0].tolist(), "T": T1.tolist()}))
"""

DEVICES = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])


def _run(tmp_path, max_iter, device):
    card = tmp_path / ("partition_mi%d.yaml" % max_iter)
    card.write_text(CARD % max_iter)
    res = subprocess.run([sys.executable, "-c", PROBE, str(card), device],
                         capture_output=True, text=True, check=True, cwd=tmp_path)
    return json.loads(res.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("device", DEVICES)
def test_partition_converges_with_small_max_iter(tmp_path, device):
    ref = _run(tmp_path, 50, device)
    assert all(d >= 1 for d in ref["diag"]), ref["diag"]
    got = _run(tmp_path, 3, device)
    failed = sum(d < 0 for d in got["diag"])
    assert failed == 0, "max-iter 3: %d of %d cells failed, diag %s" % (
        failed, len(got["diag"]), got["diag"])
    for t, t_ref in zip(got["T"], ref["T"]):
        assert abs(t - t_ref) <= 1e-9 * t_ref, (t, t_ref)
