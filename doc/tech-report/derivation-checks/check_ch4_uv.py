"""Ch. 4 checks, UV path (ThermoY, one-vapour card dry + H2O + H2O(l), h2o_ideal).

a. uv-solver kkt: final T vs independent bisection of U(T), U and water conserved;
b. uv-solver partition: same oracle, and KKT vs partition agreement;
c. partition near Tref (D6 regression);
d. oracle U(T) monotone on 150..400 K; analytic dU/dT (cf. src/thermo/equilibrate_uv.h) vs FD.
"""
import math
import os
import tempfile
import warnings

from common import version_line, kintera, torch

warnings.simplefilter("ignore")
R, TREF = 8.31446, 300.0
CVR, U0R = [2.5, 2.5, 9.0], [0.0, 0.0, -3430.0]
CARD = """reference-state: {Tref: 300., Pref: 1.e5}
dynamics: {equation-of-state: {max-iter: 10, uv-solver: SOLVER}}
species:
  - {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
  - {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
  - {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
  - {equation: H2O <=> H2O(l), type: nucleation, rate-constant: {formula: h2o_ideal}}
"""
CASES = [(280.0, 0.02), (250.0, 0.01), (320.0, 0.05)]
TMP = tempfile.mkdtemp()


def lsi(t, b, g):
    return (1 - 1 / t) * b - g * math.log(t)


def lsi_ddT(T, tr, b, g):
    return (b / (T / tr)**2 - g / (T / tr)) / tr


def h2o(T):
    return (lsi(T / 273.16, 24.845, 4.986009) if T > 273.16 else lsi(T / 273.16, 22.98, 0.52)) + math.log(611.7)


def h2o_ddT(T):
    return lsi_ddT(T, 273.16, 24.845, 4.986009) if T > 273.16 else lsi_ddT(T, 273.16, 22.98, 0.52)


def parts(T, cd, W):
    cv = min(W, math.exp(h2o(T)) / (R * T))
    return [cd, cv, W - cv]


def U_of(T, cd, W):
    return sum(R * (U0R[k] + CVR[k] * (T - TREF)) * c for k, c in enumerate(parts(T, cd, W)))


def dUdT(T, cd, W):
    c = parts(T, cd, W)
    d = sum(R * CVR[k] * c[k] for k in range(3))
    if c[1] < W:  # saturated: latent term, molar energy vapour minus cloud
        u = [R * (U0R[k] + CVR[k] * (T - TREF)) for k in range(3)]
        d += c[1] * (h2o_ddT(T) - 1 / T) * (u[1] - u[2])
    return d


def oracle(U, cd, W, lo=100.0, hi=1000.0):
    for _ in range(200):
        m = 0.5 * (lo + hi)
        lo, hi = (lo, m) if U_of(m, cd, W) > U else (m, hi)
    return 0.5 * (lo + hi)


def run(solver, T0, yv):
    path = os.path.join(TMP, f"uv_{solver}.yaml")
    with open(path, "w") as f:
        f.write(CARD.replace("SOLVER", solver))
    th = kintera.ThermoY(kintera.ThermoOptions.from_yaml(path))
    rho, y, inv_mu = torch.tensor([1.0]), torch.tensor([[yv], [0.0]]), th.buffer("inv_mu")
    V0 = th.compute("DY->V", [rho, y])
    U = th.compute("VT->U", [V0, torch.tensor([T0])])
    c0 = (V0 * inv_mu)[0]
    diag = torch.zeros(1, 1)
    th.forward(rho, U, y, False, diag)
    V1 = th.compute("DY->V", [rho, y]); c1 = (V1 * inv_mu)[0]  # noqa: E702
    T1 = th.compute("VU->T", [V1, U]).item()
    U1 = th.compute("VT->U", [V1, torch.tensor([T1])]).item()
    cd, W0, W1 = c0[0].item(), (c0[1] + c0[2]).item(), (c1[1] + c1[2]).item()
    return dict(diag=diag.item(), T=T1, To=oracle(U.item(), cd, W0), U=U.item(), U1=U1,
                dW=abs(W1 / W0 - 1), cd=cd, W=W0)


