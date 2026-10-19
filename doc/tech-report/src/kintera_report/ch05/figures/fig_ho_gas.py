"""Hot H-O gas with NASA-9 equilibrium constants (@sec-ch05-log-k).

(a) ln K of the four reactions from Nasa9LogK against temperature; (b) equilibrium mole fractions returned by
EquilibriumTP at 1e5 Pa from a start of 2 H2 + O2. Data: src/kintera_report/ch05/data/h2o_dissociation.json, written
by src/kintera_report/ch05/runs/run_equilibrium.py at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45 (its
`provenance` field gives the deck, cases, command and versions).
"""
import json
from pathlib import Path

from kintera_report import figstyle as fs

DATA = Path(__file__).resolve().parent.parent / "data" / "h2o_dissociation.json"
REACTIONS = ["H$_2$ + ½O$_2$ ⇌ H$_2$O", "H$_2$ ⇌ 2H", "O$_2$ ⇌ 2O", "½H$_2$ + ½O$_2$ ⇌ OH"]
SPECIES = ["H$_2$", "O$_2$", "H$_2$O", "OH", "H", "O"]
COLORS = [fs.BLACK, fs.ORANGE, fs.BLUE, fs.GREEN, fs.VERMILLION, fs.PURPLE]
MARKERS = ["o", "s", "^", "v", "D", "x"]


def make_fig():
    d = json.loads(DATA.read_text())
    T = d["T"]
    fig, (ax1, ax2) = fs.new_figure("double", 2.6, 1, 2)
    for j, name in enumerate(REACTIONS):
        ax1.plot(T, [row[j] for row in d["log_k"]], "-", marker=MARKERS[j], ms=3, color=COLORS[j], label=name)
    ax1.axhline(0., color=fs.GREY, lw=0.6)
    ax1.set_xlabel("temperature $T$ [K]")
    ax1.set_ylabel("$\\ln K_r$ [-]")
    ax1.legend(loc="lower right")
    for n, name in enumerate(SPECIES):
        ax2.semilogy(T, [row[n] for row in d["x"]], "-", marker=MARKERS[n], ms=3, color=COLORS[n], label=name)
    ax2.set_ylim(1e-8, 3.)
    ax2.set_xlabel("temperature $T$ [K]")
    ax2.set_ylabel("mole fraction [-]")
    ax2.legend(loc="lower center", ncol=3)
    fs.panel_labels([ax1, ax2])
    return fig
