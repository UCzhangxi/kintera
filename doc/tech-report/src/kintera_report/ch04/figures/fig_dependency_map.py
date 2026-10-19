"""Dependency map of the schemes of chapter 4 (@sec-ch04).

Boxes are the six schemes; arrows read "requires": the nucleation reactions define the conditions, both solvers aim
at the conditions and call the constrained least-squares step, and the warm-start and failure bookkeeping wraps both
solvers. No data file. Structure read from src/thermo/thermo_x.cpp, thermo_y.cpp, equilibrate_tp.h, equilibrate_uv.h
at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45.
"""
from matplotlib.patches import FancyBboxPatch

from kintera_report import figstyle as fs

BOXES = {
    "nuc": (0.10, 0.80, "nucleation\nreactions"),
    "cond": (0.10, 0.45, "equilibrium\nconditions"),
    "tp": (0.50, 0.70, "fixed T, p\n(ThermoX)"),
    "uv": (0.50, 0.20, "fixed U, V\n(ThermoY)"),
    "ls": (0.88, 0.45, "constrained\nleast squares"),
    "ws": (0.50, 0.95, "warm start, failures"),
}
ARROWS = [("cond", "nuc"), ("tp", "cond"), ("uv", "cond"), ("tp", "ls"), ("uv", "ls")]


def make_fig():
    fig, ax = fs.new_figure("double", 2.4)
    ax.set_axis_off()
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(0.0, 1.08)
    w, h = 0.20, 0.17
    for key, (x, y, text) in BOXES.items():
        color = fs.GREY if key == "ws" else fs.BLACK
        hh = 0.08 if key == "ws" else h
        ax.add_patch(FancyBboxPatch((x - w / 2, y - hh / 2), w, hh, boxstyle="round,pad=0.01",
                                    fc=fs.CELL_FILL, ec=color, lw=0.8))
        ax.text(x, y, text, ha="center", va="center", fontsize=fs.SMALL_PT)
    for a, b in ARROWS:
        xa, ya, _ = BOXES[a]
        xb, yb, _ = BOXES[b]
        if abs(xa - xb) < 1e-9:  # vertical: top edge to bottom edge
            start, end = (xa, ya + h / 2), (xb, yb - h / 2)
        elif xb < xa:  # target to the left
            start, end = (xa - w / 2, ya), (xb + w / 2, yb)
        else:
            start, end = (xa + w / 2, ya), (xb - w / 2, yb)
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=0.9, shrinkA=0, shrinkB=0))
    ax.plot([0.5, 0.5], [0.91, 0.79], ls=":", color=fs.GREY, lw=0.9)
    ax.plot([0.62, 0.62], [0.91, 0.29], ls=":", color=fs.GREY, lw=0.9)
    return fig