def pf(ok, expected_fail=False):
    return ("PASS (defect not reproduced)" if ok else "EXPECTED-FAIL") if expected_fail else ("PASS" if ok else "FAIL")


def check_ab():
    res = {}
    for solver, tolT, tag in [("kkt", 1e-6, "a"), ("partition", 1e-9, "b")]:
        print(f"== {tag}. uv-solver {solver}: |T - T_oracle| <= {tolT:g} K, U rel 1e-10, water rel 1e-14")
        for T0, yv in CASES:
            r = run(solver, T0, yv)
            res[solver, T0] = r["T"]
            dT, dU = abs(r["T"] - r["To"]), abs(r["U1"] / r["U"] - 1)
            print(f"  T0={T0:.0f} yv={yv}: diag={r['diag']:.0f} T={r['T']:.10f} oracle={r['To']:.10f}"
                  f" dT={dT:.1e} {pf(dT <= tolT)}; dU={dU:.1e} {pf(dU <= 1e-10)};"
                  f" dWater={r['dW']:.1e} {pf(r['dW'] <= 1e-14)}")
    print("== b. KKT vs partition final T, tol 1e-6 K")
    for T0, _ in CASES:
        d = abs(res["kkt", T0] - res["partition", T0])
        print(f"  T0={T0:.0f}: |T_kkt - T_partition|={d:.1e} {pf(d <= 1e-6)}")


def check_c():
    print("== c. partition near Tref, yv=0.05 (D6 regression): converged (diag>=0) and |dT|<=1e-9 K")
    fails = []
    for T0 in [296.0, 298.0, 299.0, 300.0, 301.0, 302.0, 304.0]:
        r = run("partition", T0, 0.05)
        dT = abs(r["T"] - r["To"])
        ok = r["diag"] >= 0 and dT <= 1e-9
        fails += [] if ok else [T0]
        print(f"  T0={T0:.0f}: diag={r['diag']:.0f} U={r['U']:.4e} T={r['T']:.8f} oracle={r['To']:.8f} dT={dT:.1e}")
    assert not fails, f"D6 regression: nonconverged or inaccurate starts {fails}"
    print(f"  failing T0: {fails} ({len(fails)}/7)  {pf(not fails)}")


def check_d():
    print("== d. oracle U(T) on 150..400 K: dU/dT > 0; analytic dU/dT vs central FD, tol 1e-7 rel")
    for T0, yv in CASES:
        r = run("kkt", T0, yv)
        cd, W = r["cd"], r["W"]
        lo, hi = 100.0, 1000.0  # saturation kink: p_sat/(R T) = W
        for _ in range(200):
            m = 0.5 * (lo + hi)
            lo, hi = (m, hi) if math.exp(h2o(m)) / (R * m) < W else (lo, m)
        Tsat, h = 0.5 * (lo + hi), 1e-3
        minslope, worst = float("inf"), 0.0
        for k in range(2501):
            T = 150.0 + 0.1 * k
            minslope = min(minslope, dUdT(T, cd, W))
            if min(abs(T - Tsat), abs(T - 273.16)) < 3 * h:
                continue
            fd = (U_of(T + h, cd, W) - U_of(T - h, cd, W)) / (2 * h)
            worst = max(worst, abs(dUdT(T, cd, W) / fd - 1))
        mono = all(U_of(150.0 + 0.1 * (k + 1), cd, W) > U_of(150.0 + 0.1 * k, cd, W) for k in range(2500))
        print(f"  case T0={T0:.0f} yv={yv} (T_sat={Tsat:.3f} K): min dU/dT={minslope:.4e} J/K/m3"
              f" {pf(minslope > 0 and mono)}; max rel(analytic/FD-1)={worst:.1e} tol 1e-7 {pf(worst <= 1e-7)}")


if __name__ == "__main__":
    print(version_line())
    check_ab(), check_c(), check_d()
