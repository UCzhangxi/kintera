"""Ch.3 species functions: Cp = dH/dT, Cp - Cv, EOS, relative humidity (jupiter.yaml)."""
import math

from common import thermo_x, species, jupiter_x, version_line, DECK, kintera, torch

R = 8.31446  # kintera Rgas (constants.h)
RES = []


def report(name, val, tol, ok, tag=None):
    tag = tag or ("PASS" if ok else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}")


def logsvp_ideal(t, beta, gamma):
    return (1.0 - 1.0 / t) * beta - gamma * math.log(t)


def h2o_ideal(T):  # independent copy of vapor_functions.h
    tr, pr = 273.16, 611.7
    return (logsvp_ideal(T / tr, 24.845, 4.986009) if T > tr
            else logsvp_ideal(T / tr, 22.98, 0.52)) + math.log(pr)


def nh3_ideal(T):
    tr, pr = 195.4, 6060.0
    return (logsvp_ideal(T / tr, 20.08, 5.62) if T > tr
            else logsvp_ideal(T / tr, 20.64, 1.43)) + math.log(pr)


def nh3_h2s_lewis(T):
    return (14.82 - 4705.0 / T) * math.log(10.0) + 2.0 * math.log(101325.0)


def check_cp_fd(op, th):
    sp, x = jupiter_x(op)
    T, p = torch.tensor([300.0]), torch.tensor([1e5])
    c = th.compute("TPX->V", [T, p, x])
    dT = 1e-3
    fd = (th.compute("TV->H", [T + dT, c]) - th.compute("TV->H", [T - dT, c])) / (2 * dT)
    cp = th.compute("TV->cp", [T, c])
    report("1a Cp vs central FD of TV->H (rel)", ((fd - cp) / cp).abs().item(), 1e-8,
           ((fd - cp) / cp).abs().item() < 1e-8)
    return T, c


def check_cp_cv(op, th, T, c):
    opy = kintera.ThermoOptions.from_yaml(DECK)  # fresh options: reset() shifts offsets in place
    ty = kintera.ThermoY(opy)
    ty.to(torch.float64)
    ivol = c * th.buffer("mu")  # ThermoY volume variable = partial density, kg/m^3
    cv = ty.compute("VT->cv", [ivol, T])
    cp = th.compute("TV->cp", [T, c])
    ngas = len(op.vapor_ids())
    ref = R * c[..., :ngas].sum(-1)
    err = (((cp - cv) - ref) / ref).abs().item()
    report("1b Cp - Cv - R*sum_gas(c) (rel, ThermoY VT->cv)", err, 1e-12, err < 1e-12)


def check_eos(op, th):
    sp, x = jupiter_x(op)
    il = sp.index("H2O(l)")
    x[:, il] = 1e-3
    x[:, 0] = 0.0
    x[:, 0] = 1.0 - x.sum(-1)
    T, p = torch.tensor([300.0]), torch.tensor([1e5])
    c = th.compute("TPX->V", [T, p, x])
    ngas = len(op.vapor_ids())
    e1 = ((c[..., :ngas].sum(-1) * R * T - p) / p).abs().item()
    report("1c sum_gas c R T = p (rel)", e1, 1e-13, e1 < 1e-13)
    e2 = max(abs(c[0, il] / c[0, j] / (x[0, il] / x[0, j]) - 1).item() for j in range(ngas))
    report("1c c_cloud/c_gas = x_cloud/x_gas, worst over gases (rel)", e2, 1e-13, e2 < 1e-13)


def check_rh(op, th):
    sp, x = jupiter_x(op)
    T, p = torch.tensor([300.0]), torch.tensor([1e5])
    c = th.compute("TPX->V", [T, p, x])
    stoich = th.buffer("stoich")
    ngas = len(op.vapor_ids())
    rh = kintera.relative_humidity(T, c, stoich, op.nucleation(), ngas)[0]
    xg = x[0, :ngas].sum().item()
    pp = {s: x[0, sp.index(s)].item() * 1e5 / xg for s in ("H2O", "NH3", "H2S")}
    hand = [pp["H2O"] / math.exp(h2o_ideal(300.0)), pp["NH3"] / math.exp(nh3_ideal(300.0)),
            pp["NH3"] * pp["H2S"] / math.exp(nh3_h2s_lewis(300.0))]
    for j, name in enumerate(("H2O", "NH3", "NH4SH")):
        e = abs(rh[j].item() / hand[j] - 1)
        print(f"   RH[{name}] kintera {rh[j].item():.12e}  hand {hand[j]:.12e}")
        report(f"1d RH[{name}] vs hand value (rel)", e, 1e-12, e < 1e-12)
    # cloudy states after equilibrium; default max_iter (10) vs 100
    Ts = torch.tensor([130., 140., 160., 180., 200., 220., 240., 260., 280.])
    cloud = [species(op).index(s) for s in ("H2O(l)", "NH3(s)", "NH4SH(s)")]
    for mi in (None, 100):
        opi, thi = thermo_x(max_iter=mi)
        sp, x = jupiter_x(opi, n=len(Ts))
        P = torch.full_like(Ts, 1e5)
        diag = torch.zeros(len(Ts), 1)
        thi.forward(Ts, P, x, diag=diag)
        c = thi.compute("TPX->V", [Ts, P, x])
        rh = kintera.relative_humidity(Ts, c, stoich, opi.nucleation(), ngas)
        worst, n = 0.0, 0
        for j, ic in enumerate(cloud):
            m = x[:, ic] > 0
            n += int(m.sum())
            if m.any():
                worst = max(worst, (rh[m, j] - 1).abs().max().item())
        nfail = int((diag < 0).sum())
        print(f"   max_iter={opi.max_iter()}: {n} (cell, reaction) pairs with condensate, "
              f"T = 130..280 K, p = 1e5 Pa; {nfail} cells report non-convergence (diag < 0)")
        name = f"1d |RH - 1| where condensate present after forward (max_iter={opi.max_iter()})"
        if mi is None:  # unconverged cells are returned as-is: report, do not gate
            report(name, worst, 1e-6, worst < 1e-6, None if worst < 1e-6 else "INFO")
        else:
            report(name, worst, 1e-6, worst < 1e-6)

if __name__ == "__main__":
    print(version_line())
    op, th = thermo_x()
    print(f"thermo species ({len(species(op))}): {species(op)}")
    T, c = check_cp_fd(op, th)
    check_cp_cv(op, th, T, c)
    check_eos(op, th)
    check_rh(op, th)
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "INFO")))
