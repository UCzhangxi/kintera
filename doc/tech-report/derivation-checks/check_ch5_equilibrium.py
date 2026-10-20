"""Ch. 5 checks, chemical/phase equilibrium (EquilibriumTP, Nasa9LogK).

a. two-phase N2 + H2O(g) | H2O(l) vs analytic n_v = n_N2 p_sat / (p - p_sat);
b. Newton Jacobian J = sum nu (nu/n - nu_phase/N_phase) vs central FD of the residual;
c. 2 H2 + O2 <=> 2 H2O with Nasa9LogK at 3500 K: residual, H/O conservation,
   van 't Hoff d lnK/dT = Delta h / (R T^2) with h/RT from the bundled NASA-9 table;
d. kintera's returned gain against the Jacobian formula: at the input (max-iter 1, three-phase system of
   src/kintera_report/ch05/checks/newton_check.py), at the iterate before the last (status 0) and at the
   returned amounts (status 4);
e. a numpy copy of the iteration of phase_equilibrate_tp with a plain LU direction and no least-squares
   fallback against kintera, for a converged start and a start whose liquid must vanish (status 4): amounts,
   status, steps, error, smallest slack n - floor, and why the last halving loop rejects every scale. The amounts
   are compared to round-off: max |n_kintera - n_copy| <= 1e-14 max |n_kintera| (norm-wise relative), and each
   amount to 1e-5 of itself (the norm-wise bound alone exceeds a vanishing liquid of ~3e-15 mol), because the
   LU solves of kintera and numpy round differently on different platforms.
f. phase rule: the three-phase system of line d has N = 6 species, C = 2 elements, P = 3 phases and R = 4
   independent reactions; the residuals depend only on mole fractions within each phase, so rank J <= N - P = 3 < R
   and J is singular (P > C). Asserts sigma_min(J) < 1e-12 at the start state and over 200 random states (seed 0);
   kintera's status on it is decided by rounding (3 or 4), so it is printed, not tested;
g. reference pressure of the kinetics: K_c = k_f/k_r of O + O2 <=> O3 at 1500 K from Kinetics with the default
   Pref (101325 Pa) and with Pref = 1e5 Pa, against the 1-bar NASA-9 value; the default is low by (1e5/101325)^(-dn).
"""
import math
import os
import warnings

import numpy as np

from common import version_line, kintera, torch
from kintera import EquilibriumOptions, EquilibriumTP, nasa9_gibbs_rt
from kintera.equilibrium import Nasa9LogK

warnings.simplefilter("ignore")


def pf(ok):
    return "PASS" if ok else "FAIL"


def h2o_ideal(T):
    t = T / 273.16
    b, g = (24.845, 4.986009) if T > 273.16 else (22.98, 0.52)
    return (1 - 1 / t) * b - g * math.log(t) + math.log(611.7)


def residual(n, nu, phase, gas, P, p0, lnK):
    """sum_i nu_i ln a_i - lnK, a_i = n_i / N_phase (times P/p0 in the gas phase)."""
    tot = {}
    for ni, ph in zip(n, phase):
        tot[ph] = tot.get(ph, 0.0) + ni
    r = -lnK
    for ni, vi, ph in zip(n, nu, phase):
        la = math.log(ni / tot[ph]) + (math.log(P / p0) if ph == gas else 0.0)
        r += vi * la
    return r


def jac_formula(n, nu, phase):
    tot, dph = {}, {}
    for ni, vi, ph in zip(n, nu, phase):
        tot[ph] = tot.get(ph, 0.0) + ni
        dph[ph] = dph.get(ph, 0.0) + vi
    return sum(vi * (vi / ni - dph[ph] / tot[ph]) for ni, vi, ph in zip(n, nu, phase))


