"""ThermoX.forward(warm_start=True) must give exactly the cold result.

The TP solver re-tests every reaction against the current composition in each
outer iteration and never reads the incoming active-set count, so the kept
(reaction_set, nactive) could not save iterations; it only reordered the
reactions and so changed round-off. After the warm start was removed, a warm
call after priming on a different state matches a cold call bit for bit.
"""

import os

import pytest
import torch
from kintera import ThermoOptions, ThermoX, species_names

torch.set_default_dtype(torch.float64)

CARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jupiter.yaml")
TEMPS = [130.0, 150.0, 175.0, 200.0, 250.0]


def _jupiter_x(op, n, device):
    names = species_names()
    sp = [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]
    x = torch.zeros(n, len(sp), device=device)
    x[:, sp.index("H2O")] = 2.5e-3
    x[:, sp.index("NH3")] = 3.0e-4
    x[:, sp.index("H2S")] = 8.0e-5
    x[:, 0] = 1.0 - x[:, 1:].sum(-1)
    return x


@pytest.mark.parametrize("device", ["cpu", "cuda"])
def test_warm_start_matches_cold(device):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("no cuda")
    op = ThermoOptions.from_yaml(CARD)
    op.max_iter(50)
    thermo = ThermoX(op)
    thermo.to(torch.device(device))

    temp = torch.tensor(TEMPS, device=device)
    pres = torch.full_like(temp, 1.0e5)
    x0 = _jupiter_x(op, len(TEMPS), device)

    out = {}
    for warm in (False, True):
        # prime on a state 20 K warmer, so a kept active set would differ
        thermo.forward(temp + 20.0, pres, x0.clone())
        x = x0.clone()
        diag = torch.zeros(len(TEMPS), 1, device=device)
        gain = thermo.forward(temp, pres, x, warm, diag)
        out[warm] = (x, diag, gain)

    for cold, warm in zip(out[False], out[True]):
        torch.testing.assert_close(warm, cold, rtol=0.0, atol=0.0)
    assert (out[False][1] > 0).all(), out[False][1].flatten()
