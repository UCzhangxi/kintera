"""ThermoX "PXS->T" returns the temperature whose entropy was given.

The input entropy is volumetric ("TPV->S"). At fixed p and x the
concentrations scale as 1/T, so dS_vol/dT = (cp_vol - S_vol) / T, and the
Newton step must use that slope. Oracle: build a state at a known T*, take
its entropy and invert it with the default max-iter.
"""

import pytest
import torch
import kintera

P = 1.0e5

DEVICES = ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(
    not torch.cuda.is_available(), reason="needs CUDA"))]

# (H2O, NH3, H2S) mole fractions, T*: a dry parcel, the jupiter default and
# an H2O-rich parcel where latent heat dominates the slope (cp_eff/cp ~ 3)
CASES = [
    ((0.0, 0.0, 0.0), 150.0),
    ((0.0, 0.0, 0.0), 600.0),
    ((2.5e-3, 3.0e-4, 8.0e-5), 150.0),
    ((2.5e-3, 3.0e-4, 8.0e-5), 200.0),
    ((5.0e-2, 3.0e-4, 8.0e-5), 300.0),
]


@pytest.fixture(scope="module")
def thermo():
    op = kintera.ThermoOptions.from_yaml("tests/jupiter.yaml")
    names = kintera.species_names()
    sp = [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]
    # the oracle state needs a converged TP equilibrium at cold T*
    op_ref = kintera.ThermoOptions.from_yaml("tests/jupiter.yaml")
    op_ref.max_iter(200)
    return op, op_ref, sp


def _thermo_x(op, device):
    th = kintera.ThermoX(op)
    th.to(torch.float64)
    th.to(torch.device(device))
    return th


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("vapors,Tstar", CASES)
def test_pxs_to_t_inverts_entropy(thermo, device, vapors, Tstar):
    op, op_ref, sp = thermo
    th = _thermo_x(op, device)
    th_ref = _thermo_x(op_ref, device)

    x = torch.zeros(1, len(sp), dtype=torch.float64, device=device)
    for name, xv in zip(("H2O", "NH3", "H2S"), vapors):
        x[0, sp.index(name)] = xv
    x[0, 0] = 1.0 - x[0, 1:].sum()

    temp = torch.tensor([Tstar], dtype=torch.float64, device=device)
    pres = torch.tensor([P], dtype=torch.float64, device=device)
    xeq = x.clone()
    th_ref.forward(temp, pres, xeq)
    conc = th_ref.compute("TPX->V", [temp, pres, xeq])
    entropy = th_ref.compute("TPV->S", [temp, pres, conc])

    T = th.compute("PXS->T", [pres, x.clone(), entropy])
    assert T.item() == pytest.approx(Tstar, rel=1e-5)
