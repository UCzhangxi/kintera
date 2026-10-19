"""Runs quoted by chapter 9 (@sec-ch09): the two-dimensional solver of `python/atm2d`.

Uses the pure-Python package `python/atm2d` of a kintera checkout at
kintera@0d9f67f97d841147e23283d2dcdab302238d2c45, imported from source (the root of the checkout is the
environment variable KINTERA_REPO); only torch, numpy and scipy are needed, no compiled kintera. CPU, float64.

    KINTERA_REPO=/path/to/kintera python3 atm2d_run.py

[R1] Neumann boundary rows: the derivative a row imposes, bottom and top.
[R2] adaptive_advance: the largest accepted step after one rejection.
[R3] rosenbrock2_step on dc/dt = -k c: error at two step sizes and the observed order.
"""
import math
import os
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(os.environ["KINTERA_REPO"]) / "python"))
import atm2d  # noqa: E402
from atm2d.atm_state2d import SpeciesBoundaryCondition, SpeciesBoundaryConditions2D  # noqa: E402
from atm2d.sources import IndexedFirstOrderSource  # noqa: E402

torch.set_default_dtype(torch.float64)


def column(nlyr, conc):
    return atm2d.AtmState2D(
        x1f=torch.linspace(0.0, 1.0, nlyr + 1), x2f=torch.tensor([0.0, 1.0]),
        temperature=torch.full((1, nlyr), 300.0), pressure=torch.full((1, nlyr), 1.0e5),
        concentration=conc)


def r1_neumann():
    nlyr, g = 20, 0.5
    state = column(nlyr, torch.zeros(1, nlyr, 1))
    kzz = torch.ones(1, nlyr)
    h = float(state.dx1v[0])
    out = []
    for side in ("bottom", "top"):
        other = "top" if side == "bottom" else "bottom"
        bc = SpeciesBoundaryConditions2D(**{
            side: SpeciesBoundaryCondition("neumann", g),
            other: SpeciesBoundaryCondition("dirichlet", 1.0)})
        op = atm2d.build_eddy_diffusion_matrix(state, kzz, boundary_conditions=bc, form="c_diffusion")
        c = atm2d.solve_sparse_system(op, torch.zeros(1, nlyr, 1))[0, :, 0]
        if side == "bottom":
            dcdz = float((c[1] - c[0]) / h)
            outward = -dcdz
        else:
            dcdz = float((c[-1] - c[-2]) / h)
            outward = dcdz
        out.append((side, dcdz, outward))
        print(f"[R1] {side}: value {g}, imposed dc/dz = {dcdz:.6f}, outward normal derivative = {outward:.6f}")
    return out


def r2_ceiling():
    calls = {"n": 0}

    class S:
        concentration = torch.ones(1, 1, 1)

    def step(state, dt):
        calls["n"] += 1
        if calls["n"] == 1:            # reject only the very first attempt
            return torch.full_like(state.concentration, float("nan"))
        return state.concentration.clone()
    res = atm2d.adaptive_advance(S(), 8.0, step, initial_attempt=1.0, record_trace=True)
    dts = sorted({r.dt for r in res.records if r.action == "accept"})
    print(f"[R2] dt_target 8, initial_attempt 1, only the first attempt rejected: accepted {res.accepted_steps}, "
          f"rejected {res.rejected_steps}, distinct accepted dts {dts}, max accepted dt {res.max_accepted_dt:g}")
    return res


def r3_ros2_order():
    k, c0, t = 1.0, 1.0, 1.0
    errs = []
    for n in (8, 16, 32, 64):
        dt = t / n
        state = column(1, torch.full((1, 1, 1), c0))
        src = [IndexedFirstOrderSource(reactant=0, products=[], rate=k)]
        for _ in range(n):
            res = atm2d.rosenbrock2_step(state, dt, kzz=torch.zeros(1, 1), source_terms=src,
                                         transport_form="c_diffusion")
            state.concentration = res.concentration
        err = abs(float(state.concentration[0, 0, 0]) - c0 * math.exp(-k * t))
        errs.append((n, err))
    for (n1, e1), (n2, e2) in zip(errs, errs[1:]):
        print(f"[R3] steps {n1}->{n2}: error {e1:.3e} -> {e2:.3e}, observed order {math.log2(e1 / e2):.3f}")
    return errs


if __name__ == "__main__":
    print(f"torch {torch.__version__}; atm2d from $KINTERA_REPO/python at the pin")
    r1_neumann()
    r2_ceiling()
    r3_ros2_order()
