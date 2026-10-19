"""Check of the log-K equilibrium conditions and their Newton Jacobian (@sec-ch05-conditions, @sec-ch05-newton).

Mirrors, line for line, `equilibrium_max_error` and the Jacobian loop of `phase_equilibrate_tp`
(src/equilibrium/phase_equilibrate_tp.h) at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45:

    residual[j] = -log_k[j] + sum_i stoich[i][j] * (log(n_i / N_phase(i)) + [phase(i) == gas] log(p / p_std))
    jac[j][k]   = sum_i stoich[i][j] * (stoich[i][k] / n_i - phase_stoich[phase(i)][k] / N_phase(i))

with N_p the total amount of phase p and phase_stoich[p][k] the sum of stoich over the species of phase p. The
example has a gas phase, a two-species liquid and a pure solid. Needs numpy only:

    python3 newton_check.py
"""
import sys

import numpy as np

# species: gas A, gas B, gas C | liquid A_l, B_l | solid S; reactions A <=> A_l, B <=> B_l, A + B <=> C, C <=> S
PHASE = np.array([0, 0, 0, 1, 1, 2])
GAS = 0
STOICH = np.array([[-1., 0., -1., 0.],
                   [0., -1., -1., 0.],
                   [0., 0., 1., -1.],
                   [1., 0., 0., 0.],
                   [0., 1., 0., 0.],
                   [0., 0., 0., 1.]])  # species x reactions, products > 0
# composition (elements X, Z) of each species; every reaction conserves both
COMP = np.array([[1, 0], [0, 1], [1, 1], [1, 0], [0, 1], [1, 1]], dtype=float)
LOG_K = np.array([0.7, -0.3, 2.0, 0.4])
P, P_STD = 3.0e5, 1.0e5
N0 = np.array([0.6, 0.5, 0.1, 0.2, 0.3, 0.05])
# central differences with relative step 1e-6: truncation O(h^2) ~ 1e-12, round-off ~ 1e-16 * 1e1 / 1e-6 ~ 1e-9
# relative to Jacobian entries of size 1e0..1e1, so 1e-6 relative leaves margin.
H, TOL = 1e-6, 1e-6


def residual(n):
    totals = np.bincount(PHASE, weights=n)
    log_act = np.log(n / totals[PHASE]) + np.where(PHASE == GAS, np.log(P / P_STD), 0.)
    return -LOG_K + STOICH.T @ log_act


def jacobian(n):
    totals = np.bincount(PHASE, weights=n)
    phase_stoich = np.zeros((PHASE.max() + 1, STOICH.shape[1]))
    for i, p in enumerate(PHASE):
        phase_stoich[p] += STOICH[i]
    jac = np.zeros((STOICH.shape[1],) * 2)
    for j in range(STOICH.shape[1]):
        for k in range(STOICH.shape[1]):
            jac[j, k] = sum(STOICH[i, j] * (STOICH[i, k] / n[i] - phase_stoich[PHASE[i], k] / totals[PHASE[i]])
                            for i in range(len(n)))
    return jac


def check_C1_jacobian():
    """The Jacobian is the derivative of the residual with respect to the reaction extents, n = n0 + S xi."""
    fd = np.zeros((STOICH.shape[1],) * 2)
    for k in range(STOICH.shape[1]):
        d = H * STOICH[:, k] * N0.min()
        fd[:, k] = (residual(N0 + d) - residual(N0 - d)) / (2 * H * N0.min())
    err = np.max(np.abs(jacobian(N0) - fd)) / np.max(np.abs(fd))
    ok = err < TOL
    print(f"[C1] {'PASS' if ok else 'FAIL'} Jacobian equals d(residual)/d(extent): max relative difference {err:.1e}")
    return ok


def check_C2_elements():
    """Any extent step conserves every element exactly when each reaction is balanced: COMP^T S = 0."""
    balance = np.max(np.abs(COMP.T @ STOICH))
    xi = np.array([0.01, -0.02, 0.03, -0.005])
    drift = np.max(np.abs(COMP.T @ (N0 + STOICH @ xi) - COMP.T @ N0))
    ok = balance == 0. and drift < 1e-15
    print(f"[C2] {'PASS' if ok else 'FAIL'} element balance of the stoichiometry {balance:.1e}; drift of a step {drift:.1e}")
    return ok


def check_C3_pure_phase():
    """A one-species phase has activity 1 whatever its amount, so its column of the Jacobian is zero."""
    totals = np.bincount(PHASE, weights=N0)
    s_col = STOICH[5] * (1. / N0[5] - 1. / totals[2])
    ok = np.max(np.abs(s_col)) < 1e-12
    print(f"[C3] {'PASS' if ok else 'FAIL'} the pure solid contributes {np.max(np.abs(s_col)):.1e} to the Jacobian")
    return ok


def check_C4_raoult():
    """With ln K = ln(p_std / p_sat), the condition of A <=> A_l is Raoult's law x_liquid p_sat = p x_gas."""
    p_sat = P_STD / np.exp(LOG_K[0])
    n = N0.copy()
    n[0] = 0.05  # little enough gas A that the liquid mole fraction below is under 1
    x_gas = n[0] / n[PHASE == 0].sum()
    # put A_l where its condition holds, keeping B_l: x_l = p x_gas / p_sat, n_Al = x_l n_Bl / (1 - x_l)
    x_l = P * x_gas / p_sat
    n[3] = x_l * n[4] / (1. - x_l)
    r = residual(n)[0]
    ok = abs(r) < 1e-14
    print(f"[C4] {'PASS' if ok else 'FAIL'} residual of A <=> A_l at Raoult's composition {r:.1e}")
    return ok


def check_C5_tolerance():
    """Stop test max|r| <= max(log1p(ftol), 4 eps) and the reported error exp(max|r|) - 1."""
    ftol = 1e-8
    tgt64 = max(np.log1p(ftol), 4 * np.finfo(np.float64).eps)
    tgt32 = max(np.log1p(np.float32(ftol)), 4 * np.finfo(np.float32).eps)
    rep = np.expm1(tgt64)
    ok = abs(rep - ftol) < 1e-20 and abs(tgt32 - 4 * np.finfo(np.float32).eps) == 0
    print(f"[C5] {'PASS' if ok else 'FAIL'} double: target {tgt64:.3e}, reported error at the target {rep:.3e}; "
          f"single: target {tgt32:.3e} = 4 eps")
    return ok


def main():
    return sum(not f() for f in (check_C1_jacobian, check_C2_elements, check_C3_pure_phase, check_C4_raoult,
                                 check_C5_tolerance))


if __name__ == "__main__":
    sys.exit(main())
