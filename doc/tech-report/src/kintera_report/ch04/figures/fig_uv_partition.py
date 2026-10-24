"""Partition method against the general method near the reference temperature (@sec-ch04-equilibrate-uv).

Remaining ln RH after `ThermoY.forward` with `uv-solver: partition` and `uv-solver: kkt`, one vapour (water,
x_v 5e-2, 1 bar, Tref 300 K), against the start temperature. Data: src/kintera_report/ch04/data/uv_partition_tref.json,
written by a run of kintera at kintera@e357792d50639d68e9090b542edf038d2b029aa2 (see its `provenance`).
"""
import json
from pathlib import Path

from kintera_report import figstyle as fs

DATA = Path(__file__).resolve().parent.parent / "data" / "uv_partition_tref.json"


def make_fig():
    d = json.loads(DATA.read_text())
    p, k = d["partition"], d["kkt"]
    fig, ax = fs.new_figure("single", 2.4)
    ax.plot(p["T0"], p["ln_rh"], "^", color=fs.VERMILLION, label="partition")
    ax.plot(k["T0"], k["ln_rh"], "o", color=fs.GREEN, mfc="none", label="kkt")
    ax.axvline(300.0, color=fs.BLACK, ls=":", lw=0.8)
    ax.text(300.1, 0.9, "Tref", fontsize=fs.SMALL_PT, transform=ax.get_xaxis_transform())
    ax.set_xlabel("start temperature [K]")
    ax.set_ylabel("$\\ln \\mathrm{RH}$ after the solve [-]")
    ax.legend(loc="upper right")
    return fig
