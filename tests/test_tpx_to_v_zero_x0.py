"""ThermoX "TPX->V" must give finite cloud concentrations when x_0 = 0.

The cloud concentrations scale the gas concentration by the cloud-to-gas mole
ratio. Dividing by the mole fraction of species 0 alone gave inf (or nan) for a
state without species 0, e.g. a pure vapour with its condensate.
"""

import pytest
import torch
from kintera import ThermoOptions, ThermoX

torch.set_default_dtype(torch.float64)

CARD = """reference-state: {Tref: 300., Pref: 1.e5}
species:
- {name: dry, composition: {N: 1.56, O: 0.42}, cv_R: 2.5}
- {name: A, composition: {H: 2, O: 1}, cv_R: 1.5, u0_R: 0.}
- {name: A(l), composition: {H: 2, O: 1}, cv_R: 7.5, u0_R: -6786.66}
reactions:
- {equation: 'A <=> A(l)', type: nucleation, rate-constant: {formula: antoine, A: 1.5, B: 900., C: 0.}}
"""


@pytest.mark.parametrize("device", ["cpu", "cuda"])
@pytest.mark.parametrize("x0", [0.5, 1.0e-12, 0.0])
def test_cloud_concentration_without_species_0(tmp_path, device, x0):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("no cuda")
    (card := tmp_path / "one_cloud.yaml").write_text(CARD)
    thermo = ThermoX(ThermoOptions.from_yaml(str(card)))
    thermo.to(torch.device(device))

    temp = torch.tensor([300.0], device=device)
    pres = torch.tensor([1.0e5], device=device)
    xfrac = torch.tensor([[x0, 0.9 - x0, 0.1]], device=device)
    conc = thermo.compute("TPX->V", [temp, pres, xfrac])

    conc_gas = conc[0, :2].sum()
    torch.testing.assert_close(conc_gas, pres[0] / (8.31446 * temp[0]),
                               rtol=1e-12, atol=0.)
    torch.testing.assert_close(conc[0, 2], conc_gas * 0.1 / 0.9,
                               rtol=1e-12, atol=0.)