def check_ab():
    T, P, p0 = 300.0, 1.0e5, 1.0e5
    psat = math.exp(h2o_ideal(T))
    op = (EquilibriumOptions().components(["N2", "H2O", "H2O(l)"]).phases(["gas", "liquid"])
          .phase_ids([0, 0, 1]).reactions(["H2O <=> H2O(l)"]).gas_phase(0).standard_pressure(p0))
    lnK = math.log(p0 / psat)
    n0 = torch.tensor([1.0, 0.05, 0.05])
    n, gain, dg = EquilibriumTP(op)(torch.tensor(T), torch.tensor(P), n0, torch.tensor([lnK]))
    exact = 1.0 * psat / (P - psat)
    rel = abs(n[1].item() / exact - 1)
    ftol = op.ftol()
    print("== a. two-phase vapour-liquid, T=300 K, p=1e5 Pa, n0=(1, .05, .05)")
    print(f"  n_v={n[1].item():.14e} analytic={exact:.14e} rel={rel:.1e} tol 1e-10 {pf(rel <= 1e-10)}")
    print(f"  status={dg[0].item():.0f} (0 = converged) {pf(dg[0].item() == 0)}; iterations={dg[1].item():.0f};"
          f" reported error={dg[2].item():.1e} <= ftol={ftol:g} {pf(dg[2].item() <= ftol)}")
    dw = abs((n[1] + n[2]).item() / 0.1 - 1)
    print(f"  water conservation rel={dw:.1e} tol 1e-14 {pf(dw <= 1e-14)}")
    nu, phase = [0.0, -1.0, 1.0], [0, 0, 1]
    nn = [v.item() for v in n]
    J = jac_formula(nn, nu, phase)
    h = 1e-6 * nn[1]
    fd = (residual([a + h * b for a, b in zip(nn, nu)], nu, phase, 0, P, p0, lnK)
          - residual([a - h * b for a, b in zip(nn, nu)], nu, phase, 0, P, p0, lnK)) / (2 * h)
    relJ = abs(J / fd - 1)
    print("== b. Newton Jacobian at the converged state vs central FD along the reaction direction")
    print(f"  J={J:.12e} FD={fd:.12e} rel={relJ:.1e} tol 1e-8 {pf(relJ <= 1e-8)}"
          f"  (returned gain {gain.flatten()[0].item():.6e} is from the last Newton iterate)")


def nasa9_table(names):
    """Parse the bundled NASA-9 table: name line, then 20 numbers (low range 10, high range 10)."""
    path = os.path.join(os.path.dirname(kintera.__file__), "data", "nasa9.dat")
    lines = [ln.strip() for ln in open(path) if ln.strip() and not ln.startswith("#")]
    out = {}
    for k, ln in enumerate(lines):
        if ln in names:
            out[ln] = [float(v) for v in " ".join(lines[k + 1:k + 5]).split()]
    return out


def h_rt(c, T, tmid=1000.0):
    a = c[:10] if T < tmid else c[10:]
    return (-a[0] / T**2 + a[1] * math.log(T) / T + a[2] + a[3] * T / 2 + a[4] * T**2 / 3
            + a[5] * T**3 / 4 + a[6] * T**4 / 5 + a[8] / T)


def s_r(c, T, tmid=1000.0):
    a = c[:10] if T < tmid else c[10:]
    return (-a[0] / (2 * T**2) - a[1] / T + a[2] * math.log(T) + a[3] * T + a[4] * T**2 / 2
            + a[5] * T**3 / 3 + a[6] * T**4 / 4 + a[9])


def check_c():
    T, P = 3500.0, 1.0e5
    names, nu = ["H2", "O2", "H2O"], [-2.0, -1.0, 2.0]
    op = (EquilibriumOptions().components(names).phases(["gas"]).phase_ids([0, 0, 0])
          .reactions(["2 H2 + O2 <=> 2 H2O"]).gas_phase(0).standard_pressure(P))
    lk = Nasa9LogK(op)
    lnK = lk(torch.tensor(T), torch.tensor(P)).item()
    init = torch.tensor([0.6, 0.2, 0.2])
    n, _, dg = EquilibriumTP(op)(torch.tensor(T), torch.tensor(P), init, torch.tensor([lnK]))
    nn, n0 = [v.item() for v in n], init.tolist()
    r = residual(nn, nu, [0, 0, 0], 0, P, P, lnK)
    dH = abs((2 * nn[0] + 2 * nn[2]) / (2 * n0[0] + 2 * n0[2]) - 1)
    dO = abs((2 * nn[1] + nn[2]) / (2 * n0[1] + n0[2]) - 1)
    print("== c. 2 H2 + O2 <=> 2 H2O, Nasa9LogK, T=3500 K, p=p0=1e5 Pa")
    print(f"  lnK={lnK:.10f} status={dg[0].item():.0f} n={['%.6e' % v for v in nn]}")
    print(f"  |residual|={abs(r):.1e} tol 1e-10 {pf(abs(r) <= 1e-10)}")
    print(f"  H rel={dH:.1e} tol 1e-14 {pf(dH <= 1e-14)}; O rel={dO:.1e} tol 1e-14 {pf(dO <= 1e-14)}")
    tab = nasa9_table(names)
    g_tab = sum(v * (h_rt(tab[s], T) - s_r(tab[s], T)) for s, v in zip(names, nu))
    g_lib = (nasa9_gibbs_rt(torch.tensor([T]), names)[0] * torch.tensor(nu)).sum().item()
    dg_rel = abs(g_tab / g_lib - 1)
    print(f"  table parse: Delta g/RT table={g_tab:.12f} library={g_lib:.12f} rel={dg_rel:.1e}"
          f" tol 1e-12 {pf(dg_rel <= 1e-12)}")
    h = 1e-2
    fd = (lk(torch.tensor(T + h), torch.tensor(P)).item() - lk(torch.tensor(T - h), torch.tensor(P)).item()) / (2 * h)
    vh = sum(v * h_rt(tab[s], T) for s, v in zip(names, nu)) / T
    relv = abs(fd / vh - 1)
    print(f"  van 't Hoff: FD dlnK/dT={fd:.10e} Delta h/(R T^2)={vh:.10e} rel={relv:.1e} tol 1e-6 {pf(relv <= 1e-6)}")


