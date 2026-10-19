"""tests/jupiter.yaml condensate cards match their saturation curves.

For `vapour -> condensate` with an ideal saturation formula,
ln p_sat = ln p3 + beta (1 - T3/T) - gamma ln(T/T3), Clausius-Clapeyron gives
the latent heat l_svp = R (beta T3 - gamma T). The card latent heat
l_card = h_vapour - h_condensate (from TV->H) must equal it on the branch of
the formula the card is meant for: liquid water above T3 = 273.16 K, solid
ammonia below T3 = 195.4 K.
"""

import pytest
import torch
import kintera

R = 8.31446  # src/constants.h

# (vapour, condensate, beta, gamma, T3, temperatures) from
# src/vapors/vapor_functions.h, h2o_ideal liquid and nh3_ideal solid branch
CASES = [
    ("H2O", "H2O(l)", 24.845, 4.986009, 273.16, (280.0, 300.0, 350.0)),
    ("H2O", "H2O(l,p)", 24.845, 4.986009, 273.16, (280.0, 300.0, 350.0)),
    ("NH3", "NH3(s)", 20.64, 1.43, 195.4, (130.0, 160.0, 190.0)),
    ("NH3", "NH3(s,p)", 20.64, 1.43, 195.4, (130.0, 160.0, 190.0)),
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
@pytest.mark.parametrize("vap,cond,beta,gamma,T3,temps", CASES,
                         ids=[c[1] for c in CASES])
def test_card_latent_heat_matches_svp(thermo, device, vap, cond, beta, gamma,
                                      T3, temps):
    op, sp = thermo
    th = kintera.ThermoX(op)
    th.to(torch.float64)
    th.to(torch.device(device))

    conc = torch.ones(1, len(sp), dtype=torch.float64, device=device)
    dn = torch.zeros_like(conc)
    dn[0, sp.index(vap)] = -1.0e-3
    dn[0, sp.index(cond)] = 1.0e-3
    for T in temps:
        temp = torch.tensor([T], dtype=torch.float64, device=device)
        dH = (th.compute("TV->H", [temp, conc + dn]) -
              th.compute("TV->H", [temp, conc - dn])) / 2.0e-3
        l_card = -dH.item()
        l_svp = R * (beta * T3 - gamma * T)
        assert l_card / l_svp == pytest.approx(1.0, abs=1e-10), (T, l_card,
                                                                 l_svp)
