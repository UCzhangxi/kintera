"""Ch. 1b (parcel model, state section): amounts, fractions and conserved budgets on the TP path.

a. Algebra, no kintera: balanced A + B -> C (element E_A in A and C), starting mole fractions (0.4, 0.3, 0.3), extent
   0.1 mol per mole of parcel. The amount of E_A is conserved exactly; the element-weighted mole fraction is not,
   because the reaction changes the number of moles (INFO, the size of the change).
b. kintera TP path: ThermoX.forward on tests/jupiter.yaml (max_iter 100, T = 160, 200, 250 K, p = 1e5 Pa). Amounts
   are recovered per mole of dry gas, N_i = x_i / x_dry (the dry species is in no reaction). Gated:
   - every cell converged (diag >= 0) and at least one cell has condensate;
   - the amount change is a combination of the stoichiometric columns, |dN - S xi| / |dN|, with xi_r the change of
     the condensed product of reaction r;
   - element/dry ratios O, N, S are unchanged (relative).
   INFO: the change of the element-weighted mole fractions (nonzero where NH3 + H2S -> NH4SH(s) changes the number of
   moles), the relative change of the gas volume at fixed T and p, and the fixed-T energy change per mole of dry gas,
   sum_i u_i dN_i = -sum_r L_r xi_r with the linear energies of the deck (u_i = R (u0_i + cv_i (T - 300 K))).
"""
import math
import sys

from common import thermo_x, species, jupiter_x, version_line, torch

R = 8.31446
RES = []
TOL_SPAN, TOL_ELEM = 1e-12, 1e-14
# atoms of O, N, S per species of tests/jupiter.yaml
ATOMS = {"H2O": (1, 0, 0), "NH3": (0, 1, 0), "H2S": (0, 0, 1), "H2O(l)": (1, 0, 0), "H2O(l,p)": (1, 0, 0),
         "NH3(s)": (0, 1, 0), "NH3(s,p)": (0, 1, 0), "NH4SH(s)": (0, 1, 1)}
# linear energies of tests/jupiter.yaml (Tref 300 K)
CV = {"dry": 2.5, "H2O": 2.5, "NH3": 2.5, "H2S": 2.5, "H2O(l)": 9.0, "H2O(l,p)": 9.0, "NH3(s)": 9.6,
      "NH3(s,p)": 9.6, "NH4SH(s)": 9.6}
U0 = {"dry": 0., "H2O": 0., "NH3": 0., "H2S": 0., "H2O(l)": -3430., "H2O(l,p)": -3430., "NH3(s)": -5520.,
      "NH3(s,p)": -5520., "NH4SH(s)": -1.2e4}


def worst_of(a, b):
    """max that propagates NaN: Python's max(0.0, nan) is 0.0, which would hide a NaN and let the line PASS."""
    return a if a != a else (b if b != b else max(a, b))


def report(name, val, tol, ok, tag=None):
    tag = tag or ("PASS" if ok and math.isfinite(val) else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}")


def info(name, val):
    RES.append("INFO")
    print(f"{name}: {val:.6e}  INFO")


def check_algebra():
    x0 = [0.4, 0.3, 0.3]                      # A, B, C
    S = [-1.0, -1.0, 1.0]
    xi = 0.1
    N = [x0[i] + S[i] * xi for i in range(3)]  # amounts, per mole of the starting parcel
    a = [1, 0, 1]                             # atoms of E_A in A, B, C
    amount0, amount1 = sum(a[i] * x0[i] for i in range(3)), sum(a[i] * N[i] for i in range(3))
    frac1 = amount1 / sum(N)                  # element-weighted mole fraction after renormalization
    print(f"(a) A + B -> C: E_A amount {amount0:.10f} -> {amount1:.10f}; element-weighted fraction "
          f"{amount0:.10f} -> {frac1:.10f}")
    report("(a) E_A amount change", abs(amount1 - amount0), 1e-15, abs(amount1 - amount0) <= 1e-15)
    info("(a) E_A element-weighted mole fraction change (not a conserved quantity)", frac1 - amount0)


def check_tp():
    op, th = thermo_x(max_iter=100)
    sp = species(op)
    Ts = torch.tensor([160., 200., 250.])
    _, x = jupiter_x(op, n=len(Ts))
    x0 = x.clone()
    P = torch.full_like(Ts, 1e5)
    diag = torch.zeros(len(Ts), 1)
    th.forward(Ts, P, x, diag=diag)
    S = th.buffer("stoich")                    # species x reactions
    ngas = len(op.vapor_ids())
    idry = sp.index("dry")
    clouds = [i for i, s in enumerate(sp) if i >= ngas]
    nfail = int((diag < 0).sum())
    ncloud = int((x[:, clouds] > 0).any(-1).sum())
    report("(b) cells not converged (diag < 0) at max_iter 100", float(nfail), 0, nfail == 0)
    RES.append("PASS" if ncloud > 0 else "FAIL")
    print(f"(b) cells with condensate: {ncloud} of {len(Ts)} (must be > 0)  {RES[-1]}")
    # the one condensed product of each reaction column (S > 0 on a cloud species)
    prod = [next(i for i in clouds if S[i, r] > 0) for r in range(S.shape[1])]
    A = torch.tensor([[ATOMS.get(s, (0, 0, 0))[e] for s in sp] for e in range(3)], dtype=x.dtype)
    worst_span, worst_elem, worst_frac = 0.0, 0.0, 0.0
    for k in range(len(Ts)):
        N0, N1 = x0[k] / x0[k, idry], x[k] / x[k, idry]
        dN = N1 - N0
        xi = dN[prod]                          # each reaction's extent is the change of its own condensate
        nrm = dN.norm().item()
        span = ((dN - S @ xi).norm() / dN.norm()).item() if nrm > 0 else (0.0 if nrm == 0 else float("nan"))
        e0, e1 = A @ N0, A @ N1                # element per mole of dry gas
        elem = ((e1 - e0).abs() / e0).max().item()
        f0, f1 = A @ x0[k], A @ x[k]           # element-weighted mole fractions
        frac = ((f1 - f0).abs() / f0).max().item()
        T = Ts[k].item()
        u = torch.tensor([R * (U0[s] + CV[s] * (T - 300.0)) for s in sp], dtype=x.dtype)
        dU = (u * dN).sum().item()
        L = -(S.T @ u)
        dV = (dN[:ngas].sum() / N0[:ngas].sum()).item()
        print(f"   T={T:.0f}: diag={diag[k].item():.0f} xi={[round(v, 8) for v in xi.tolist()]}; |dN - S xi|/|dN| "
              f"{span:.2e}; element/dry {elem:.2e}; element-weighted fraction {frac:.2e}; dV/V {dV:+.3e}; "
              f"sum u dN {dU:+.6e} J, -sum L xi {-(L * xi).sum().item():+.6e} J per mol dry")
        worst_span, worst_elem = worst_of(worst_span, span), worst_of(worst_elem, elem)
        worst_frac = worst_of(worst_frac, frac)
    report("(b) worst |dN - S xi| / |dN| (amounts per mole of dry gas)", worst_span, TOL_SPAN, worst_span <= TOL_SPAN)
    report("(b) worst element/dry ratio change O, N, S (rel)", worst_elem, TOL_ELEM, worst_elem <= TOL_ELEM)
    info("(b) worst element-weighted mole fraction change O, N, S (rel; not a conserved quantity)", worst_frac)


if __name__ == "__main__":
    print(version_line())
    check_algebra()
    check_tp()
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "INFO")))
    sys.exit(1 if "FAIL" in RES else 0)