def jac_matrix(n, stoich, phase):
    """J[j][k] = sum_i S[i][j] (S[i][k] / n_i - S_phase[phase(i)][k] / N_phase(i)), as in phase_equilibrate_tp."""
    n, stoich, phase = np.asarray(n, float), np.asarray(stoich, float), np.asarray(phase)
    tot = np.bincount(phase, weights=n)
    ps = np.zeros((phase.max() + 1, stoich.shape[1]))
    for i, p in enumerate(phase):
        ps[p] += stoich[i]
    return np.array([[sum(stoich[i, j] * (stoich[i, k] / n[i] - ps[phase[i], k] / tot[phase[i]])
                          for i in range(len(n))) for k in range(stoich.shape[1])] for j in range(stoich.shape[1])])


def residual_vec(n, stoich, phase, gas, P, p0, lnk):
    n, phase = np.asarray(n, float), np.asarray(phase)
    tot = np.bincount(phase, weights=n)
    la = np.log(n / tot[phase]) + np.where(phase == gas, math.log(P / p0), 0.0)
    return -np.asarray(lnk, float) + np.asarray(stoich, float).T @ la


WATER = dict(names=["N2", "H2O", "H2O(l)"], phases=["gas", "liquid"], pids=[0, 0, 1],
             rxns=["H2O <=> H2O(l)"], stoich=[[0.0], [-1.0], [1.0]])


def solve(card, T, P, p0, n0, lnk, max_iter=None):
    op = (EquilibriumOptions().components(card["names"]).phases(card["phases"]).phase_ids(card["pids"])
          .reactions(card["rxns"]).gas_phase(0).standard_pressure(p0))
    if max_iter is not None:
        op.max_iter(max_iter)
    n, gain, dg = EquilibriumTP(op)(torch.tensor(T), torch.tensor(P), torch.tensor(n0), torch.tensor(lnk))
    return op, n.numpy(), gain.numpy().reshape(len(lnk), len(lnk)), dg.numpy()


def water_lnk(T, p0):
    return [math.log(p0 / math.exp(h2o_ideal(T)))]


