"""Dependency map of the schemes of chapter 5 (@sec-ch05).

Arrows read "requires": the Newton iteration solves the conditions, which the options define and the log-K model
feeds; the diagnostics report on the Newton iteration. Structure read from src/equilibrium/ and
python/equilibrium/ at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45. No data file.
"""
from matplotlib.patches import FancyBboxPatch

from kintera_report import figstyle as fs

BOXES = {
    "opt": (0.12, 0.70, "options\n(YAML or API)"),
    "logk": (0.12, 0.25, "log K\n(NASA-9)"),
    "cond": (0.45, 0.47, "equilibrium\nconditions"),
    "newton": (0.80, 0.70, "Newton in\nreaction extents"),
    "diag": (0.80, 0.25, "convergence and\nfailure report"),
}
ARROWS = [("cond", "opt"), ("cond", "logk"), ("newton", "cond"), ("diag", "newton")]


def make_fig():
    fig, ax = fs.new_figure("double", 2.2)
    ax.set_axis_off()
    ax.set_xlim(-0.05, 1.0)
    ax.set_ylim(0.0, 0.95)
    w, h = 0.22, 0.2
    for key, (x, y, text) in BOXES.items():
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.01",
                                    fc=fs.CELL_FILL, ec=fs.BLACK, lw=0.8))
        ax.text(x, y, text, ha="center", va="center", fontsize=fs.SMALL_PT)
    for a, b in ARROWS:
        xa, ya, _ = BOXES[a]
        xb, yb, _ = BOXES[b]
        if abs(xa - xb) < 1e-9:
            start, end = (xa, ya + h / 2), (xb, yb - h / 2)
        elif xb < xa:
            start, end = (xa - w / 2, ya), (xb + w / 2, yb)
        else:
            start, end = (xa + w / 2, ya), (xb - w / 2, yb)
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=0.9, shrinkA=0, shrinkB=0))
    return fig
