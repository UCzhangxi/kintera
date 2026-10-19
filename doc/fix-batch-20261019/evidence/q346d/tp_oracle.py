"""Independent TP equilibrium oracle for tests/jupiter.yaml (3 nucleation reactions).

Reactions: (1) H2O -> H2O(l) [h2o_ideal], (2) NH3 -> NH3(s) [nh3_ideal],
(3) NH3 + H2S -> NH4SH(s) [nh3_h2s_lewis]. Fixed T and P, ideal gas,
p_i = (n_i / n_gas) P. Brute force: for each of the 8 active subsets solve the
equalities by damped Newton in the extents, keep the feasible solution
(amounts >= 0, inactive reactions not supersaturated). The svp formulas are
re-typed from src/vapors/vapor_functions.h at 0d9f67f.
Also reports the residual r_j = sum(a ln p) - ln svp_j of any given state.
"""
import itertools
import math

import numpy as np


def logsvp_ideal(t, beta, gamma):
    return (1.0 - 1.0 / t) * beta - gamma * math.log(t)


def h2o_ideal(T):
    tr, pr = 273.16, 611.7
    return (logsvp_ideal(T / tr, 24.845, 4.986009) if T > tr
            else logsvp_ideal(T / tr, 22.98, 0.52)) + math.log(pr)


def nh3_ideal(T):
    tr, pr = 195.4, 6060.0
    return (logsvp_ideal(T / tr, 20.08, 5.62) if T > tr
            else logsvp_ideal(T / tr, 20.64, 1.43)) + math.log(pr)


def nh3_h2s_lewis(T):
    return (14.82 - 4705.0 / T) * math.log(10.0) + 2.0 * math.log(101325.0)


# species order: dry, H2O, NH3, H2S, H2O(l), NH3(s), NH4SH(s)
S = np.array([  # rows species, cols reactions
    [0, 0, 0],
    [-1, 0, 0],
    [0, -1, -1],
    [0, 0, -1],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
], dtype=float)
NGAS = 4


def residuals(n, T, P):
    ng = n[:NGAS].sum()
    lnp = np.log(np.maximum(n[:NGAS], 1e-300) / ng * P)
    lsvp = np.array([h2o_ideal(T), nh3_ideal(T), nh3_h2s_lewis(T)])
    a = -S[:NGAS]
    return a.T @ lnp - lsvp


def solve(n0, T, P):
    """Enumerate active sets; for each, the equalities give the vapour amounts in
    closed form for a given gas total n_g, and n_g is iterated to a fixed point."""
    L = np.array([h2o_ideal(T), nh3_ideal(T), nh3_h2s_lewis(T)])
    e1, e2, e3 = np.exp(L - np.array([1, 1, 2]) * math.log(P))
    for act in itertools.product([0, 1], repeat=3):
        a1, a2, a3 = act
        ng = n0[:NGAS].sum()
        for _ in range(500):
            v1 = ng * e1 if a1 else n0[1]
            if a2 and a3:
                v2 = ng * e2
                v3 = ng * ng * e3 / v2
            elif a2:
                v2, v3 = ng * e2, n0[3]
            elif a3:
                # (n2_0 - n3_0 + v3) v3 = ng^2 e3
                b = n0[2] - n0[3]
                c = ng * ng * e3
                v3 = 2 * c / (b + math.sqrt(b * b + 4 * c)) if b > 0 else (-b + math.sqrt(b * b + 4 * c)) / 2
                v2 = n0[2] - n0[3] + v3
            else:
                v2, v3 = n0[2], n0[3]
            ng_new = n0[0] + v1 + v2 + v3
            if abs(ng_new - ng) < 1e-16:
                ng = ng_new
                break
            ng = ng_new
        nh4sh = n0[3] - v3
        n = np.array([n0[0], v1, v2, v3, n0[1] - v1, n0[2] - v2 - nh4sh, nh4sh])
        if np.any(n[:NGAS] <= 0):
            continue
        r = residuals(n, T, P)
        if np.all(n >= -1e-15) and all(
                act[j] or r[j] <= 1e-9 for j in range(3)) and all(
                not act[j] or n[NGAS + j] >= -1e-15 for j in range(3)):
            return act, n, r
    return None
