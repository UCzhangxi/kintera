"""Temperature derivative ``rc_ddT`` of the reverse rate constants.

``Kinetics.forward`` appends one reverse column per reversible reaction,
with ``k_r = k_f / K_c`` and ``K_c = exp(-sum(nu g/RT)) (Pref / (R T))^dn``
from the NASA-9 data. The reverse entries of ``rc_ddT`` used to be copies
of the forward ``dk_f/dT``; they must be

    dk_r/dT = (dk_f/dT) / K_c - k_r d ln K_c/dT,
    d ln K_c/dT = sum(nu h/RT) / T - dn / T.

The test compares every column of ``rc_ddT`` with a central finite
difference of the rate constant read back from the rates, below and above
the NASA-9 mid-point (1000 K), on CPU and CUDA.
"""

import pytest
import torch

import kintera as kt

torch.set_default_dtype(torch.float64)

CARD = """reference-state: {Tref: 300., Pref: 1.e5}
species:
  - {name: N2, composition: {N: 2}, cv_R: 2.5}
  - {name: O2, composition: {O: 2}, cv_R: 2.5}
  - {name: O, composition: {O: 1}, cv_R: 1.5}
  - {name: O3, composition: {O: 3}, cv_R: 3.0}
reactions:
  - equation: O + O2 <=> O3
    type: arrhenius
    rate-constant: {A: 1.7e-14, b: -2.4, Ea_R: 0.}
  - equation: O + O3 <=> 2 O2
    type: arrhenius
    rate-constant: {A: 8.0e-12, b: 0., Ea_R: 2060.}
"""
CONC = {"N2": 1.0, "O2": 0.2, "O": 1e-8, "O3": 1e-6}
# species whose concentration product turns a rate into its rate constant
REACTANTS = [{"O": 1, "O2": 1}, {"O": 1, "O3": 1}]
PRODUCTS = [{"O3": 1}, {"O2": 2}]


def _rate_constants(kin, names, temp, device):
    conc = torch.tensor([[CONC[n] for n in names]], device=device)
    pres = torch.tensor([1.0e5], device=device)
    rate, _, rc_ddT = kin.forward(torch.tensor([temp], device=device), pres,
                                  conc)
    k = []
    for side in (REACTANTS, PRODUCTS):
        for j, spec in enumerate(side):
            col = j if side is REACTANTS else len(REACTANTS) + j
            prod = 1.0
            for s, v in spec.items():
                prod *= CONC[s]**v
            k.append(rate[0, col].item() / prod)
    return torch.tensor(k), rc_ddT


@pytest.mark.parametrize("device", ["cpu", "cuda"])
@pytest.mark.parametrize("temp", [300.0, 1500.0])
def test_reverse_rc_ddT_matches_finite_difference(tmp_path, device, temp):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("no cuda")
    (card := tmp_path / "ozone.yaml").write_text(CARD)
    op = kt.KineticsOptions.from_yaml(str(card))
    op.evolve_temperature(True)
    kin = kt.Kinetics(op)
    kin.to(torch.device(device))
    names = op.species()

    _, rc_ddT = _rate_constants(kin, names, temp, device)
    assert rc_ddT is not None and rc_ddT.shape[-1] == 4

    h = temp * 1e-5
    kp, _ = _rate_constants(kin, names, temp + h, device)
    km, _ = _rate_constants(kin, names, temp - h, device)
    fd = (kp - km) / (2 * h)

    rel = (rc_ddT[0].cpu() / fd - 1).abs()
    assert rel.max().item() < 1e-6, (
        f"T={temp}: rc_ddT {rc_ddT[0].tolist()} vs FD {fd.tolist()}, "
        f"rel {rel.tolist()}")
