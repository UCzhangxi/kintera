"""Worked example of a validation tolerance (@sec-ch13-suite): the case `IdealGasReaction` of
`tests/test_equilibrium.cpp`, rebuilt in Python (A <=> B, one gas phase, ln K = 0, ftol 1e-7, mole floor 1e-20,
start 0.8/0.2 at 1000 and 1500 K and 1e5 Pa), in single and double precision.

It prints the largest |x_A - 0.5|, the largest |x_A + x_B - 1| and the reported equilibrium error, next to the bound
derived in the chapter and the bound the test allows.

    python -P tolerance_example.py
"""
import math

import torch
import kintera as kt

for dtype in (torch.float32, torch.float64):
    op = (kt.EquilibriumOptions().components(["A", "B"]).phases(["gas"]).phase_ids([0, 0]).reactions(["A <=> B"])
          .gas_phase(0).standard_pressure(1e5).max_iter(50).ftol(1e-7).mole_floor(1e-20))
    eq = kt.EquilibriumTP(op)
    t = torch.tensor([1000.0, 1500.0], dtype=dtype)
    moles, _, diag = eq(t, torch.tensor(1e5, dtype=dtype), torch.tensor([[0.8, 0.2]], dtype=dtype),
                        torch.zeros(2, 1, dtype=dtype))
    eps = torch.finfo(dtype).eps
    target = max(math.log1p(1e-7), 4 * eps)
    derived = target / 4 + 0.5 * eps
    print(f"{str(dtype).split('.')[-1]}: status {diag[:, 0].tolist()}, max |x_A - 0.5| "
          f"{float((moles[..., 0] - 0.5).abs().max()):.2e}, max |x_A + x_B - 1| {float((moles.sum(-1) - 1).abs().max()):.2e}, "
          f"reported error max {float(diag[:, 2].max()):.2e}; derived bound {derived:.2e}; test allows "
          f"{1e-6 + 1e-5 * 0.5:.1e} (atol 1e-6 + rtol 1e-5 x 0.5)")
