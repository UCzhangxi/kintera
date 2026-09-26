"""Regression: VU->T and PV->T for `use-h2-dissociation` converge on a strongly dissociating grid.

From the cold constant-cv guess, plain Newton on the S-shaped U(T) jumped from the flat hot tail
across the latent peak to T < 0 (NaN) in 503 of these 2400 cells and ended far from the root in
117 more; the damped PV->T step left up to 0.36% error after the default 10 iterations. Both
solves are now a bracketed (rtsafe-style) Newton, PV->T with the exact f' from the Mayer relation.
"""
import re

import numpy as np
import pytest
import torch
import kintera
from kintera import ThermoOptions, ThermoY

torch.set_default_dtype(torch.float64)
NH, NHE = 1.6667, 0.16667


def thermo(tmp_path, extra):
    card = tmp_path / "h2diss.yaml"
    card.write_text("reference-state: {Tref: 300.0, Pref: 1.0e5, use-h2-dissociation: true%s}\n"
                    "species:\n- {name: H2, composition: {H: %r, He: %r}, cv_R: 2.5}\n"
                    % (extra, NH, NHE))
    return ThermoOptions.from_yaml(str(card))


@pytest.mark.parametrize("extra", ["", ", fused-h2diss: true"])
def test_inversions_converge_on_dissociating_grid(tmp_path, capfd, extra):
    op = thermo(tmp_path, extra)  # default max-iter
    TT, CC = np.meshgrid(np.linspace(1100., 5500., 60), np.logspace(-2, 4, 40), indexing="ij")
    T = torch.tensor(TT.ravel())
    rho = torch.tensor(CC.ravel()) * kintera.species_weights()[0]
    th = ThermoY(op)
    V = th.compute("DY->V", (rho, torch.zeros(0, T.numel())))
    U, P = th.compute("VT->U", (V, T)), th.compute("VT->P", (V, T))
    capfd.readouterr()
    T_vu = ThermoY(op).compute("VU->T", (V, U))  # fresh objects: no warm-start seeds
    T_pv = ThermoY(op).compute("PV->T", (P, V))
    log = capfd.readouterr().err  # TORCH_WARN goes to C++ stderr, not Python warnings
    assert not re.search(r"max[ _]iter", log), log  # fused: "hit max_iter"; torch: "max iterations"
    for name, Ts in [("VU->T", T_vu), ("PV->T", T_pv)]:
        err = ((Ts - T).abs() / T).numpy()
        assert np.isfinite(err).all(), "%s: %d NaN" % (name, (~np.isfinite(err)).sum())
        assert err.max() < 1e-9, "%s: %d cells off, max rel err %g" % (name, (err > 1e-9).sum(), err.max())


def test_full_dissociation_does_not_overflow(tmp_path):
    # Kc^2 overflowed above ~44 kK and the root returned [H] = 0, i.e. cz fell back to 1
    op = thermo(tmp_path, "")
    th = ThermoY(op)
    T = torch.tensor([3.0e4, 4.5e4, 6.0e4])
    V = th.compute("DY->V", (torch.full((3,), kintera.species_weights()[0]), torch.zeros(0, 3)))
    cz = th.compute("VT->P", (V, T)) / (8.31446 * T)
    np.testing.assert_allclose(cz.numpy(), NH + NHE, rtol=1e-6)


@pytest.mark.parametrize("max_iter", [None, 30])
def test_degenerate_cell_does_not_seed_the_next_solve(tmp_path, capfd, max_iter):
    # A rho = 0 cell (c at the gas floor) converged to T ~ 1e23 K and was kept as the fused
    # warm-start seed; the next PV->T of the same size then bisected down from it and returned
    # ~6e14 K for a physical cell at that index, with only a max_iter warning. At max-iter 30
    # the degenerate cell does converge, so only the seed range check stops it.
    op = thermo(tmp_path, ", fused-h2diss: true")
    if max_iter is not None:
        op.max_iter(max_iter)
    th = ThermoY(op)
    T = torch.linspace(1100., 5500., 64)
    rho = torch.full_like(T, 10.) * kintera.species_weights()[0]  # c = 10 mol/m^3
    V = th.compute("DY->V", (rho, torch.zeros(0, T.numel())))
    P = th.compute("VT->P", (V, T))
    rho_bad = rho.clone()
    rho_bad[::8] = 0.
    th.compute("PV->T", (P, th.compute("DY->V", (rho_bad, torch.zeros(0, T.numel())))))
    capfd.readouterr()  # the kernels' TORCH_WARN goes to C++ stderr, not Python warnings
    T_pv = th.compute("PV->T", (P, V))
    assert "hit max_iter" not in capfd.readouterr().err
    np.testing.assert_allclose(T_pv.numpy(), T.numpy(), rtol=1e-9)


@pytest.mark.parametrize("ab", ["PV->T", "VU->T"])
def test_cold_cell_below_seed_range_still_converges(tmp_path, capfd, ab):
    # warm seeds are kept only inside [kTmin, kTmax] = [200, 6000] K; a colder cell loses its
    # seed and restarts from the cold guess every call, but must still return its own T
    op = thermo(tmp_path, ", fused-h2diss: true")
    th = ThermoY(op)
    T = torch.tensor([150., 180., 250.])
    rho = torch.full_like(T, 1.0) * kintera.species_weights()[0]
    V = th.compute("DY->V", (rho, torch.zeros(0, T.numel())))
    X = th.compute("VT->P", (V, T)) if ab == "PV->T" else th.compute("VT->U", (V, T))
    args = (X, V) if ab == "PV->T" else (V, X)
    capfd.readouterr()
    for _ in range(3):
        Ts = th.compute(ab, args)
        np.testing.assert_allclose(Ts.numpy(), T.numpy(), rtol=1e-9)
    assert "hit max_iter" not in capfd.readouterr().err


def test_unconverged_cell_finishes_on_the_next_call(tmp_path, capfd):
    # at the default max_iter, thin partly dissociated cells do not converge in one VU->T call;
    # their in-range iterate is kept as the seed, so the next same-size call finishes them
    op = thermo(tmp_path, ", fused-h2diss: true")
    th = ThermoY(op)
    TT, CC = np.meshgrid(np.linspace(1900., 2950., 22), np.logspace(-7, -2.2, 12), indexing="ij")
    T = torch.tensor(TT.ravel())
    rho = torch.tensor(CC.ravel()) * kintera.species_weights()[0]
    V = th.compute("DY->V", (rho, torch.zeros(0, T.numel())))
    U = th.compute("VT->U", (V, T))
    err1 = ((th.compute("VU->T", (V, U)) - T).abs() / T).max().item()
    assert err1 > 1e-9, "every cell converged on the first call: the test is vacuous"
    capfd.readouterr()
    T_vu = th.compute("VU->T", (V, U))
    assert "hit max_iter" not in capfd.readouterr().err
    np.testing.assert_allclose(T_vu.numpy(), T.numpy(), rtol=1e-9)
