"""Check of the weight row of the fixed-energy saturation step (@sec-ch04-equilibrate-uv, @eq-ch04-equilibrate-uv-weight).

Mirrors, line for line, the weight row of `equilibrate_uv` (src/thermo/equilibrate_uv.h, the loop that fills
`weight` for an active reaction) at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45:

    weight[r][i] = logsvp_ddT[r] * intEng[i] / heat_capacity            (every species i)
                 + nu[i][r] / conc[i]                                    (gases i of reaction r)

with nu = -stoich (positive for a species the reaction consumes), heat_capacity = sum_i intEng_ddT[i] * conc[i],
and logsvp the concentration-unit constant ln K'_r(T) = ln K_r(T) - (sum_{gas} nu) ln(R T). The claims are checked
against central finite differences of the saturation residual F_r = sum_{gas} nu ln c - ln K'_r(T(c)), with T(c)
the temperature that keeps the internal energy per volume U = sum_i u_i(T) c_i fixed. Needs numpy only:

    python3 equilibrate_uv_check.py
"""
import sys

import numpy as np

R = 8.31446261815324
# species: dry gas, vapour A, vapour B, condensate A(s), condensate AB(s); reactions A <=> A(s), A + B <=> AB(s)
NGAS = 3
STOICH = np.array([[0., 0.], [-1., -1.], [0., -1.], [1., 0.], [0., 1.]])  # species x reactions, products > 0
CV = R * np.array([2.5, 3.0, 3.5, 4.0, 7.0])                              # J/mol/K
U0 = R * np.array([0.0, 0.0, 0.0, -3000.0, -9000.0])                      # J/mol, energy at T = 0
LNK_A = np.array([25.0, 60.0])                                            # ln K_r(T) = a - b / T, K in Pa^m
LNK_B = np.array([5000.0, 12000.0])
C = np.array([30.0, 0.4, 0.2, 0.05, 0.03])                                # mol/m^3
T0 = 260.0
NU = -STOICH
# The relative step of the central differences, and the tolerance: with h = 1e-6 the truncation error is
# O(h^2) ~ 1e-12 and the round-off of F (terms of size 1e1, double) divided by h is ~ 1e-15 * 1e1 / 1e-6 ~ 1e-8
# relative to entries of size 1e0..1e2, so 1e-6 relative leaves two digits of margin.
H, TOL = 1e-6, 1e-6


def u(T):
    return U0 + CV * T


def temperature(c, U):
    return (U - U0 @ c) / (CV @ c)                       # U = sum (u0 + cv T) c, constant cv


def lnk_prime(T):
    return LNK_A - LNK_B / T - NU[:NGAS].sum(0) * np.log(R * T)


def lnk_prime_ddT(T):
    return LNK_B / T**2 - NU[:NGAS].sum(0) / T


def residual(c, U):
    return NU[:NGAS].T @ np.log(c[:NGAS]) - lnk_prime(temperature(c, U))


def weight(c, T):
    """The code's row: logsvp_ddT * intEng / heat_capacity + nu / conc on the gases."""
    heat_capacity = CV @ c
    w = np.outer(lnk_prime_ddT(T), u(T)) / heat_capacity
    for r in range(STOICH.shape[1]):
        for i in range(NGAS):
            if NU[i, r] != 0.:
                w[r, i] += NU[i, r] / c[i]
    return w


def fd_jacobian(c, U):
    jac = np.zeros((STOICH.shape[1], len(c)))
    for i in range(len(c)):
        dc = np.zeros_like(c)
        dc[i] = H * c[i]
        jac[:, i] = (residual(c + dc, U) - residual(c - dc, U)) / (2 * dc[i])
    return jac


def check_C1_weight_row():
    U = u(T0) @ C
    w, fd = weight(C, T0), fd_jacobian(C, U)
    err = np.max(np.abs(w - fd)) / np.max(np.abs(fd))
    ok = err < TOL
    print(f"[C1] {'PASS' if ok else 'FAIL'} weight row equals dF/dc at fixed U: max relative difference {err:.1e}")
    return ok


def check_C2_temperature_change():
    U = u(T0) @ C
    dT_code = -u(T0) / (CV @ C)                         # dT/dc_i = -u_i / C_V
    dT_fd = np.array([(temperature(C + d, U) - temperature(C - d, U)) / (2 * d[i])
                      for i, d in enumerate(np.diag(H * C))])
    err = np.max(np.abs(dT_code - dT_fd)) / np.max(np.abs(dT_fd))
    ok = err < TOL
    print(f"[C2] {'PASS' if ok else 'FAIL'} dT/dc_i = -u_i/C_V at fixed U: max relative difference {err:.1e}")
    return ok


def check_C3_coupling_term_matters():
    """Without the coupling term (gas terms only) the row misses the condensate weights and most of the gain."""
    U = u(T0) @ C
    w, fd = weight(C, T0), fd_jacobian(C, U)
    gas_only = np.zeros_like(w)
    gas_only[:, :NGAS] = (NU[:NGAS] / C[:NGAS, None]).T
    gain, gain_gas = w @ STOICH, gas_only @ STOICH
    cond = np.max(np.abs(fd[:, NGAS:]))
    rel = np.max(np.abs(gain - gain_gas)) / np.max(np.abs(gain))
    ok = cond > 1e-3 and rel > 1e-2
    print(f"[C3] {'PASS' if ok else 'FAIL'} condensate weights are non-zero (largest {cond:.3g} m^3/mol) and "
          f"dropping the coupling term changes the gain by {rel:.2f} of its largest entry")
    return ok


def check_C4_latent_heat_form():
    """(W S)_rk = sum_n nu_nr nu_nk / c_n (signed) - (d ln K'_r/dT) L_k / C_V, with L_k = -sum_n nu_nk u_n."""
    gain = weight(C, T0) @ STOICH
    latent = -STOICH.T @ u(T0)
    gas = np.array([[sum(NU[n, r] * STOICH[n, k] / C[n] for n in range(NGAS)) for k in range(2)] for r in range(2)])
    form = gas - np.outer(lnk_prime_ddT(T0), latent) / (CV @ C)
    err = np.max(np.abs(gain - form)) / np.max(np.abs(gain))
    ok = err < 1e-13  # same arithmetic in another order: a few ulps of entries of size 1e1
    print(f"[C4] {'PASS' if ok else 'FAIL'} gain = gas part - (d ln K'/dT) L / C_V: max relative difference {err:.1e}")
    return ok


def main():
    fails = sum(not f() for f in (check_C1_weight_row, check_C2_temperature_change, check_C3_coupling_term_matters,
                                  check_C4_latent_heat_form))
    return fails


if __name__ == "__main__":
    sys.exit(main())
