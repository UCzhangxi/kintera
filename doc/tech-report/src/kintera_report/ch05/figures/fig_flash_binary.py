"""Two-component ideal solution against the closed-form flash (@sec-ch05-conditions).

(a) liquid fraction returned by EquilibriumTP against pressure, with the closed-form (Rachford-Rice) answer inside
the two-phase window; (b) the reported equilibrium error. Grey bands: cells with status 4, where one phase should
vanish. Data: src/kintera_report/ch05/data/flash_binary.json, written by src/kintera_report/ch05/runs/
run_equilibrium.py at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45 (its `provenance` field gives the deck, cases,
command and versions).
"""
import json
from pathlib import Path

from kintera_report import figstyle as fs

DATA = Path(__file__).resolve().parent.parent / "data" / "flash_binary.json"


def make_fig():
    d = json.loads(DATA.read_text())
    p = [v / 1e5 for v in d["p"]]
    two = [i for i, c in enumerate(d["closed_liquid_fraction"]) if c is not None]
    fig, (ax1, ax2) = fs.new_figure("double", 2.4, 1, 2)
    for ax in (ax1, ax2):
        for i, s in enumerate(d["status"]):
            if s != 0:
                ax.axvspan(p[i] - 0.0125, p[i] + 0.0125, color=fs.GREY, alpha=0.15, lw=0)
    ax1.plot([p[i] for i in two], [d["closed_liquid_fraction"][i] for i in two], "-", color=fs.BLUE,
             label="closed form")
    ax1.plot(p, d["liquid_fraction"], "o", color=fs.GREEN, mfc="none", ms=4, label="EquilibriumTP")
    ax1.set_xlabel("pressure $p$ [bar]")
    ax1.set_ylabel("liquid fraction [-]")
    ax1.legend(loc="upper left")
    ax2.semilogy(p, [max(e, 1e-16) for e in d["error"]], "s", color=fs.VERMILLION, ms=3)
    ax2.axhline(1e-8, color=fs.BLACK, ls="--", lw=0.8)
    ax2.text(1.27, 2e-8, "ftol", ha="right", va="bottom", fontsize=fs.SMALL_PT)
    ax2.set_xlabel("pressure $p$ [bar]")
    ax2.set_ylabel("reported error [-]")
    fs.panel_labels([ax1, ax2])
    return fig
