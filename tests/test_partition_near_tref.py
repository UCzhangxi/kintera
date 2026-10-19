"""uv-solver partition near Tref: the solve must not fail because the energy is ~0 there.

Energies are measured from Tref, so a cell whose temperature is within ~1 K of Tref has a
total internal energy U ~ 0. One vapour (H2O, 1 bar), x_v = 0.05 (supersaturated) and
1e-3 (subsaturated at Tref = 300 K), Tref = 300 and 250 K, start temperatures
Tref + {-1, -0.01, 0, +0.01, +1} K: forced `uv-solver: partition` must converge (diag >= 1)
to the state the KKT solver finds, and a vapour with cloud must sit on its saturation curve.
CPU and, if present, CUDA.

Each card runs in its own interpreter: kintera's species registry is global.
"""

import json
import math
import subprocess
import sys

import pytest
import torch

CARD = """
reference-state: {Tref: %s, Pref: 1.0e5}
species:
- {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {formula: h2o_ideal}}
dynamics: {equation-of-state: {uv-solver: %s, max-iter: 50}}
"""

PROBE = r"""
import json, sys, torch
torch.set_default_dtype(torch.float64)
from kintera import ThermoY, ThermoOptions
th = ThermoY(ThermoOptions.from_yaml(sys.argv[1]))
dev = torch.device(sys.argv[2])
th.to(dev)
TS = json.loads(sys.argv[3])
xv = float(sys.argv[4])
R = 8.314462618
mu = (1.0 / th.inv_mu).cpu()
x = torch.tensor([1 - xv, xv, 0.0])
y = (x * mu / (x * mu).sum())[1:].reshape(2, 1).expand(2, len(TS)).clone().to(dev)
rho = (1e5 * (x * mu).sum() / (R * torch.tensor(TS))).to(dev)
U = th.compute("VT->U", (th.compute("DY->V", (rho, y)), torch.tensor(TS, device=dev)))
d = torch.zeros(len(TS), 1, device=dev)
th.forward(rho, U, y, False, d)
V1 = th.compute("DY->V", (rho, y))
T1 = th.compute("VU->T", (V1, U))
c = V1.cpu() / mu
print(json.dumps({"diag": d[:, 0].tolist(), "T": T1.tolist(),
                  "p_vap": (c[:, 1] * R * T1.cpu()).tolist(),
                  "cond": (c[:, 2] / (c[:, 1] + c[:, 2])).tolist()}))
"""


def h2o_ideal(T):  # src/vapors/vapor_functions.h
    tr = 273.16
    t = T / tr
    beta, gamma = (24.845, 4.986009) if T > tr else (22.98, 0.52)
    return (1.0 - 1.0 / t) * beta - gamma * math.log(t) + math.log(611.7)


DEVICES = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])


def _run(tmp_path, tref, solver, device, TS, xv):
    card = tmp_path / ("tref%.0f_%s.yaml" % (tref, solver))
    card.write_text(CARD % (tref, solver))
    res = subprocess.run([sys.executable, "-c", PROBE, str(card), device, json.dumps(TS),
                          str(xv)],
                         capture_output=True, text=True, check=True, cwd=tmp_path)
    return json.loads(res.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("xv", [5e-2, 1e-3])
@pytest.mark.parametrize("tref", [300.0, 250.0])
def test_partition_converges_near_tref(tmp_path, tref, xv, device):
    TS = [tref + o for o in (-1.0, -0.01, 0.0, 0.01, 1.0)]
    kkt = _run(tmp_path, tref, "kkt", device, TS, xv)
    part = _run(tmp_path, tref, "partition", device, TS, xv)
    assert all(d >= 1 for d in kkt["diag"]), kkt["diag"]
    failed = [T0 for T0, d in zip(TS, part["diag"]) if d < 0]
    assert not failed, "partition failed at T0 = %s (Tref = %g)" % (failed, tref)
    for k, T0 in enumerate(TS):
        if part["cond"][k] > 0:
            r = math.log(part["p_vap"][k]) - h2o_ideal(part["T"][k])
            assert abs(r) < 1e-6, (T0, r)
        assert abs(part["T"][k] - kkt["T"][k]) < 1e-3, (T0, part["T"][k], kkt["T"][k])
        assert abs(part["cond"][k] - kkt["cond"][k]) <= 1e-5 * kkt["cond"][k], (
            T0, part["cond"][k], kkt["cond"][k])
