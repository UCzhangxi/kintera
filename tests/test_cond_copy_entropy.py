"""A condensate copy made by coagulation has the entropy of its source.

tests/jupiter.yaml has `H2O(l) => H2O(l,p)` and `NH3(s) => NH3(s,p)` coagulation.
The copies are in no nucleation reaction and have the same cv_R and u0_R as their
sources, so moving condensate from X to X(p) at fixed (T, P) must not change the
total entropy TPV->S.
"""

import subprocess
import sys

import pytest
import torch
import kintera

CASES = [
    ("H2O", "H2O(l)", "H2O(l,p)", 280.0, 5.0e5, 1.0e-3, 1.0e-3),
    ("H2O", "H2O(l)", "H2O(l,p)", 280.0, 5.0e5, 1.0e-3, 1.0e-4),
    ("NH3", "NH3(s)", "NH3(s,p)", 140.0, 0.5e5, 1.0e-5, 2.0e-4),
]

DEVICES = ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(
    not torch.cuda.is_available(), reason="needs CUDA"))]


@pytest.fixture(scope="module")
def thermo():
    op = kintera.ThermoOptions.from_yaml("tests/jupiter.yaml")
    names = kintera.species_names()
    sp = [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]
    return op, sp


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("vap,cloud,copy,T,P,xv,xc", CASES)
def test_copy_entropy_equals_source(thermo, device, vap, cloud, copy, T, P,
                                    xv, xc):
    op, sp = thermo
    th = kintera.ThermoX(op)
    th.to(torch.float64)
    th.to(torch.device(device))

    temp = torch.tensor([T], dtype=torch.float64, device=device)
    pres = torch.tensor([P], dtype=torch.float64, device=device)

    entropy = []
    for where in (cloud, copy):
        x = torch.zeros(1, len(sp), dtype=torch.float64, device=device)
        x[0, sp.index(vap)] = xv
        x[0, sp.index(where)] = xc
        x[0, 0] = 1.0 - xv - xc
        conc = th.compute("TPX->V", [temp, pres, x])
        entropy.append(th.compute("TPV->S", [temp, pres, conc]).item())

    assert entropy[1] == pytest.approx(entropy[0], rel=1e-12, abs=0.0)


UNEQUAL_CARD = """
reference-state: {Tref: 300., Pref: 1.e5}
species:
- name: dry
  composition: {H: 2}
  cv_R: 2.5
- name: H2O
  composition: {H: 2, O: 1}
  cv_R: 2.5
  u0_R: 0.
- name: H2O(l)
  composition: {H: 2, O: 1}
  cv_R: 9.0
  u0_R: -3430.
- name: H2O(l,p)
  composition: {H: 2, O: 1}
  cv_R: 8.0
  u0_R: -3500.
reactions:
- equation: H2O <=> H2O(l)
  type: nucleation
  rate-constant: {formula: h2o_ideal}
- equation: H2O(l) => H2O(l,p)
  type: coagulation
  rate-constant: {A: 0.001, b: 0, Ea_R: 1.}
"""

# entropy carried by 1 mol/m^3 of H2O(l,p): TPV->S with and without it
UNEQUAL_SCRIPT = """
import sys, torch, kintera
op = kintera.ThermoOptions.from_yaml(sys.argv[1])
th = kintera.ThermoX(op)
th.to(torch.float64)
th.to(torch.device(sys.argv[2]))
names = kintera.species_names()
sp = [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]
opt = dict(dtype=torch.float64, device=sys.argv[2])
temp = torch.tensor([280.0], **opt)
pres = torch.tensor([5.0e5], **opt)
conc = torch.zeros(1, len(sp), **opt)
conc[0, sp.index("dry")] = 200.0
conc[0, sp.index("H2O")] = 0.2
with_copy = conc.clone()
with_copy[0, sp.index("H2O(l,p)")] = 1.0
s0 = th.compute("TPV->S", [temp, pres, conc]).item()
s1 = th.compute("TPV->S", [temp, pres, with_copy]).item()
print(repr(s1 - s0))
"""


@pytest.mark.parametrize("device", DEVICES)
def test_unequal_copy_keeps_base_entropy(tmp_path, device):
    """A coagulation product whose cv_R/u0_R differ from its source is not a
    copy: it keeps the base entropy (s = 0 from the pseudo-inverse)."""
    card = tmp_path / "unequal_copy.yaml"
    card.write_text(UNEQUAL_CARD)
    # own interpreter: the species registry is process-global
    out = subprocess.run(
        [sys.executable, "-c", UNEQUAL_SCRIPT, str(card), device],
        capture_output=True, text=True, check=True).stdout
    assert float(out.strip().splitlines()[-1]) == 0.0
