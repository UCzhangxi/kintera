"""atm2d project_atomic_budget: the budget is met whatever the size of the hog total.

The excess is split over the hog species in proportion to their atoms, hog_atoms / hog_total.
The projection must meet the budget when the hogs hold less than one unit of the element in
total, and scaling all amounts and the budget by s must scale the result by s. CPU and, if
present, CUDA.
"""

import pytest
import torch
from kintera.atm2d.conservation import project_atomic_budget

DEVICES = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])

# element C in species [A (C1), B (C2), N2 fixed]
COUNTS = [1.0, 2.0, 0.0]
FIXED = [False, False, True]


def _project(c, budget, device):
    d = torch.device(device)
    return project_atomic_budget(
        c.to(d, torch.float64),
        atom_counts={"C": torch.tensor(COUNTS, dtype=torch.float64, device=d)},
        fixed_mask=torch.tensor(FIXED, device=d),
        budget={"C": budget.to(d, torch.float64)},
    ).cpu()


def _total(c):
    return (c * torch.tensor(COUNTS, dtype=torch.float64)).sum(-1)


@pytest.mark.parametrize("device", DEVICES)
def test_budget_met_with_hog_total_below_one(device):
    # A holds 0.5 C (the hog), B 0.01 C: total 0.51 > budget 0.3
    c = torch.tensor([[[0.5, 0.005, 1.0]]], dtype=torch.float64)
    out = _project(c, torch.tensor([[[0.3]]], dtype=torch.float64), device)
    assert abs(_total(out).item() - 0.3) < 1e-15, _total(out).item()
    assert torch.all(out >= 0.0)
    assert out[0, 0, 1].item() == 0.005  # B is below the mean: untouched
    assert out[0, 0, 2].item() == 1.0  # fixed species untouched


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("scale", [1e-12, 1e-3, 1.0, 1e12])
def test_projection_scales_with_units(device, scale):
    gen = torch.Generator().manual_seed(9)
    c = torch.stack([5.0 * (1 + torch.rand(2, 4, generator=gen, dtype=torch.float64)),
                     0.1 * (1 + torch.rand(2, 4, generator=gen, dtype=torch.float64)),
                     torch.full((2, 4), 100.0, dtype=torch.float64)], -1)
    budget = 0.8 * _total(c).unsqueeze(-1)
    out = _project(c * scale, budget * scale, device)
    assert torch.allclose(_total(out) / (budget[..., 0] * scale),
                          torch.ones_like(budget[..., 0]), rtol=1e-13, atol=0.0)
    assert torch.allclose(out / scale, _project(c, budget, device), rtol=1e-13, atol=0.0)
    assert torch.all(out >= 0.0)


@pytest.mark.parametrize("device", DEVICES)
def test_no_hog_cell_stays_finite(device):
    # equal contributions: no species is above the mean, so nothing is trimmed
    c = torch.tensor([[[0.2, 0.1, 1.0]]], dtype=torch.float64)
    out = _project(c, torch.tensor([[[0.1]]], dtype=torch.float64), device)
    assert torch.all(torch.isfinite(out))
    assert torch.equal(out, c)
