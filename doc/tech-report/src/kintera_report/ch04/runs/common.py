"""Shared helpers of the chapter 4 runs (@sec-ch04): input cards, ThermoX residuals, ThermoY cells.

Needs kintera built at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45 (CPU, double). The kintera test input
`tests/jupiter.yaml` is found through the environment variable KINTERA_REPO, the root of a kintera checkout at
that commit. Self-written cards are defined in the scripts that use them and written to a temporary directory.
"""
import os
import tempfile
from pathlib import Path

import torch
import kintera as kt

torch.set_default_dtype(torch.float64)
TMP = Path(tempfile.mkdtemp(prefix="kintera_ch04_"))


def jupiter():
    root = os.environ.get("KINTERA_REPO")
    if not root:
        raise SystemExit("set KINTERA_REPO to a kintera checkout at 0d9f67f97d841147e23283d2dcdab302238d2c45")
    return str(Path(root) / "tests" / "jupiter.yaml")


def write_card(name, text):
    path = TMP / name
    path.write_text(text)
    return str(path)


def card_with(path_in, name, max_iter=None, uv_solver=None):
    """Copy a card, prepending `dynamics: {equation-of-state: {...}}` with the given options."""
    s = Path(path_in).read_text()
    dyn = {}
    if max_iter is not None:
        dyn["max-iter"] = max_iter
    if uv_solver is not None:
        dyn["uv-solver"] = uv_solver
    if dyn:
        body = ", ".join(f"{k}: {v}" for k, v in dyn.items())
        s = f"dynamics: {{equation-of-state: {{{body}}}}}\n" + s
    return write_card(name, s)


def jupiter_cold_cells(names, temps):
    """The cold-start cells: x(H2O, NH3, H2S) = 3e-3, 3e-4, 1e-4, rest dry, no condensate."""
    x = torch.zeros(len(temps), len(names))
    x[:, names.index("H2O")] = 3e-3
    x[:, names.index("NH3")] = 3e-4
    x[:, names.index("H2S")] = 1e-4
    x[:, names.index("dry")] = 1 - x.sum(-1)
    return x


def log_rh_x(th, temp, pres, xfrac):
    """ln RH per reaction for a ThermoX state (ideal-gas partial pressures)."""
    conc = th.compute("TPX->V", [temp, pres, xfrac])
    rh = kt.relative_humidity(temp, conc, th.buffer("stoich"), th.options.nucleation())
    return rh.log()


def cell_from_tpx(card, T, P, x):
    """ThermoY cells with the composition x at (T, P): density and mass fractions (dry species implicit)."""
    thx = kt.ThermoX(kt.ThermoOptions.from_yaml(card))
    thy = kt.ThermoY(kt.ThermoOptions.from_yaml(card))
    conc = thx.compute("TPX->V", [T, P, x])
    dens = conc * (1.0 / thy.buffer("inv_mu"))
    rho = dens.sum(-1)
    yfrac = (dens / rho.unsqueeze(-1))[..., 1:].t().contiguous()
    return thy, rho, yfrac


def adjust(thy, rho, yfrac, T):
    """ThermoY.forward at the internal energy of (rho, yfrac, T). Returns the diagnostic, the gain, the temperature
    the host reads back from the returned state (`VU->T`), ln RH per reaction at that temperature, and the returned
    concentrations."""
    ivol = thy.compute("DY->V", [rho, yfrac])
    U = thy.compute("VT->U", [ivol, T])
    y = yfrac.clone()
    d = torch.zeros(T.numel(), 1)
    gain = thy.forward(rho, U, y, False, d)
    ivol1 = thy.compute("DY->V", [rho, y])
    conc1 = ivol1 * thy.buffer("inv_mu")
    T1 = thy.compute("VU->T", [ivol1, U])
    lrh = kt.relative_humidity(T1, conc1, thy.buffer("stoich"), thy.options.nucleation()).log()
    return d[:, 0], gain, T1, lrh, conc1


# The self-written one-vapour card: dry gas, water vapour and liquid water, one nucleation reaction.
ONE_VAPOUR = """reference-state: {{Tref: {tref}, Pref: 1.e5}}
dynamics: {{equation-of-state: {{max-iter: {max_iter}, uv-solver: {solver}}}}}
species:
  - {{name: dry, composition: {{H: 1.5, He: 0.15}}, cv_R: 2.5}}
  - {{name: H2O, composition: {{H: 2, O: 1}}, cv_R: 2.5, u0_R: 0.}}
  - {{name: H2O(l), composition: {{H: 2, O: 1}}, cv_R: 9.0, u0_R: -3430.}}
reactions:
  - {{equation: H2O <=> H2O(l), type: nucleation, rate-constant: {{formula: h2o_ideal}}}}
"""

VERSIONS = f"kintera {getattr(kt, '__version__', '?')} source build, torch {torch.__version__}"
