"""One iteration of `phase_equilibrate_tp` (@sec-ch05-newton), as read from src/equilibrium/phase_equilibrate_tp.h
at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45. No data file."""
from kintera_report import figstyle as fs
from kintera_report.ch04.flow import flow


def make_fig():
    fig = flow(["residuals; stop\nif max |r| ≤ target", "Jacobian in\nreaction extents", "bounded\nNewton step",
                "halve until\nerror falls"],
               notes=[(0, "status 0"), (2, "fails: status 3"), (3, "no decrease:\nstatus 4")], height=1.9)
    ax = fig.axes[0]
    top = 0.25 + 0.62 / 2  # upper edge of the boxes drawn by flow()
    ax.annotate("", xy=(0.5, top), xytext=(3.5, top),
                arrowprops=dict(arrowstyle="->", color=fs.GREEN, lw=0.9, connectionstyle="arc3,rad=0.18"))
    ax.text(2.0, 1.0, "accept; repeat up to max-iter (status 2)", ha="center", va="bottom",
            fontsize=fs.SMALL_PT, color=fs.GREEN)
    return fig
