"""Timing protocol for one kintera call on CPU and CUDA (@sec-ch12-dispatch).

Times the implicit kinetics step of `tests/jupiter.yaml` -- `Kinetics.forward`, `Kinetics.jacobian` and
`evolve_implicit` -- on the same cells, precision and inputs on each device. It follows the protocol of the
chapter: the module and inputs are moved to the device once, before timing, so host-device transfers are excluded;
a few warm-up calls absorb one-time costs (library load, kernel compilation, caches); every CUDA sample is bracketed
by CUDA events after a synchronization; the median and the interquartile range of the samples are reported with the
metadata that can move the numbers. It prints the numbers and makes no claim about them.

    KINTERA_REPO=<kintera checkout> python -P time_dispatch.py [--ncell 4096] [--dtype float64] [--repeat 20]
"""
import argparse
import os
import platform
import statistics
import time

import torch
import kintera as kt


def step(kin, temp, pres, conc, dt):
    rate, rc_ddc, rc_ddt = kin.forward(temp, pres, conc)
    jac = kin.jacobian(temp, conc, torch.ones_like(temp), rate, rc_ddc, rc_ddt)
    return kt.evolve_implicit(rate, kin.stoich, jac, dt)


def samples(fn, device, warmup, repeat):
    for _ in range(warmup):
        fn()
    out = []
    for _ in range(repeat):
        if device.type == "cuda":
            torch.cuda.synchronize(device)
            start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            start.record()
            fn()
            end.record()
            torch.cuda.synchronize(device)
            out.append(start.elapsed_time(end) / 1e3)
        else:
            t0 = time.perf_counter()
            fn()
            out.append(time.perf_counter() - t0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ncell", type=int, default=4096)
    ap.add_argument("--dtype", default="float64", choices=["float32", "float64"])
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--repeat", type=int, default=20)
    ap.add_argument("--dt", type=float, default=10.0)
    a = ap.parse_args()
    dtype = getattr(torch, a.dtype)
    yaml = os.path.join(os.environ["KINTERA_REPO"], "tests", "jupiter.yaml")
    gen = torch.Generator().manual_seed(0)
    devices = [torch.device("cpu")] + ([torch.device("cuda")] if torch.cuda.is_available() else [])
    print(f"kintera {getattr(kt, '__version__', '?')}, torch {torch.__version__}, Python {platform.python_version()}, "
          f"CPU threads {torch.get_num_threads()}, ncell {a.ncell}, dtype {a.dtype}, warmup {a.warmup}, "
          f"repeat {a.repeat}, transfers excluded")
    for device in devices:
        kin = kt.Kinetics(kt.KineticsOptions.from_yaml(yaml))
        kin.to(device)            # in place; the binding returns None
        kin.to(dtype)
        n = len(kin.options.species())
        temp = (180.0 + 40.0 * torch.rand(a.ncell, generator=gen)).to(device, dtype)
        pres = torch.full((a.ncell,), 1.0e5).to(device, dtype)
        conc = (1e-3 * torch.rand(a.ncell, n, generator=gen)).to(device, dtype)
        t = samples(lambda: step(kin, temp, pres, conc, a.dt), device, a.warmup, a.repeat)
        q = statistics.quantiles(t, n=4)
        name = torch.cuda.get_device_name(device) if device.type == "cuda" else platform.processor() or "cpu"
        print(f"{device.type} ({name}): median {statistics.median(t):.4e} s, interquartile {q[0]:.4e} to {q[2]:.4e} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
