"""Cold-start saturation adjustment at fixed temperature and pressure (@sec-ch04-equilibrate-tp).

(a) outer iterations `equilibrate_tp` needs to converge with max-iter 60, against the explicit reduced max-iter of 10;
(b) the largest remaining ln RH when max-iter is 10. Data: src/kintera_report/ch04/data/tp_coldstart.json, written by
a run of kintera at kintera@e357792d50639d68e9090b542edf038d2b029aa2 (its `provenance` field gives the
deck, cells, command and versions).
"""
import json
from pathlib import Path

from kintera_report import figstyle as fs

DATA = Path(__file__).resolve().parent.parent / "data" / "tp_coldstart.json"


def make_fig():
    d = json.loads(DATA.read_text())
    a, b = d["max_iter_60"], d["max_iter_10"]
    fig, (ax1, ax2) = fs.new_figure("double", 2.4, 1, 2)
    ax1.plot(a["T"], a["diag"], "o-", color=fs.GREEN, label="iterations needed (max-iter 60)")
    ax1.axhline(10, color=fs.VERMILLION, ls="--", label="reduced max-iter 10")
    ax1.set_xlabel("temperature $T$ [K]")
    ax1.set_ylabel("outer iterations [-]")
    ax1.legend(loc="upper right")
    failed = [t for t, g in zip(b["T"], b["diag"]) if g < 0]
    ax2.plot(b["T"], b["max_ln_rh"], "s-", color=fs.VERMILLION, label="max-iter 10")
    ax2.plot(a["T"], a["max_ln_rh"], "o-", color=fs.GREEN, label="max-iter 60")
    for t in failed:
        ax2.axvspan(t - 5, t + 5, color=fs.GREY, alpha=0.15, lw=0)
    ax2.set_xlabel("temperature $T$ [K]")
    ax2.set_ylabel("largest $\\ln \\mathrm{RH}$ after the solve [-]")
    ax2.legend(loc="upper right")
    fs.panel_labels([ax1, ax2])
    return fig
