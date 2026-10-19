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


@pytest.mark.parametrize("device", DEVICES)
def test_pxs_to_t_batched(thermo, device):
    """One batched call: columns that converge early must stay finite while
    the others keep iterating."""
    op, op_ref, sp = thermo
    th = _thermo_x(op, device)
    th_ref = _thermo_x(op_ref, device)

    grid = [(h, float(t)) for h in (0.0, 2.5e-3, 1.0e-2, 5.0e-2)
            for t in range(130, 410, 10)]
    n = len(grid)
    x = torch.zeros(n, len(sp), dtype=torch.float64, device=device)
    for i, (h, _) in enumerate(grid):
        if h > 0.0:
            x[i, sp.index("H2O")] = h
            x[i, sp.index("NH3")] = 3.0e-4
            x[i, sp.index("H2S")] = 8.0e-5
    x[:, 0] = 1.0 - x[:, 1:].sum(-1)

    tstar = torch.tensor([t for _, t in grid], dtype=torch.float64,
                         device=device)
    pres = torch.full((n,), P, dtype=torch.float64, device=device)
    xeq = x.clone()
    th_ref.forward(tstar, pres, xeq)
    conc = th_ref.compute("TPX->V", [tstar, pres, xeq])
    entropy = th_ref.compute("TPV->S", [tstar, pres, conc])

    T = th.compute("PXS->T", [pres, x.clone(), entropy])
    relerr = ((T - tstar) / tstar).abs()
    bad = [(grid[i], T[i].item()) for i in range(n)
           if not relerr[i].item() < 1e-5]
    assert bad == []


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("batched", [False, True], ids=["single", "batched"])
def test_pxs_to_t_nan_entropy_is_reported(thermo, device, batched, tmp_path,
                                          monkeypatch, capfd):
    """A NaN entropy never converges: the call must reach max-iter, warn and
    write its diagnostic dump, as base does, also inside a batch."""
    op, op_ref, sp = thermo
    th = _thermo_x(op, device)
    monkeypatch.chdir(tmp_path)

    n = 3 if batched else 1
    x = torch.zeros(n, len(sp), dtype=torch.float64, device=device)
    x[:, 0] = 1.0
    pres = torch.full((n,), P, dtype=torch.float64, device=device)
    tstar = torch.full((n,), 300.0, dtype=torch.float64, device=device)
    conc = th.compute("TPX->V", [tstar, pres, x])
    entropy = th.compute("TPV->S", [tstar, pres, conc])
    entropy[0] = float("nan")

    T = th.compute("PXS->T", [pres, x.clone(), entropy])

    err = capfd.readouterr().err
    assert "_entropy_to_temp: max iteration reached" in err
    assert list(tmp_path.glob("thermo_x_entropy_to_temp_*.pt"))
    assert T[0].isnan().item()
    if batched:
        assert torch.allclose(T[1:], tstar[1:], rtol=1e-5)
