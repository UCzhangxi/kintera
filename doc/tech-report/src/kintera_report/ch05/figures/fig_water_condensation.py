"""Water vapour over a pure liquid phase with NASA-9 constants (@sec-ch05-diagnostics).

(a) water partial pressure returned by EquilibriumTP against temperature, and the saturation pressure p_std/K from
the NASA-9 constant; (b) the reported error, with status 4 cells marked. The total water is fixed, so above about
301 K the liquid should vanish and cannot. Data: src/kintera_report/ch05/data/water_condensation.json, written by
src/kintera_report/ch05/runs/run_equilibrium.py at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45 (its
`provenance` field gives the deck, cases, command and versions).
"""
import json
from pathlib import Path

from kintera_report import figstyle as fs

DATA = Path(__file__).resolve().parent.parent / "data" / "water_condensation.json"


def make_fig():
    d = json.loads(DATA.read_text())
    T = d["T"]
    bad = [i for i, s in enumerate(d["status"]) if s != 0]
    fig, (ax1, ax2) = fs.new_figure("double", 2.4, 1, 2)
    ax1.plot(T, [v / 1e3 for v in d["psat_from_K"]], "-", color=fs.BLUE, label="$p_{\\mathrm{std}}/K$ (NASA-9)")
    ax1.plot(T, [v / 1e3 for v in d["p_h2o"]], "o", color=fs.GREEN, mfc="none", ms=4, label="EquilibriumTP")
    ax1.set_xlabel("temperature $T$ [K]")
    ax1.set_ylabel("water partial pressure [kPa]")
    ax1.legend(loc="upper left")
    for ax in (ax1, ax2):
        for i in bad:
            ax.axvspan(T[i] - 1.25, T[i] + 1.25, color=fs.GREY, alpha=0.15, lw=0)
    ax2.semilogy(T, [max(e, 1e-16) for e in d["error"]], "s", color=fs.VERMILLION, ms=3)
    ax2.axhline(1e-8, color=fs.BLACK, ls="--", lw=0.8)
    ax2.text(284, 2e-8, "ftol", ha="left", va="bottom", fontsize=fs.SMALL_PT)
    ax2.set_xlabel("temperature $T$ [K]")
    ax2.set_ylabel("reported error [-]")
    fs.panel_labels([ax1, ax2])
    return fig
