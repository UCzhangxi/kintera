"""Ch.2 saturation vapour pressure: analytic d ln p_sat/dT vs FD, and the T = 0 latent heat.

No Python binding returns ln p_sat directly, so kintera's value is read back through
relative_humidity at p_i = 1 Pa for every reactant (c_i = 1/(R T)): RH_j = exp(-ln K_j).
"""
import math

from common import thermo_x, species, version_line, kintera, torch

R = 8.31446  # kintera Rgas (constants.h)
RES = []
# independent copies of vapor_functions.h: (T3, P3, beta_l, gamma_l, beta_s, gamma_s)
IDEAL = {"h2o_ideal": (273.16, 611.7, 24.845, 4.986009, 22.98, 0.52),
         "nh3_ideal": (195.4, 6060.0, 20.08, 5.62, 20.64, 1.43)}
LEWIS_B = 4705.0 * math.log(10.0)  # nh3_h2s_lewis: ln K = 14.82 ln10 - B/T + 2 ln(1 atm)


def report(name, val, tol, ok):
    RES.append("PASS" if ok else "FAIL")
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {RES[-1]}")


def branch(f, T):
    T3, P3, bl, gl, bs, gs = IDEAL[f]
    return (T3, P3, bl, gl) if T > T3 else (T3, P3, bs, gs)


def logsvp(f, T):
    if f == "nh3_h2s_lewis":
        return 14.82 * math.log(10.0) - LEWIS_B / T + 2.0 * math.log(101325.0)
    T3, P3, b, g = branch(f, T)
    t = T / T3
    return (1.0 - 1.0 / t) * b - g * math.log(t) + math.log(P3)


def logsvp_ddT(f, T):
    if f == "nh3_h2s_lewis":
        return LEWIS_B / T ** 2
    T3, P3, b, g = branch(f, T)
    t = T / T3
    return (b / t ** 2 - g / t) / T3


def kintera_logsvp(op, th, T):
    """ln K_j(T) for all nucleation reactions, from kintera.relative_humidity."""
    ngas = len(op.vapor_ids())
    c = torch.zeros(len(T), len(species(op)))
    c[:, 1:ngas] = (1.0 / (R * T)).unsqueeze(-1)  # every vapour at 1 Pa
    c[:, 0] = 1.0
    rh = kintera.relative_humidity(T, c, th.buffer("stoich"), op.nucleation(), ngas)
    return -rh.log()


if __name__ == "__main__":
    print(version_line())
    op, th = thermo_x()
    forms = list(op.nucleation().logsvp())
    print(f"nucleation formulas: {forms}")
    Ts = [150., 175., 200., 225., 250., 275., 300., 325., 350.]
    T = torch.tensor(Ts)
    h = 1e-3
    Lk = kintera_logsvp(op, th, T)
    fd = (kintera_logsvp(op, th, T + h) - kintera_logsvp(op, th, T - h)) / (2 * h)
    for j, f in enumerate(forms):
        ev = max(abs(Lk[i, j].item() - logsvp(f, t)) for i, t in enumerate(Ts))
        report(f"2 {f}: kintera ln p_sat vs Python copy, max abs over 150..350 K", ev, 1e-12, ev < 1e-12)
        ed = max(abs(fd[i, j].item() / logsvp_ddT(f, t) - 1) for i, t in enumerate(Ts))
        report(f"2 {f}: analytic d ln p_sat/dT vs central FD (h = 1e-3 K), max rel", ed, 1e-7, ed < 1e-7)
    print("T = 0 extrapolated latent heat beta*R*T3 (J/mol) and gamma:")
    for f, (T3, P3, bl, gl, bs, gs) in IDEAL.items():
        print(f"   {f} liquid branch (T > {T3}): beta*R*T3 = {bl * R * T3:.3f}  gamma = {gl}")
        print(f"   {f} solid  branch (T <= {T3}): beta*R*T3 = {bs * R * T3:.3f}  gamma = {gs}")
    print(f"   nh3_h2s_lewis (2 gases -> 1 solid): R*4705*ln10 = {R * LEWIS_B:.3f} (T-independent)")
    worst = 0.0
    for f in IDEAL:
        T3 = IDEAL[f][0]
        for t in (100., 150., 200., 250., 273.16, 300., 350., T3 - 1e-6, T3 + 1e-6):
            _, _, b, g = branch(f, t)
            lhs = R * t * t * logsvp_ddT(f, t)
            rhs = R * (b * T3 - g * t)
            worst = max(worst, abs(lhs / rhs - 1))
    for t in (150., 250., 350.):
        worst = max(worst, abs(R * t * t * logsvp_ddT("nh3_h2s_lewis", t) / (R * LEWIS_B) - 1))
    report("2 R T^2 dln p/dT = R (beta T3 - gamma T), worst rel over T and branches", worst, 1e-12,
           worst < 1e-12)
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL")))
