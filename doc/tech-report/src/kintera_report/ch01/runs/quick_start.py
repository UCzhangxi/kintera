"""Quick start of chapter 1 (@sec-ch01): one equilibrium-condensation call on the Jupiter example card.

Needs kintera built at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45 (CPU, double), installed as the README of
that commit describes. The input card `examples/jupiter.yaml` is found through the environment variable
KINTERA_REPO, the root of a kintera checkout at that commit. Unlike `examples/example_jupiter.py`, the composition
is fixed rather than random, so the printed numbers are reproducible.

Run: KINTERA_REPO=<checkout> CUDA_VISIBLE_DEVICES= python -P src/kintera_report/ch01/runs/quick_start.py [max_iter]
`max_iter` is the iteration limit of the equilibrium solve, 30 by default; 0 keeps the card's own limit.
Recorded output: src/kintera_report/ch01/data/quick_start.out (default) and quick_start_maxiter0.out (argument 0).
"""
import os
import platform
import sys
from pathlib import Path

import torch
import kintera
from kintera import ThermoOptions, ThermoX

torch.set_default_dtype(torch.float64)


def main():
    root = os.environ.get("KINTERA_REPO")
    if not root:
        raise SystemExit("set KINTERA_REPO to a kintera checkout at 0d9f67f97d841147e23283d2dcdab302238d2c45")
    card = str(Path(root) / "examples" / "jupiter.yaml")

    print(f"[Q0] versions: python {platform.python_version()}, torch {torch.__version__}, "
          f"kintera {kintera.__version__}")

    max_iter = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    op = ThermoOptions.from_yaml(card)
    if max_iter > 0:
        op.max_iter(max_iter)
    print(f"[Q5] max_iter: {op.max_iter()}")
    thermo = ThermoX(op)
    species = op.species()
    print(f"[Q1] species ({len(species)}): {species}")

    # 200 K, 1 bar; vapours only, no condensate yet
    temp = torch.tensor([200.0])
    pres = torch.tensor([1.0e5])
    xfrac = torch.zeros((1, 1, len(species)))
    initial = {"dry": 0.86, "H2O": 0.1, "NH3": 0.03, "H2S": 0.01}
    for name, value in initial.items():
        xfrac[..., species.index(name)] = value

    print(f"[Q2] xfrac before: {[round(v, 6) for v in xfrac.flatten().tolist()]}")
    thermo.forward(temp, pres, xfrac)
    print(f"[Q3] xfrac after:  {[f'{v:.6e}' for v in xfrac.flatten().tolist()]}")
    print(f"[Q4] sum of xfrac after: {xfrac.sum().item():.15f}")


if __name__ == "__main__":
    main()
