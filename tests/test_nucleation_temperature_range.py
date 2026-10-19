"""A nucleation minT/maxT range that no solver applies must be refused.

minT/maxT are parsed and printed, but no solver reads them: a reaction whose
range excludes the state condensed exactly as one without a range. A range
other than the defaults (minT 0, maxT 1e4 K) is now refused when the options
are read from YAML and when ThermoX/ThermoY are built; the defaults are still
accepted. Each case runs in a fresh subprocess.
"""

import os
import subprocess
import sys

import pytest

CARD = """reference-state: {Tref: 300., Pref: 1.e5}
species:
- {name: dry, composition: {N: 1.56, O: 0.42}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 3.0, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -6786.66}
reactions:
- {equation: 'H2O <=> H2O(l)', type: nucleation, rate-constant: {formula: h2o_ideal%s}}
"""

YAML_SCRIPT = """
import sys, torch
from kintera import ThermoOptions, ThermoX
torch.set_default_dtype(torch.float64)
op = ThermoOptions.from_yaml(sys.argv[1])
x = torch.tensor([[0.9, 0.1, 0.0]])
ThermoX(op).forward(torch.tensor([300.0]), torch.tensor([1e5]), x)
print("condensed at 300 K:", x[0, 2].item(), flush=True)
"""

PYTHON_SCRIPT = """
import sys, torch, kintera
from kintera import NucleationOptions, Reaction, ThermoOptions, ThermoX, ThermoY
torch.set_default_dtype(torch.float64)
kind, minT, maxT = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
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
              .logsvp(["h2o_ideal"]).minT([minT]).maxT([maxT]))
(ThermoX if kind == "X" else ThermoY)(op)
print("Thermo built", flush=True)
"""


def _run(*args):
    return subprocess.run([sys.executable, "-c", *args], capture_output=True,
                          text=True, env=os.environ.copy())


def _refused(out):
    assert out.returncode == 1 and "Traceback" in out.stderr, (
        f"range accepted (returncode {out.returncode})\nstdout:\n{out.stdout}"
        f"\nstderr:\n{out.stderr[-2000:]}")
    assert "minT/maxT" in out.stderr, out.stderr[-2000:]


@pytest.mark.parametrize("keys", [", minT: 350.", ", maxT: 250."])
def test_yaml_range_excluding_the_state_is_refused(tmp_path, keys):
    (card := tmp_path / "card.yaml").write_text(CARD % keys)
    _refused(_run(YAML_SCRIPT, str(card)))


@pytest.mark.parametrize("keys", ["", ", minT: 0., maxT: 1.e4"])
def test_yaml_default_range_is_accepted(tmp_path, keys):
    (card := tmp_path / "card.yaml").write_text(CARD % keys)
    out = _run(YAML_SCRIPT, str(card))
    assert out.returncode == 0, out.stderr[-2000:]
    assert float(out.stdout.split()[-1]) > 0.


@pytest.mark.parametrize("kind", ["X", "Y"])
def test_python_built_range(kind):
    _refused(_run(PYTHON_SCRIPT, kind, "350.", "1.e4"))
    out = _run(PYTHON_SCRIPT, kind, "0.", "1.e4")
    assert out.returncode == 0, out.stderr[-2000:]
