"""A condensate copy made by coagulation has the entropy of its source.

tests/jupiter.yaml has `H2O(l) => H2O(l,p)` and `NH3(s) => NH3(s,p)` coagulation.
The copies are in no nucleation reaction and have the same cv_R and u0_R as their
sources, so moving condensate from X to X(p) at fixed (T, P) must not change the
total entropy TPV->S.
"""

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
