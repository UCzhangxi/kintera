"""A misspelled named svp formula must be refused before the first forward.

Before, a typo such as 'h2o_idael' was accepted by ThermoOptions.from_yaml and
ThermoX/ThermoY construction; the "Function ... not registered." error came
only from the first forward call. Each case runs in a fresh subprocess, so a
failed YAML load cannot leave species state behind for the next one.
"""

import os
import subprocess
import sys

import pytest

CARD = """reference-state: {Tref: 0., Pref: 1.e5}
species:
- {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {formula: %s}}
"""

YAML_SCRIPT = """
import sys, torch
from kintera import ThermoOptions, ThermoX
torch.set_default_dtype(torch.float64)
op = ThermoOptions.from_yaml(sys.argv[1])
print("options built", flush=True)
th = ThermoX(op)
print("ThermoX built", flush=True)
x = torch.tensor([[0.95, 0.05, 0.0]])
th.forward(torch.tensor([300.0]), torch.tensor([1e5]), x)
print("forward returned", flush=True)
"""

PYTHON_SCRIPT = """
import sys, torch, kintera
from kintera import NucleationOptions, Reaction, ThermoOptions, ThermoX, ThermoY
torch.set_default_dtype(torch.float64)
formula, kind = sys.argv[1], sys.argv[2]
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
              .logsvp([formula]))
th = (ThermoX if kind == "X" else ThermoY)(op)
print("Thermo built", flush=True)
"""


def _run(*args):
    return subprocess.run([sys.executable, "-c", *args], capture_output=True,
                          text=True, env=os.environ.copy())


@pytest.mark.parametrize("formula", ["h2o_ideal", "h2o_idael"])
def test_yaml_formula(tmp_path, formula):
    (card := tmp_path / "card.yaml").write_text(CARD % formula)
    out = _run(YAML_SCRIPT, str(card))
    if formula == "h2o_ideal":
        assert out.returncode == 0, out.stderr
        assert "forward returned" in out.stdout
        return
    assert out.returncode == 1 and "Traceback" in out.stderr, (
        f"returncode {out.returncode}\nstdout:\n{out.stdout}\n"
        f"stderr:\n{out.stderr}")
    assert "Function h2o_idael not registered." in out.stderr
    assert "options built" not in out.stdout, out.stdout


@pytest.mark.parametrize("kind", ["X", "Y"])
@pytest.mark.parametrize("formula", ["h2o_ideal", "h2o_idael"])
def test_python_built_formula(formula, kind):
    out = _run(PYTHON_SCRIPT, formula, kind)
    if formula == "h2o_ideal":
        assert out.returncode == 0, out.stderr
        return
    assert out.returncode == 1 and "Traceback" in out.stderr, (
        f"returncode {out.returncode}\nstdout:\n{out.stdout}\n"
        f"stderr:\n{out.stderr}")
    assert "Function h2o_idael not registered." in out.stderr
    assert "Thermo built" not in out.stdout, out.stdout
