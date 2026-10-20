"""Ch.3 adiabats: dry-limit extrapolate_dlnp, effective_cp vs FD of equilibrium enthalpy, PXS->T."""
import math

from common import thermo_x, species, jupiter_x, version_line, kintera, torch

R = 8.31446  # kintera Rgas (constants.h)
RES = []


def report(name, val, tol, ok, tag=None, row=None):
    tag = tag or ("PASS" if ok else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}" + (f" ({row})" if row and tag == "EXPECTED-FAIL" else ""))


def dry_x(op):
    x = torch.zeros(1, len(species(op)))
    x[0, 0] = 1.0
    return x


def check_dry_adiabat():
    for ftol, mi in ((None, None), (1e-12, 50)):
        op, th = thermo_x(ftol=ftol, max_iter=mi)
        cp_bar = op.cref_R()[0] + 1.0  # dry cv_R + 1
        T, p, x = torch.tensor([300.0]), torch.tensor([1e5]), dry_x(op)
        th.extrapolate_dlnp(T, p, x, -0.5)
        ref = 300.0 * math.exp(-0.5 / cp_bar)
        e = abs(T.item() / ref - 1)
        print(f"   ftol={op.ftol():.0e}: T1 = {T.item():.12f} K, analytic {ref:.12f} K "
              f"(cp/R = {cp_bar}), p1 = {p.item():.6f} Pa")
        report(f"4a dry adiabat T1 vs 300 exp(-0.5 R/cp), ftol={op.ftol():.0e} (rel)", e, 1e-8, e < 1e-8)


def molar_h(th, T, p, x0):
    x = x0.clone()
    th.forward(T, p, x)
    c = th.compute("TPX->V", [T, p, x])
    return (th.compute("TV->H", [T, c]) / c.sum(-1)).item(), x


def check_effective_cp():
    op, th = thermo_x(ftol=1e-14, max_iter=100)
    sp, x0 = jupiter_x(op)
    T, p = torch.tensor([280.0]), torch.tensor([1e6])
    x = x0.clone()
    gain = th.forward(T, p, x)
    cloudy = {s: x[0, sp.index(s)].item() for s in ("H2O(l)", "NH3(s)", "NH4SH(s)")}
    print(f"   state T=280 K, p=1e6 Pa, condensate mole fractions {cloudy}")
    cpe = th.effective_cp(T, p, x, gain).item()
    cf = th.compute("TPX->V", [T, p, x])
    cp_frozen = (th.compute("TV->cp", [T, cf]) / cf.sum(-1)).item()
    dT = 1e-2
    hp, _ = molar_h(th, T + dT, p, x0)
    hm, _ = molar_h(th, T - dT, p, x0)
    fd = (hp - hm) / (2 * dT)
    print(f"   effective_cp = {cpe:.10f}, FD d(H/n)/dT = {fd:.10f}, frozen cp = {cp_frozen:.6f} J/(mol K)")
    e = abs(cpe / fd - 1)
    report("4b effective_cp vs central FD of equilibrium molar enthalpy (rel)", e, 1e-5, e < 1e-5)
    # reversible step: molar entropy conserved by a small saturated extrapolation
    opd, thd = thermo_x()
    T1, p1, x1 = T.clone(), p.clone(), x0.clone()
    thd.forward(T1, p1, x1)
    s0 = (thd.compute("TPV->S", [T1, p1, c := thd.compute("TPX->V", [T1, p1, x1])]) / c.sum(-1)).item()
    thd.extrapolate_dlnp(T1, p1, x1, -0.01)
    c = thd.compute("TPX->V", [T1, p1, x1])
    s1 = (thd.compute("TPV->S", [T1, p1, c]) / c.sum(-1)).item()
    print(f"   saturated step dlnp=-0.01: T {T.item()} -> {T1.item():.8f} K, s {s0:.10f} -> {s1:.10f} J/(mol K)")
    report("4b |ds| over saturated extrapolate_dlnp step (J/(mol K))", abs(s1 - s0), 10 * opd.ftol(),
           abs(s1 - s0) < 10 * opd.ftol())


def check_pxs_roundtrip():
    op, th = thermo_x()
    T, p, x = torch.tensor([600.0]), torch.tensor([1e5]), dry_x(op)
    c = th.compute("TPX->V", [T, p, x])
    S = th.compute("TPV->S", [T, p, c])  # volumetric, as compared inside PXS->T
    Tb = th.compute("PXS->T", [p, x, S])
    d = abs(Tb.item() - 600.0)
    print(f"   S(600 K) = {S.item():.10f} J/(K m^3); PXS->T returns {Tb.item():.10f} K "
          f"(start guess Tref = {op.Tref()} K, max_iter = {op.max_iter()})")
    report("4c PXS->T round trip |T - 600| (K)", d, 1e-6, d < 1e-6, None if d < 1e-6 else "EXPECTED-FAIL", row="D8")


if __name__ == "__main__":
    print(version_line())
    check_dry_adiabat()
    check_effective_cp()
    check_pxs_roundtrip()
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "EXPECTED-FAIL")))
