"""Shared setup for the Q346b checks: kintera built at 0d9f67f (v2.6.5)."""
import os
import sys
import warnings

# kintera 0d9f67f build (a worktree with `_pyinstall/`): $KINTERA_WT, else ../../wt/q346b-0d9f67f next to this dir
WT = os.environ.get("KINTERA_WT") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "wt", "q346b-0d9f67f"))
sys.path.insert(0, os.path.join(WT, "_pyinstall"))

import torch  # noqa: E402
import kintera  # noqa: E402

torch.set_default_dtype(torch.float64)
DECK = os.path.join(WT, "tests", "jupiter.yaml")


def thermo_x(deck=DECK, max_iter=None, ftol=None):
    op = kintera.ThermoOptions.from_yaml(deck)
    if max_iter is not None:
        op.max_iter(max_iter)
    if ftol is not None:
        op.ftol(ftol)
    th = kintera.ThermoX(op)
    th.to(torch.float64)
    return op, th


def species(op):
    """Names of the ThermoX working set, in xfrac order (vapours, then clouds)."""
    names = kintera.species_names()
    return [names[i] for i in list(op.vapor_ids()) + list(op.cloud_ids())]


def jupiter_x(op, xh2o=2.5e-3, xnh3=3.0e-4, xh2s=8.0e-5, n=1):
    """Total composition for jupiter.yaml: dry + 3 vapours, clouds empty."""
    sp = species(op)
    x = torch.zeros(n, len(sp))
    x[:, sp.index("H2O")] = xh2o
    x[:, sp.index("NH3")] = xnh3
    x[:, sp.index("H2S")] = xh2s
    x[:, 0] = 1.0 - x[:, 1:].sum(-1)
    return sp, x


def version_line():
    return f"kintera {kintera.__version__} from $KINTERA_WT/{os.path.relpath(kintera.__file__, WT)}"