def check_d():
    print("== d. returned gain vs the Jacobian formula (kintera's gain, not a copy)")
    three = dict(names=["A", "B", "C", "A_l", "B_l", "S"], phases=["gas", "liquid", "solid"],
                 pids=[0, 0, 0, 1, 1, 2], rxns=["A <=> A_l", "B <=> B_l", "A + B <=> C", "C <=> S"],
                 stoich=[[-1, 0, -1, 0], [0, -1, -1, 0], [0, 0, 1, -1], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    n0 = [0.6, 0.5, 0.1, 0.2, 0.3, 0.05]
    _, _, gain, dg = solve(three, 300.0, 3.0e5, 1.0e5, n0, [0.7, -0.3, 2.0, 0.4], max_iter=1)
    J = jac_matrix(n0, three["stoich"], three["pids"])
    rel = np.max(np.abs(gain - J)) / np.max(np.abs(J))
    print(f"  three-phase system, max-iter 1 (gain formed at the input): max rel |gain - J(n0)|={rel:.1e}"
          f" tol 1e-14 {pf(rel <= 1e-14)}  (status {dg[0]:.0f}; J singular, P > C: line f)")
    T, P, p0 = 300.0, 1.0e5, 1.0e5
    lnk = water_lnk(T, p0)
    _, n, gain, dg = solve(WATER, T, P, p0, [1.0, 0.05, 0.05], lnk)
    k = int(dg[1])
    _, nprev, _, dgp = solve(WATER, T, P, p0, [1.0, 0.05, 0.05], lnk, max_iter=k - 1)
    jp = jac_matrix(nprev, WATER["stoich"], WATER["pids"])[0, 0]
    jn = jac_matrix(n, WATER["stoich"], WATER["pids"])[0, 0]
    rel = abs(gain[0, 0] / jp - 1)
    print(f"  water card, status {dg[0]:.0f} after {k} steps: gain={gain[0, 0]:.13e} J(iterate {k - 1}, status"
          f" {dgp[0]:.0f})={jp:.13e} rel={rel:.1e} tol 1e-14 {pf(rel <= 1e-14)}; J(returned)={jn:.13e}"
          f" rel {abs(gain[0, 0] / jn - 1):.1e}")
    _, n, gain, dg = solve(WATER, T, P, p0, [1.0, 0.01, 0.001], lnk)
    jn = jac_matrix(n, WATER["stoich"], WATER["pids"])[0, 0]
    rel = abs(gain[0, 0] / jn - 1)
    print(f"  water card, start (1, .01, .001), status {dg[0]:.0f}: gain={gain[0, 0]:.13e} J(returned)={jn:.13e}"
          f" rel={rel:.1e} tol 1e-14 {pf(rel <= 1e-14)}")


def newton_copy(n0, stoich, phase, gas, P, p0, lnk, floor, ftol, max_iter):
    """phase_equilibrate_tp with the direction from a plain LU solve and no least-squares fallback."""
    S = np.asarray(stoich, float)
    n = np.asarray(n0, float)
    target = max(math.log1p(ftol), 4.0 * np.finfo(float).eps)
    status, it, minslack, last = 2, max_iter, np.inf, (0, 0)
    for k in range(max_iter):
        err = np.max(np.abs(residual_vec(n, S, phase, gas, P, p0, lnk)))
        if err <= target:
            status, it = 0, k
            break
        J = jac_matrix(n, S, phase)
        minslack = min(minslack, np.min(n - floor))
        step = np.linalg.solve(J, -residual_vec(n, S, phase, gas, P, p0, lnk))
        scale, accepted, nfloor, nworse = 1.0, False, 0, 0
        while scale >= 1e-12:
            trial = n + scale * (S @ step)
            if np.all(np.isfinite(trial)) and np.all(trial >= 0) and np.all(trial > floor):
                if np.max(np.abs(residual_vec(trial, S, phase, gas, P, p0, lnk))) < err:
                    n, accepted = trial, True
                    break
                nworse += 1
            else:
                nfloor += 1
            scale *= 0.5
        if not accepted:
            status, it, last = 4, k, (nfloor, nworse)
            break
    err = np.max(np.abs(residual_vec(n, S, phase, gas, P, p0, lnk)))
    return n, status, it, math.exp(err) - 1.0, minslack, last


def check_e():
    print("== e. numpy copy of the iteration, plain LU direction, no least-squares fallback, vs kintera")
    T, P, p0 = 300.0, 1.0e5, 1.0e5
    lnk = water_lnk(T, p0)
    for n0 in ([1.0, 0.05, 0.05], [1.0, 0.01, 0.001]):
        op, n, _, dg = solve(WATER, T, P, p0, n0, lnk)
        m, st, it, err, minslack, last = newton_copy(n0, WATER["stoich"], WATER["pids"], 0, P, p0, lnk,
                                                     op.mole_floor(), op.ftol(), op.max_iter())
        dn = np.max(np.abs(m - n))
        dnrel = dn / np.max(np.abs(n))
        dncomp = np.max(np.abs(m - n) / np.abs(n))
        same = st == int(dg[0]) and it == int(dg[1]) and dnrel <= 1e-14 and dncomp <= 1e-5
        print(f"  start {tuple(n0)}: kintera status {dg[0]:.0f} steps {dg[1]:.0f} error {dg[2]:.3e};"
              f" copy status {st} steps {it} error {err:.3e}; max |n_kintera - n_copy|={dn:.1e} mol (rel {dnrel:.1e}, tol 1e-14; per amount {dncomp:.1e}, tol 1e-5)"
              f" {pf(same)}")
        print(f"    smallest slack n - floor along the path={minslack:.2e} mol (> 0: the fallback test"
              f" d <= 0 never holds) {pf(minslack > 0)}")
        if st == 4:
            print(f"    returned liquid={n[2]:.3e} mol; last halving loop: {last[0]} scales rejected by the floor"
                  f" test, {last[1]} by no decrease of max|r| (INFO)")


THREE = dict(names=["A", "B", "C", "A_l", "B_l", "S"], phases=["gas", "liquid", "solid"], pids=[0, 0, 0, 1, 1, 2],
             rxns=["A <=> A_l", "B <=> B_l", "A + B <=> C", "C <=> S"],
             stoich=[[-1, 0, -1, 0], [0, -1, -1, 0], [0, 0, 1, -1], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])


def check_f():
    print("== f. phase rule P <= C: three-phase system of line d (N=6, C=2, P=3, R=4), J singular")
    n0 = [0.6, 0.5, 0.1, 0.2, 0.3, 0.05]
    S = np.asarray(THREE["stoich"], float)
    print(f"  rank S={np.linalg.matrix_rank(S)} (reactions independent), N - P = {6 - 3}")
    sv = np.linalg.svd(jac_matrix(n0, S, THREE["pids"]), compute_uv=False)
    print(f"  start state: sigma_min(J)={sv[-1]:.1e} sigma_max={sv[0]:.3e} cond={sv[0] / sv[-1]:.1e}"
          f" rank={np.linalg.matrix_rank(jac_matrix(n0, S, THREE['pids']))} tol 1e-12 {pf(sv[-1] < 1e-12)}")
    rng = np.random.default_rng(0)
    worst = max(np.linalg.svd(jac_matrix(rng.uniform(0.01, 1.0, 6), S, THREE["pids"]), compute_uv=False)[-1]
                for _ in range(200))
    print(f"  200 random states (seed 0, amounts 0.01..1 mol): max sigma_min(J)={worst:.1e} tol 1e-12 {pf(worst < 1e-12)}")
    st = []
    for mi in (1, None):
        _, _, _, dg = solve(THREE, 300.0, 3.0e5, 1.0e5, n0, [0.7, -0.3, 2.0, 0.4], max_iter=mi)
        st.append(f"max-iter {mi or 'default'}: status {dg[0]:.0f} after {dg[1]:.0f} steps")
    print(f"  kintera on it: {'; '.join(st)} (INFO: status 3 or 4 is decided by rounding)")


def check_g():
    print("== g. kinetics reference pressure: K_c of O + O2 <=> O3 at 1500 K (dn = -1)")
    import tempfile
    T, R = 1500.0, 8.31446
    tmp = tempfile.mkdtemp(prefix="ch5g_")

    def kc(ref):
        card = (f"reference-state: {ref}\nspecies:\n" + "".join(
            f"  - {{name: {n}, composition: {{{c}}}, cv_R: 2.5}}\n"
            for n, c in [("N2", "N: 2"), ("O", "O: 1"), ("O2", "O: 2"), ("O3", "O: 3")])
            + "reactions:\n  - equation: O + O2 <=> O3\n    type: arrhenius\n"
            "    rate-constant: {A: 1.7e-14, b: -2.4, Ea_R: 0.}\n")
        path = os.path.join(tmp, "k.yaml")
        with open(path, "w") as f:
            f.write(card)
        op = kintera.KineticsOptions.from_yaml(path)
        kin = kintera.Kinetics(op)
        cc = torch.ones(1, len(op.species()))
        rate, _, _, kf = kin.forward_with_rate_constants(torch.tensor([T]), torch.tensor([1.0e5]), cc)
        return kf[0, 0].item() / rate[0, 1].item(), op.Pref()

    k_def, p_def = kc("{Tref: 300.}")
    k_bar, p_bar = kc("{Tref: 300., Pref: 1.e5}")
    g = nasa9_gibbs_rt(torch.tensor([T]), ["O", "O2", "O3"])[0]
    k_ref = math.exp(-(g[2] - g[0] - g[1]).item()) * (1.0e5 / (R * T)) ** (-1)
    r_bar = abs(k_bar / k_ref - 1)
    print(f"  Pref={p_bar:.0f} Pa: K_c={k_bar:.10e} vs 1-bar NASA-9 {k_ref:.10e} rel={r_bar:.1e} tol 1e-12 {pf(r_bar <= 1e-12)}")
    want = (1.0e5 / p_def) ** 1
    r_def = abs((k_def / k_bar) / want - 1)
    print(f"  default Pref={p_def:.0f} Pa: K_c/K_c(1 bar)={k_def / k_bar:.6f}, i.e. {k_def / k_bar - 1:.4e}; expected"
          f" (1e5/Pref)^(-dn)={want:.6f}, rel={r_def:.1e} tol 1e-12 {pf(r_def <= 1e-12)}")


if __name__ == "__main__":
    print(version_line())
    check_ab()
    check_c()
    check_d()
    check_e()
    check_f()
    check_g()
