"""CPU versus CUDA for the two kinetics features the suite checks on CPU only (@sec-ch13-device-coverage).

Reads the reaction decks of `tests/test_evaporation_kessler.py` (Kessler-form evaporation) and
`tests/test_coagulation_pressure_switch.py` (pressure-switched coagulation) from a kintera checkout, builds the same
64 cells on both devices in double precision, and compares the rates and rate constants
(`Kinetics.forward_with_rate_constants`), the reaction-space Jacobian (`Kinetics.jacobian`) and the implicit step
(`kintera.evolve_implicit`). The difference of a quantity is max|a_cuda - a_cpu| / max|a_cpu| over all cells.

    KINTERA_REPO=<kintera checkout> python -P gpu_probe.py [--tol 1e-13]

Needs a CUDA build of kintera; exits 3 without a CUDA device, 1 if any difference exceeds --tol
or outputs have incompatible shapes or nonfinite values. An all-zero CPU reference uses absolute error.
"""
import argparse
import importlib.util
import math
import os
import platform
import sys
import tempfile

import torch
import kintera as kt

NCELL = 64


def test_module(name):
    path = os.path.join(os.environ["KINTERA_REPO"], "tests", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load(card):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(card)
    try:
        op = kt.KineticsOptions.from_yaml(f.name)
        return op, kt.Kinetics(op)
    finally:
        os.unlink(f.name)


def kessler_cells(mod, names):
    """Sub- and supersaturated methane cells, with and without precipitation, 70 to 100 K."""
    g = torch.Generator().manual_seed(1)
    u = torch.rand(NCELL, 4, generator=g, dtype=torch.float64)
    T = 70. + 30. * u[:, 0]
    P = 1.e5 + 1.e5 * u[:, 1]
    n = P / (mod.R * T)
    c = torch.zeros(NCELL, len(names), dtype=torch.float64)
    c[:, names.index("CH4")] = (0.002 + 0.05 * u[:, 2]) * n
    c[:, names.index("CH4(s)")] = 0.002 * n
    c[:, names.index("CH4(s,p)")] = torch.where(torch.arange(NCELL) % 8 == 0, 0., 0.02 * u[:, 3]) * n
    return T, P, c


def switch_cells(mod, names):
    """Pressures on both sides of the threshold, including its two neighbouring doubles."""
    pth = mod.PTH
    edge = [math.nextafter(pth, 0.), pth, math.nextafter(pth, math.inf), pth * (1. - 1e-9), pth * (1. + 1e-9)]
    P = torch.tensor(edge + torch.logspace(3., 5., NCELL - len(edge), dtype=torch.float64).tolist(),
                     dtype=torch.float64)
    T = torch.full((NCELL,), 80., dtype=torch.float64)
    n = P / (mod.R * T)
    c = torch.zeros(NCELL, len(names), dtype=torch.float64)
    for k, sp in enumerate(mod.FACTORS):
        c[:, names.index(f"{sp}(s)")] = (1. + k) * 1e-3 * n
        c[:, names.index(f"{sp}(s,p)")] = 0.5e-3 * n
    return T, P, c


def evaluate(kin, T, P, c, dt):
    rate, rc_ddC, rc_ddT, kf = kin.forward_with_rate_constants(T, P, c)
    jac = kin.jacobian(T, c, torch.ones_like(T), rate, rc_ddC, rc_ddT, kf)
    stoich = dict(kin.named_buffers())["stoich"]
    step = kt.evolve_implicit(rate, stoich, jac, dt)
    return {"rate": rate, "rate constant": kf, "jacobian": jac, "implicit step": step}


def comparison_error(a, b):
    """Norm-wise relative error; invalid outputs fail even if max would hide NaN."""
    if a.shape != b.shape or a.numel() == 0:
        return math.inf
    if not torch.isfinite(a).all().item() or not torch.isfinite(b).all().item():
        return math.inf
    scale = a.abs().max().item()
    error = (b - a).abs().max().item()
    value = error / scale if scale > 0. else error
    return value if math.isfinite(value) else math.inf


def compare(label, card, cells, dt):
    op, kin = load(card)
    names = op.species()
    T, P, c = cells(names)
    cpu = evaluate(kin, T, P, c, dt)
    kin_cuda = kt.Kinetics(op)
    kin_cuda.to(torch.device("cuda"))
    gpu = evaluate(kin_cuda, *(x.cuda() for x in (T, P, c)), dt)
    torch.cuda.synchronize()
    worst = 0.
    for key, a in cpu.items():
        b = gpu[key].cpu()
        scale = a.abs().max().item()
        diff = comparison_error(a, b)
        worst = max(worst, diff)
        print(f"  {label:16s} {key:14s} shape {tuple(a.shape)!s:14s} max|cpu| {scale:.3e}  rel diff {diff:.2e}"
              f"  bitwise equal {torch.equal(a, b)}")
    return worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=1e-13)
    ap.add_argument("--dt", type=float, default=10.)
    a = ap.parse_args()
    if not math.isfinite(a.tol) or a.tol < 0.:
        ap.error("--tol must be finite and nonnegative")
    if not math.isfinite(a.dt) or a.dt <= 0.:
        ap.error("--dt must be finite and positive")
    if not torch.cuda.is_available():
        print("no CUDA device: nothing compared")
        return 3
    torch.set_default_dtype(torch.float64)
    kes = test_module("test_evaporation_kessler")
    sw = test_module("test_coagulation_pressure_switch")
    print(f"kintera {kt.__version__}, torch {torch.__version__} (CUDA {torch.version.cuda}), "
          f"Python {platform.python_version()}, {torch.cuda.get_device_name(0)}, double, {NCELL} cells, dt {a.dt:g} s")
    worst = max(compare("kessler", kes.CARD.format(extra=kes.KESSLER), lambda n: kessler_cells(kes, n), a.dt),
                compare("pressure switch", sw.CARD.format(**sw.SWITCH), lambda n: switch_cells(sw, n), a.dt))
    ok = worst <= a.tol
    print(f"largest relative CPU-CUDA difference {worst:.2e} (tol {a.tol:g}) {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
