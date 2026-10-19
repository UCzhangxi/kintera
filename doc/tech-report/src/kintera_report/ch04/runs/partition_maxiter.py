"""The partition method's temperature search is capped by max-iter (@sec-ch04-equilibrate-uv): the one-vapour card
with Tref 0 and uv-solver partition, 15 cells from 200 to 320 K with x_v from 1e-3 to 5e-2, for max-iter 3, 5, 10
and 50; failed cells (diagnostic -1) and the largest pass count of the converged ones.

    python -P partition_maxiter.py
"""
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import ONE_VAPOUR, adjust, cell_from_tpx, write_card

T = torch.linspace(200., 320., 15)
xv = torch.logspace(-3., torch.log10(torch.tensor(5e-2)).item(), 15)
x = torch.stack([1 - xv, xv, torch.zeros_like(xv)], -1)
for mi in (3, 5, 10, 50):
    card = write_card(f"pmi_{mi}.yaml", ONE_VAPOUR.format(tref=0., max_iter=mi, solver="partition"))
    thy, rho, y = cell_from_tpx(card, T, torch.full_like(T, 1e5), x)
    d, _, _, lrh, conc = adjust(thy, rho, y, T)
    ok = d > 0
    cloudy = ok & (conc[:, 2] > 0)
    print(f"max-iter {mi}: failed {int((d == -1).sum())} of {T.numel()}, largest pass count "
          f"{int(d[ok].max()) if ok.any() else 0}, converged cells with condensate {int(cloudy.sum())}, "
          f"their max |ln RH| {lrh[cloudy].abs().max().item() if cloudy.any() else float('nan'):.1e}")
