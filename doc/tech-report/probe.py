"""Stand-in measurement of deck nucleation ln K on an unmodified build.

The historical chapter-12 scratch probe was NOT recovered. This stand-in cannot
validate the deferred patched-CUDA experiment or its historical 4.559 result.
Use: python -P probe.py h2o_ideal nh3_ideal
KINTERA_REPO supplies tests/jupiter.yaml. Derivative names are not registered
nucleation formulas. Missing requested names fail even when other names exist.
CPU-only results do not establish CPU/CUDA equivalence. Printed device differences
are measurements, not a numerical equivalence assertion.
"""
import argparse
import os
import sys

R = 8.31446261815324

DECK = ("tests", "jupiter.yaml")


def _deck() -> str:
    repo = os.environ.get("KINTERA_REPO")
    if not repo:
        sys.exit("probe.py: set KINTERA_REPO to a kintera checkout (it supplies the deck)")
    path = os.path.join(repo, *DECK)
    if not os.path.exists(path):
        sys.exit(f"probe.py: no deck at {path}")
    return path


def log_k(kintera, torch, op, th, names, temps):
    """ln K_j(T) for every nucleation reaction, as check_ch2_svp.py computes it."""
    ngas = len(op.vapor_ids())
    T = torch.tensor(temps, dtype=torch.float64)
    c = torch.zeros(len(temps), len(op.species()), dtype=torch.float64)
    c[:, 1:ngas] = (1.0 / (R * T)).unsqueeze(-1)
    c[:, 0] = 1.0
    out = {}
    for device in ("cpu", "cuda"):
        if device == "cuda" and not torch.cuda.is_available():
            out[device] = None
            continue
        rh = kintera.relative_humidity(T.to(device), c.to(device),
                                       th.buffer("stoich").to(device), op.nucleation(), ngas)
        out[device] = (-rh.log()).cpu()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="func1 names to report; default: every nucleation formula")
    ap.add_argument("--temps", default="250,300", help="kelvin, comma separated")
    ap.add_argument("--self-test", action="store_true",
                    help="check the argument handling and ln K construction without a GPU")
    args = ap.parse_args()
    temps = [float(t) for t in args.temps.split(",")]

    try:
        import torch
        import kintera
    except ImportError as e:
        sys.exit(f"probe.py: {e}. Build and install kintera first.")

    op = kintera.ThermoOptions.from_yaml(_deck())
    th = kintera.ThermoX(op)
    forms = list(op.nucleation().logsvp())
    wanted = args.names or forms
    missing = [n for n in wanted if n not in forms]
    if missing:
        # Never silently report nothing: a name the deck does not register is the user's answer.
        print(f"not registered by this deck: {', '.join(missing)}", file=sys.stderr)
        print(f"deck registers: {', '.join(forms)}", file=sys.stderr)
        return 2

    cols = log_k(kintera, torch, op, th, wanted, temps)
    if cols["cuda"] is None and not args.self_test:
        print("no CUDA device visible: the CPU column alone cannot show a device-table gap",
              file=sys.stderr)

    print(f"kintera {kintera.__version__}; ln K at {', '.join(f'{t:g} K' for t in temps)}")
    print(f"{'name':<24}{'T':>8}{'cpu':>16}{'cuda':>16}   verdict")
    worst = 0.0
    for name in wanted:
        if name not in forms:
            continue
        j = forms.index(name)
        for i, t in enumerate(temps):
            cpu = cols["cpu"][i, j].item()
            if cols["cuda"] is None:
                print(f"{name:<24}{t:>8g}{cpu:>16.6f}{'n/a':>16}   cpu only")
                continue
            gpu = cols["cuda"][i, j].item()
            d = abs(cpu - gpu)
            worst = max(worst, d)
            print(f"{name:<24}{t:>8g}{cpu:>16.6f}{gpu:>16.6f}   "
                  f"{'same' if d == 0 else f'DIFFER by {d:.6g}'}")
    if cols["cuda"] is not None:
        print(f"largest CPU/CUDA difference: {worst:.6g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
