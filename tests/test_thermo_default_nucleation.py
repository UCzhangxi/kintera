"""ThermoX/ThermoY built from a default ThermoOptions() must not crash.

The construction follows examples/example_earth_dry.py: a Python ThermoOptions()
with no .nucleation(...), then ThermoX(op) or ThermoY(op). Each construction runs
in a fresh subprocess, because a segfault would kill pytest.

The same Python-built options with one nucleation reaction, H2O => H2O(l) with
the registered h2o_ideal, must condense a supersaturated cell to saturation:
ThermoX at fixed T, P and ThermoY at fixed density and internal energy.
"""

import math
import os
import subprocess
import sys

import pytest
import torch

SCRIPT = """
import sys, torch, kintera
from kintera import ThermoOptions, ThermoX, ThermoY
torch.set_default_dtype(torch.float64)
kind, device = sys.argv[1], sys.argv[2]
kintera.set_species_names(["dry"])
kintera.set_species_weights([29.e-3])
op = ThermoOptions()
op.vapor_ids([0])
op.cref_R([2.5])
op.uref_R([0.0])
op.sref_R([0.0])
op.Tref(300.0)
op.Pref(1.e5)
th = (ThermoX if kind == "X" else ThermoY)(op)
th.to(torch.device(device))
mu = th.mu[0] if kind == "X" else 1. / th.inv_mu[0]
print(mu.device.type, repr(mu.item()))
"""


def _default_options(kind, device):
    out = subprocess.run([sys.executable, "-c", SCRIPT, kind, device],
                         capture_output=True, text=True, env=os.environ.copy())
    assert out.returncode == 0, (
        f"Thermo{kind}(ThermoOptions()) on {device}: returncode "
        f"{out.returncode} (-11 = SIGSEGV)\nstderr:\n{out.stderr}")
    dev, mu = out.stdout.strip().splitlines()[-1].split()
    assert dev == torch.device(device).type
    torch.testing.assert_close(torch.tensor(float(mu)), torch.tensor(29.e-3),
                               rtol=1e-12, atol=0.)


def test_thermo_x_default_options():
    _default_options("X", "cpu")


def test_thermo_y_default_options():
    _default_options("Y", "cpu")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA")
def test_thermo_x_default_options_cuda():
    _default_options("X", "cuda:0")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA")
def test_thermo_y_default_options_cuda():
    _default_options("Y", "cuda:0")


NUCLEATION_SCRIPT = """
import sys, torch, kintera
from kintera import NucleationOptions, Reaction, ThermoOptions, ThermoX, ThermoY
torch.set_default_dtype(torch.float64)
kind, device = sys.argv[1], torch.device(sys.argv[2])
kintera.set_species_names(["dry", "H2O", "H2O(l)"])
kintera.set_species_weights([29.e-3, 18.e-3, 18.e-3])
op = ThermoOptions()
op.vapor_ids([0, 1])
op.cloud_ids([2])
op.cref_R([2.5, 3.0, 9.0])
op.uref_R([0.0, 0.0, -6786.66])
op.sref_R([0.0, 0.0, 0.0])
op.Tref(300.0)
op.Pref(1.e5)
op.nucleation(NucleationOptions().reactions([Reaction("H2O => H2O(l)")])
              .logsvp(["h2o_ideal"]))
th = (ThermoX if kind == "X" else ThermoY)(op)
th.to(device)
diag = torch.zeros((1, 1), device=device)
if kind == "X":
    temp = torch.tensor([300.], device=device)
    xfrac = torch.tensor([[0.9, 0.1, 0.]], device=device)
    th.forward(temp, torch.tensor([1.e5], device=device), xfrac, diag=diag)
    vapor, cloud = xfrac[0, 1].item(), xfrac[0, 2].item()
    pvap = vapor / xfrac[0, :2].sum().item() * 1.e5
else:
    rho = torch.tensor([1.], device=device)
    yfrac = torch.tensor([[0.05], [0.]], device=device)
    ivol = th.compute("DY->V", [rho, yfrac])
    intEng = th.compute("VT->U", [ivol, torch.tensor([300.], device=device)])
    th.forward(rho, intEng, yfrac, False, diag)
    ivol = th.compute("DY->V", [rho, yfrac])
    temp = th.compute("VU->T", [ivol, intEng])
    vapor, cloud = yfrac[0, 0].item(), yfrac[1, 0].item()
    pvap = (ivol[0, 1] / 18.e-3).item() * 8.31446 * temp.item()
print(device.type, repr(temp.item()), repr(vapor), repr(cloud), repr(pvap),
      repr(diag.item()))
"""


def _log_svp_h2o_ideal(temp):
    # src/vapors/vapor_functions.h: h2o_ideal above the triple point
    t = temp / 273.16
    return (1. - 1. / t) * 24.845 - 4.986009 * math.log(t) + math.log(611.7)


def _nucleation(kind, device):
    out = subprocess.run(
        [sys.executable, "-c", NUCLEATION_SCRIPT, kind, device],
        capture_output=True, text=True, env=os.environ.copy())
    assert out.returncode == 0, (
        f"Thermo{kind} with a nucleation reaction on {device}: returncode "
        f"{out.returncode} (-11 = SIGSEGV)\nstderr:\n{out.stderr}")
    dev, *values = out.stdout.strip().splitlines()[-1].split()
    temp, vapor, cloud, pvap, diag = map(float, values)
    assert dev == torch.device(device).type
    assert diag > 0, f"solver reported failure, diag = {diag}"
    total = 0.1 if kind == "X" else 0.05
    assert 0. < cloud < total, f"cloud {cloud} of {total}"
    assert abs(vapor + cloud - total) <= 1e-12 * total
    if kind == "Y":
        assert temp > 300., f"latent heat must warm the cell, T = {temp}"
    assert abs(math.log(pvap) - _log_svp_h2o_ideal(temp)) < 1e-6, (
        f"not at saturation: T {temp} p_H2O {pvap}")


def test_thermo_x_nucleation():
    _nucleation("X", "cpu")


def test_thermo_y_nucleation():
    _nucleation("Y", "cpu")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA")
def test_thermo_x_nucleation_cuda():
    _nucleation("X", "cuda:0")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA")
def test_thermo_y_nucleation_cuda():
    _nucleation("Y", "cuda:0")
