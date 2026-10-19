"""Proposed check of the fixed-energy solve (@sec-ch04-equilibrate-uv): after ThermoY.forward, the host reads the
temperature back from the returned state at the input internal energy (`VU->T`); at that temperature no reaction may
be supersaturated, and a reaction whose condensate is present must be saturated, to the solver tolerance.

Cases: (a) the one-vapour card (x_v 5e-2, 1e5 Pa, Tref 300 K), 25 cells started at 297..303 K, uv-solver kkt and
auto; (b) the five cold-start cells of tests/jupiter.yaml, uv-solver kkt, max-iter 30; (c) the same with max-iter 2
and (d) the one-vapour card with use-h2-cp and Tref 0 at 300 K, where the check must fail.

    KINTERA_REPO=<kintera checkout> python -P uv_host_rh.py
"""
import sys
from pathlib import Path
import torch
import kintera as kt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import ONE_VAPOUR, adjust, card_with, cell_from_tpx, jupiter, jupiter_cold_cells, write_card

TOL = 1e-5  # the RH tolerance of test_saturation_adjustment_nh4sh.py


def measure(label, card, T, x):
    thy, rho, y = cell_from_tpx(card, T, torch.full_like(T, 1e5), x)
    d, _, T1, lrh, conc = adjust(thy, rho, y, T)
    # a reaction whose condensate is present after the solve must sit on its saturation curve
    stoich = thy.buffer("stoich")
    ngas = len(thy.options.vapor_ids())
    present = ((conc[:, ngas:] > 0).double() @ (stoich[ngas:] > 0).double()) > 0
    over = lrh.max().item()
    on_curve = lrh[present].abs().max().item() if present.any() else 0.
    ok = over <= TOL and on_curve <= TOL
    print(f"{label}: cells {T.numel()}, diag {sorted(set(d.tolist()))}, max ln RH {over:+.1e}, "
          f"max |ln RH| with condensate {on_curve:.1e}, check {'passes' if ok else 'FAILS'}")


T = torch.arange(297., 303.001, 0.25)
x = torch.zeros(T.numel(), 3)
x[:, 1] = 5e-2
x[:, 0] = 1 - 5e-2
for s in ("kkt", "auto"):
    measure(f"(a) one vapour, {s}", write_card(f"host_{s}.yaml", ONE_VAPOUR.format(tref=300., max_iter=50, solver=s)),
            T, x)
Tj = torch.tensor([130., 150., 175., 200., 250.])
for mi, tag in ((30, "(b)"), (2, "(c)")):
    card = card_with(jupiter(), f"host_jup_{mi}.yaml", max_iter=mi, uv_solver="kkt")
    names = kt.ThermoX(kt.ThermoOptions.from_yaml(card)).options.species()
    measure(f"{tag} jupiter.yaml cold start, kkt, max-iter {mi}", card, Tj, jupiter_cold_cells(names, Tj))
card = write_card("host_h2cp.yaml", ONE_VAPOUR.format(tref=0., max_iter=50, solver="kkt").replace(
    "Pref: 1.e5", "Pref: 1.e5, use-h2-cp: true").replace("name: dry, composition: {H: 1.5, He: 0.15}",
                                                          "name: H2, composition: {H: 2}"))
measure("(d) one vapour, use-h2-cp, Tref 0", card, torch.tensor([300.]), torch.tensor([[1 - 5e-2, 5e-2, 0.]]))
