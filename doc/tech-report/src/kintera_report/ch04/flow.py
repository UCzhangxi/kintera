"""Chapter 4 helper: a left-to-right flow cartoon of labelled boxes joined by arrows (STYLE 6: no axes frame)."""
from matplotlib.patches import FancyBboxPatch

from kintera_report import figstyle as fs


def flow(steps, notes=(), height=1.6, loop_back=None):
    """steps: box labels, left to right; notes: (index, text) placed under a box in grey; loop_back: (i, j, text)
    draws a return arrow above the boxes from box i to box j."""
    fig, ax = fs.new_figure("double", height)
    ax.set_axis_off()
    n = len(steps)
    ax.set_xlim(0.0, n)
    ax.set_ylim(-0.62, 1.18)
    w, h = 0.92, 0.62
    for k, text in enumerate(steps):
        ax.add_patch(FancyBboxPatch((k + 0.5 - w / 2, 0.25 - h / 2), w, h, boxstyle="round,pad=0.02",
                                    fc=fs.CELL_FILL, ec=fs.BLACK, lw=0.8))
        ax.text(k + 0.5, 0.25, text, ha="center", va="center", fontsize=fs.SMALL_PT)
        if k + 1 < n:
            ax.annotate("", xy=(k + 1.5 - w / 2, 0.25), xytext=(k + 0.5 + w / 2, 0.25),
                        arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=0.9, shrinkA=0, shrinkB=0))
    for k, text in notes:
        ax.text(k + 0.5, -0.32, text, ha="center", va="top", fontsize=fs.SMALL_PT, color=fs.GREY)
    if loop_back is not None:
        i, j, text = loop_back
        ax.annotate("", xy=(j + 0.5, 0.25 + h / 2), xytext=(i + 0.5, 0.25 + h / 2),
                    arrowprops=dict(arrowstyle="->", color=fs.GREEN, lw=0.9, connectionstyle="arc3,rad=0.35"))
        ax.text((i + j) / 2 + 0.5, 1.17, text, ha="center", va="top", fontsize=fs.SMALL_PT, color=fs.GREEN)
    return fig
