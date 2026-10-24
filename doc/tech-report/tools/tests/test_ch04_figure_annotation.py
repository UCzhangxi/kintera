"""The converged UV residual scale must still produce a usable raster figure."""
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from kintera_report.ch04.figures.fig_uv_partition import make_fig


def test_converged_uv_figure_renders_with_reference_label_inside_axes():
    fig = make_fig()
    try:
        output = BytesIO()
        fig.savefig(output, format='png', dpi=100)
        assert output.getvalue().startswith(b'\x89PNG')
        ax = fig.axes[0]
        label = next(t for t in ax.texts if t.get_text() == 'Tref')
        x, y = label.get_transform().transform(label.get_position())
        assert ax.bbox.contains(x, y), 'reference label is outside the plotted panel'
    finally:
        plt.close(fig)
