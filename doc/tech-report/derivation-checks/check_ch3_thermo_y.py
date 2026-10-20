"""Ch.3 ThermoY conversions and the VU->T inversion (C3-d), and one energy model for the UV solver (D12).

(d1) Y->X against x_n = (y_n mu_0/mu_n) / (1 + sum_k y_k (mu_0/mu_k - 1)), x_0 = 1 - sum_n x_n (tests/jupiter.yaml).
(d2) VT->U then VU->T returns T, constant cv (tests/jupiter.yaml).
(d3) the same round trip with use-h2-cp (both conversions use the T-dependent H2 energy).
(d4) UV saturation adjustment (ThermoY.forward) of a supersaturated H2 + H2O parcel at fixed (rho, U): afterwards
     T = VU->T(U), and the vapour must sit on its saturation curve, |ln p_v - ln K(T)| small. Flag off: PASS. With
     use-h2-cp the UV kernel at 0d9f67f receives the constant-cv offsets while VU->T uses the H2 rotational energy,
     so the result is off the curve: EXPECTED-FAIL, row D12 of UCzhangxi/kintera#54.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import thermo_x, species, version_line, DECK, kintera, torch  # noqa: E402
import ch3_card  # noqa: E402

RES = []


def report(name, val, tol, ok, expected=None):
    if not math.isfinite(val):
        ok = False
    tag = "PASS" if ok else ("EXPECTED-FAIL" if expected else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}" + (f" ({expected})" if expected and not ok else ""))


def check_jupiter():
    op, th = thermo_x()
    sp = species(op)
    mu = th.buffer("mu")
    ty = kintera.ThermoY(kintera.ThermoOptions.from_yaml(DECK))
    ty.to(torch.float64)
    torch.manual_seed(3)
    ny = len(sp) - 1
    y = 0.02 * torch.rand(ny, 4)
    x = ty.compute("Y->X", [y])
    r = mu[0] / mu[1:]
    xn = (y.T * r) / (1.0 + (y.T * (r - 1.0)).sum(-1, keepdim=True))
    ref = torch.cat([1.0 - xn.sum(-1, keepdim=True), xn], -1)
    e = ((x - ref).abs().max() / ref.abs().max()).item()
    report("(d1) Y->X vs the mole-fraction formula with the dry species implicit (rel)", e, 1e-14, e < 1e-14)
    rho = torch.full((4,), 0.5)
    V = ty.compute("DY->V", [rho, y])
    T0 = torch.tensor([150.0, 250.0, 300.0, 400.0])
    U = ty.compute("VT->U", [V, T0])
    T1 = ty.compute("VU->T", [V, U])
    e = (T1 - T0).abs().max().item()
    report("(d2) VT->U then VU->T, constant cv, |T - T0| (K)", e, 1e-10, e < 1e-10)


CARD = """reference-state: {Tref: 300.0, Pref: 1.0e5%s}
species:
- {name: H2, composition: {H: 2}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
- {name: H2O(c), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: 'H2O <=> H2O(c)', type: nucleation, rate-constant: {formula: h2o_ideal}}
dynamics: {equation-of-state: {max-iter: 50}}
"""
PROBE = r"""
from kintera import ThermoY, ThermoOptions
torch.set_default_dtype(torch.float64)
th = ThermoY(ThermoOptions.from_yaml(sys.argv[1]))
R = 8.31446
mu = (1.0 / th.inv_mu)
out = {}
T0s = torch.tensor([150.0, 300.0, 600.0])
V = th.compute("DY->V", (torch.full((3,), 0.1), torch.tensor([[0.01] * 3, [0.0] * 3])))
U = th.compute("VT->U", (V, T0s))
out["roundtrip"] = (th.compute("VU->T", (V, U)) - T0s).abs().max().item()
T0, xv = 300.0, 0.05
x = torch.tensor([1 - xv, xv, 0.0])
y = (x * mu / (x * mu).sum())[1:].reshape(2, 1).clone()
rho = torch.tensor([1e5 * (x * mu).sum().item() / (R * T0)])
U = th.compute("VT->U", (th.compute("DY->V", (rho, y)), torch.tensor([T0])))
d = torch.zeros(1, 1)
th.forward(rho, U, y, False, d)
V1 = th.compute("DY->V", (rho, y))
T1 = th.compute("VU->T", (V1, U)).item()
c = V1[0] / mu
out.update({"diag": d.item(), "T": T1, "p_vap": (c[1] * R * T1).item(), "cloud": c[2].item()})
print(json.dumps(out))
"""


def h2o_ideal(T):  # src/vapors/vapor_functions.h
    b, g = (24.845, 4.986009) if T > 273.16 else (22.98, 0.52)
    t = T / 273.16
    return (1 - 1 / t) * b - g * math.log(t) + math.log(611.7)


def check_h2():
    for flag, label, tag in (("", "use-h2-cp off", None), (", use-h2-cp: true, h2-cp-mode: normal", "use-h2-cp normal", "D12"),
                             (", use-h2-cp: true, h2-cp-mode: equilibrium", "use-h2-cp equilibrium", "D12")):
        got = ch3_card.run(CARD % flag, PROBE)
        if tag:
            report(f"(d3) VT->U then VU->T, {label}, |T - T0| (K)", got["roundtrip"], 1e-10, got["roundtrip"] < 1e-10)
        r = abs(math.log(got["p_vap"]) - h2o_ideal(got["T"]))
        print(f"   {label}: after ThermoY.forward T = {got['T']:.6f} K, cloud = {got['cloud']:.6e} mol/m^3, "
              f"ln p_v - ln K(T) = {math.log(got['p_vap']) - h2o_ideal(got['T']):+.3e}")
        report(f"(d4) UV saturation adjustment lands on the curve, {label}: |ln p_v - ln K(T)|", r, 1e-5, r < 1e-5, tag)


if __name__ == "__main__":
    print(version_line())
    check_jupiter()
    check_h2()
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "EXPECTED-FAIL")))
