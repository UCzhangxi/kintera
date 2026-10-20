"""An Arrhenius reaction without ``Ea_R`` in its YAML gets Ea_R = 0.

The default used to be 1 K, so ``{A: ..., b: 0}`` was multiplied by
exp(-1/T): 0.980 at 50 K, 0.997 at 300 K. Three-body and fall-off rates
already default to 0; this makes the plain Arrhenius form match.
"""

import pytest
import torch

import kintera as kt

torch.set_default_dtype(torch.float64)

CARD = """reference-state: {Tref: 300., Pref: 1.e5}
species:
  - {name: O, composition: {O: 1}, cv_R: 2.5}
  - {name: H, composition: {H: 1}, cv_R: 2.5}
  - {name: OH, composition: {O: 1, H: 1}, cv_R: 2.5}
reactions:
  - equation: OH => O + H
    type: arrhenius
    rate-constant: %s
"""


def _rate_constant(tmp_path, rate_constant, temp, device):
    (card := tmp_path / "card.yaml").write_text(CARD % rate_constant)
    op = kt.KineticsOptions.from_yaml(str(card))
    kin = kt.Kinetics(op)
    kin.to(torch.device(device))
    conc = torch.full((1, 3), 1e-3, device=device)
    k = kin.forward_with_rate_constants(
        torch.tensor([temp], device=device), torch.tensor([1e5], device=device),
        conc)[3]
    return list(op.arrhenius().Ea_R())[0], k.reshape(-1)[0].item()


@pytest.mark.parametrize("device", ["cpu", "cuda"])
@pytest.mark.parametrize("temp", [50.0, 300.0])
def test_omitted_ea_r_is_zero(tmp_path, device, temp):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("no cuda")
    ea_omit, k_omit = _rate_constant(tmp_path, "{A: 3.0e-3, b: 0.}", temp,
                                     device)
    ea_zero, k_zero = _rate_constant(tmp_path, "{A: 3.0e-3, b: 0., Ea_R: 0.}",
                                     temp, device)
    assert ea_zero == 0.0
    assert ea_omit == 0.0, f"omitted Ea_R stored as {ea_omit} K"
    assert k_omit == k_zero, f"T={temp}: k/k(Ea_R: 0) = {k_omit / k_zero}"
