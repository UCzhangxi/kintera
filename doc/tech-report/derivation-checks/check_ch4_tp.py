"""Ch. 4 checks, TP path (ThermoX on tests/jupiter.yaml).

a. complementarity of the converged state against an independent copy of the
   saturation laws (src/vapors/vapor_functions.h) + element conservation;
b. TP gain matrix vs a finite difference of Lambda = ln(x_v / x_g) along H2O -> H2O(l);
c. default max-iter (known defect D4) on cold-start cells, then max-iter 100.
"""
import math
import warnings

from common import thermo_x, species, version_line, torch

warnings.simplefilter("ignore")
P = 1.0e5


def lsi(t, b, g):
    return (1 - 1 / t) * b - g * math.log(t)


def h2o_ideal(T):
    return (lsi(T / 273.16, 24.845, 4.986009) if T > 273.16 else lsi(T / 273.16, 22.98, 0.52)) + math.log(611.7)


def nh3_ideal(T):
    return (lsi(T / 195.4, 20.08, 5.62) if T > 195.4 else lsi(T / 195.4, 20.64, 1.43)) + math.log(6060.0)


def nh3_h2s_lewis(T):
    return (14.82 - 4705.0 / T) * math.log(10.0) + 2 * math.log(101325.0)


def verdict(ok, expected_fail=False):
    if expected_fail:
        return "EXPECTED-FAIL" if not ok else "PASS (defect not reproduced)"
    return "PASS" if ok else "FAIL"


def initial(sp, n=1):
    x = torch.zeros(n, len(sp))
    x[:, 0], x[:, sp.index("H2O")], x[:, sp.index("NH3")], x[:, sp.index("H2S")] = .97, .02, .005, .005
    return x


def solve(th, sp, Ts):
    Ts = torch.as_tensor(Ts, dtype=torch.float64)
    x = initial(sp, len(Ts))
    x0 = x.clone()
    diag = torch.zeros(len(Ts), 1)
    gain = th.forward(Ts, torch.full((len(Ts),), P), x, False, diag)
    return x0, x, gain, diag[:, 0]


def check_a_b():
    op, th = thermo_x(max_iter=100)
    sp = species(op)
    i = {s: sp.index(s) for s in sp}
    nr = len(op.reactions())
    elem = {"O": (["H2O", "H2O(l)", "H2O(l,p)"], [1, 1, 1]),
            "N": (["NH3", "NH3(s)", "NH3(s,p)", "NH4SH(s)"], [1, 1, 1, 1]),
            "S": (["H2S", "NH4SH(s)"], [1, 1])}
    print("== a. complementarity (|res|<=1e-6 if condensate present, res<0 if absent); elements 1e-14")
    print("== b. TP gain[H2O,H2O] vs central FD of ln(x_H2O/x_g) along H2O->H2O(l), tol 1e-7 rel")
    for T in [300.0, 250.0, 200.0, 160.0]:
        x0, x, gain, diag = solve(th, sp, [T])
        v, v0 = x[0], x0[0]
        xg = v[:4].sum().item()
        lnp = {s: math.log(v[i[s]].item() / xg * P) for s in ["H2O", "NH3", "H2S"]}
        res = [lnp["H2O"] - h2o_ideal(T), lnp["NH3"] - nh3_ideal(T),
               lnp["NH3"] + lnp["H2S"] - nh3_h2s_lewis(T)]
        clouds = [v[i[c]].item() for c in ["H2O(l)", "NH3(s)", "NH4SH(s)"]]
        print(f"T={T:.0f} K  diag={diag.item():.0f}")
        for name, r, c in zip(["H2O->H2O(l)", "NH3->NH3(s)", "NH3+H2S->NH4SH(s)"], res, clouds):
            ok = abs(r) <= 1e-6 if c > 0 else r < 0
            tol = "|res|<=1e-6" if c > 0 else "res<0"
            print(f"  a {name:18s} cloud={c:.3e} res={r:+.3e}  tol {tol:12s} {verdict(ok)}")
        for e, (names, w) in elem.items():
            r1 = sum(wk * v[i[s]].item() for s, wk in zip(names, w)) / v[0].item()
            r0 = sum(wk * v0[i[s]].item() for s, wk in zip(names, w)) / v0[0].item()
            d = abs(r1 / r0 - 1)
            print(f"  a element {e}/dry rel change={d:.1e}  tol 1e-14 {verdict(d <= 1e-14)}")
        if clouds[0] > 0:
            g = gain.reshape(-1, nr, nr)[0, 0, 0].item()
            step = torch.zeros(len(sp))
            step[i["H2O"]], step[i["H2O(l)"]] = -1.0, 1.0
            h = 1e-6 * v[i["H2O"]].item()

            def lam(w):
                return math.log(w[i["H2O"]].item() / w[:4].sum().item())
            fd = (lam(v + h * step) - lam(v - h * step)) / (2 * h)
            rel = abs(g / fd - 1)
            no_term = -1.0 / v[i["H2O"]].item()
            print(f"  b gain={g:.10e} FD={fd:.10e} rel={rel:.1e} tol 1e-7 {verdict(rel <= 1e-7)}"
                  f"; without -sum(nu)/x_g: {no_term:.6e} (rel {abs(no_term / fd - 1):.1e})")


def check_c():
    print("== c. default max-iter on cold-start cells 130..250 K (known defect D4)")
    Ts = torch.linspace(130, 250, 13)
    op, th = thermo_x()
    _, _, _, diag = solve(th, species(op), Ts)
    bad = int((diag < 0).sum())
    print(f"  max-iter={op.max_iter()} (default): non-converged {bad}/{len(Ts)}; diag={[int(d) for d in diag]}"
          f"  tol 0  {verdict(bad == 0, expected_fail=True)}")
    op, th = thermo_x(max_iter=100)
    _, _, _, diag = solve(th, species(op), Ts)
    bad = int((diag < 0).sum())
    print(f"  max-iter=100: non-converged {bad}/{len(Ts)}; iterations={[int(d) for d in diag]}"
          f"  tol 0  {verdict(bad == 0)}")


if __name__ == "__main__":
    print(version_line())
    check_a_b()
    check_c()
