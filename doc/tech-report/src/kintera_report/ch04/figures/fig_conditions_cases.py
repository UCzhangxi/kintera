"""Cartoon of the three cases of the saturation conditions of chapter 4 (@sec-ch04-conditions).

A saturation curve ln K(T) with three states: on the curve with condensate present (equilibrium), above it
(supersaturated, vapour condenses back to the curve) and below it without condensate (subsaturated, allowed).
No data file: the curve is a schematic Clausius-Clapeyron shape, not a kintera fit. Mirrors the complementarity
conditions of src/thermo/equilibrate_tp.h `equilibrate_tp` at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45.
"""
import numpy as np

from kintera_report import figstyle as fs


def make_fig():
    fig, ax = fs.new_figure("single", 3.4)
    T = np.linspace(0.0, 1.0, 200)
    curve = 2.6 * T - 0.9 * T ** 2
    ax.plot(T, curve, color=fs.BLUE, label="saturation curve $\\ln K(T)$")
    ax.plot([0.45], [2.6 * 0.45 - 0.9 * 0.45 ** 2], "o", color=fs.GREEN, label="condensate present, on curve")
    xs, ys = 0.75, 2.6 * 0.75 - 0.9 * 0.75 ** 2 + 0.55
    ax.plot([xs], [ys], "^", color=fs.VERMILLION, label="supersaturated: condenses")
    ax.annotate("", xy=(xs, ys - 0.5), xytext=(xs, ys - 0.06),
                arrowprops=dict(arrowstyle="->", color=fs.VERMILLION, lw=1.0))
    ax.plot([0.25], [2.6 * 0.25 - 0.9 * 0.25 ** 2 - 0.45], "s", color=fs.BLACK,
            label="no condensate, below curve: allowed")
    ax.set_xlabel("temperature $T$ (schematic)")
    ax.set_ylabel("gas quotient, log (schematic)")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=fs.SMALL_PT)
    return fig
