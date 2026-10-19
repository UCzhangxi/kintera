"""Runs quoted by chapter 9 (@sec-ch09): the two-dimensional solver of `python/atm2d`.

Uses the pure-Python package `python/atm2d` of a kintera checkout at
kintera@0d9f67f97d841147e23283d2dcdab302238d2c45, imported from source (the root of the checkout is the
environment variable KINTERA_REPO); only torch, numpy and scipy are needed, no compiled kintera. CPU, float64.

    KINTERA_REPO=/path/to/kintera python3 atm2d_run.py

[R1] Neumann boundary rows: the derivative a row imposes, bottom and top.
[R2] adaptive_advance: the largest accepted step after one rejection.
[R3] rosenbrock2_step on dc/dt = -k c: error at two step sizes and the observed order.
[R4] pydisort layer order as compute_actinic_flux_disort calls it (needs pydisort; skipped if absent).
[R5] project_atomic_budget: atoms left above the budget when the hog atoms total less than 1.
[R6] operator_split_step: whether the caller's state.concentration is changed on return.
[R7] pins as Dirichlet rows: the pinned value after a backward-Euler solve.
[R8] molecular diffusion, one species in an isothermal column (CGS): the transport tendency of the
     hydrostatic profile c = exp(-z/H) in the c_diffusion, mr_diffusion and mr_exp forms.
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


def r4_disort_order():
    try:
        import pydisort
    except ImportError:
        print("[R4] SKIPPED: pydisort not installed")
        return None
    nlyr = 4
    op = pydisort.DisortOptions().flags("onlyfl,lamber")     # the options compute_actinic_flux_disort sets
    op.ds().nlyr = nlyr
    op.ds().nstr = 4
    op.ds().nmom = 4
    op.ds().nphase = 1
    op.nwave(1).ncol(1)
    ds = pydisort.Disort(op)
    prop = torch.zeros((1, 1, nlyr, 2))
    prop[..., 0, 0] = 5.0                  # all optical depth in index 0, atm2d's bottom cell (x1 increasing)
    ds.forward(prop, umu0=torch.ones(1), phi0=torch.zeros(1), fbeam=torch.ones(1, 1), albedo=torch.zeros(1, 1))
    u = ds.gather_flx()[..., pydisort.kIUAVG].flatten().tolist()
    print(f"[R4] pydisort {pydisort.__version__}: optical depth 5 in index 0 only; mean intensity at levels 0..{nlyr}: "
          + ", ".join(f"{v:.3e}" for v in u))
    return u


def r5_budget_floor():
    from atm2d.conservation.atomic import project_atomic_budget
    c = torch.tensor([[[0.30, 0.05, 0.05]]])          # three species, one cell, all with one atom of X
    counts = {"X": torch.tensor([1.0, 1.0, 1.0])}
    budget = {"X": torch.tensor([[[0.20]]])}
    out = project_atomic_budget(c, atom_counts=counts, fixed_mask=torch.zeros(3, dtype=torch.bool), budget=budget)
    print(f"[R5] atoms before {float(c.sum()):.3f}, budget 0.200, after {float(out.sum()):.3f} "
          f"(hog atoms 0.300 < 1, so the trim is scaled by 0.300)")
    return out


def r6_split_state():
    state = column(3, torch.tensor([[[1.0], [0.0], [0.0]]]))
    entry = state.concentration.clone()
    src = [IndexedFirstOrderSource(reactant=0, products=[], rate=0.0)]
    from atm2d.newton import operator_split_step
    res = operator_split_step(state, 1.0, kzz=torch.ones(1, 3), source_terms=src, transport_form="c_diffusion")
    changed = not torch.equal(state.concentration, entry)
    same_as_result = torch.allclose(state.concentration, res.concentration)
    print(f"[R6] state changed on return: {changed}; equals the post-transport result: {same_as_result}")
    return changed


def r7_pins():
    from atm2d.pins import BoundaryPinSpec, build_pin_mask, apply_pin_mask_as_dirichlet_rows
    state = column(3, torch.tensor([[[1.0], [2.0], [3.0]]]))
    system, rhs = atm2d.build_implicit_step_system(state, torch.ones(1, 3), 1.0, transport_form="c_diffusion")
    mask, values = build_pin_mask(state, [BoundaryPinSpec([0], [0], torch.full((1, 3, 1), 7.0))])
    system, rhs = apply_pin_mask_as_dirichlet_rows(system, rhs, mask, values)
    c = atm2d.solve_sparse_system(system, rhs)
    print(f"[R7] pinned bottom cell after the solve: {float(c[0, 0, 0]):.6f} (pin 7)")
    return c


def r8_molecular():
    nlyr, temp, mu, g, rgas = 10, 200.0, 28.0, 980.665, 8.31446261815324e7    # K, g/mol, cm/s^2, erg/mol/K
    hscale = rgas * temp / (mu * g)                                            # cm
    z = torch.linspace(0.0, 10.0e5, nlyr + 1)                                  # cm
    zc = 0.5 * (z[1:] + z[:-1])
    c = torch.exp(-zc / hscale).view(1, nlyr, 1)
    state = atm2d.AtmState2D(x1f=z, x2f=torch.tensor([0.0, 1.0]), temperature=torch.full((1, nlyr), temp),
                             pressure=torch.full((1, nlyr), 1.0e6), concentration=c, gravity=g)
    dmol = torch.full((1, nlyr, 1, 1), 1.0e5)                                  # cm^2/s
    kzz = torch.zeros(1, nlyr)
    density = c[..., 0]
    for form in ("c_diffusion", "mr_diffusion", "mr_exp"):
        op = atm2d.build_transport_matrix(state, kzz, binary_diffusion=dmol, molecular_weights=torch.tensor([mu]),
                                          density=density, form=form)
        tend = op.matvec(c)[0, 1:-1, 0]                                        # interior cells
        scale = (1.0e5 / hscale ** 2) * c[0, 1:-1, 0]                          # D c / H^2, the size of each term
        print(f"[R8] H = {hscale:.4e} cm; form {form}: max |tendency| / (D c / H^2) over interior cells = "
              f"{float((tend.abs() / scale).max()):.3e}")


if __name__ == "__main__":
    print(f"torch {torch.__version__}; atm2d from $KINTERA_REPO/python at the pin")
    r1_neumann()
    r2_ceiling()
    r3_ros2_order()
    r4_disort_order()
    r5_budget_floor()
    r6_split_state()
    r7_pins()
    r8_molecular()
