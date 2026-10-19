"""The three lists of a named user function (@sec-ch12-device-functions), as read from src/func_table.cpp,
src/func_table.cu and src/utils/user_funcs.cu at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45. No data file.

Row 1 is the host name list `func1_names`, row 2 the host table `func1_table_cpu` (same index), row 3 the device
table `func1_table_cuda`, whose slot 0 holds `nullptr`, so the same name sits at index id + 1.
"""
from matplotlib.patches import Rectangle

from kintera_report import figstyle as fs

NAMES = ["h2o_ideal", "…", "f", "f_ddT"]


def make_fig():
    fig, ax = fs.new_figure("double", 2.3)
    ax.set_axis_off()
    w, h = 0.95, 0.5
    ncell = len(NAMES) + 1
    ax.set_xlim(-2.3, ncell + 0.2)
    ax.set_ylim(-0.35, 3.3)
    rows = [(2.5, "func1_names", ["(none)"] + NAMES, 1), (1.5, "func1_table_cpu", ["(none)"] + NAMES, 1),
            (0.5, "func1_table_cuda", ["nullptr"] + NAMES, 0)]
    for y, label, cells, first in rows:
        ax.text(-0.15, y, label, ha="right", va="center", fontsize=fs.SMALL_PT, family=fs.MONO)
        for k, text in enumerate(cells):
            if k < first:
                continue
            ec = fs.GREY if text == "nullptr" else fs.BLACK
            ax.add_patch(Rectangle((k + 0.5 - w / 2, y - h / 2), w, h, fc=fs.CELL_FILL, ec=ec, lw=0.8))
            ax.text(k + 0.5, y, text, ha="center", va="center", fontsize=fs.SMALL_PT)
    for y, txt in ((2.5 + h / 2 + 0.12, "host index id = 0, 1, 2, …"), (0.5 - h / 2 - 0.12, "device index id + 1")):
        ax.text(ncell / 2 + 0.5, y, txt, ha="center", va="bottom" if y > 1 else "top", fontsize=fs.SMALL_PT,
                color=fs.GREY)
    k = 3
    ax.annotate("", xy=(k + 0.5, 1.5 + h / 2), xytext=(k + 0.5, 2.5 - h / 2),
                arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=0.9))
    ax.annotate("", xy=(k + 0.5, 0.5 + h / 2), xytext=(k + 0.5, 1.5 - h / 2),
                arrowprops=dict(arrowstyle="->", color=fs.GREEN, lw=0.9))
    return fig
