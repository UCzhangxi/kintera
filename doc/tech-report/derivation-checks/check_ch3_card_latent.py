"""Ch.3 Clausius-Clapeyron consistency of condensate cards with their saturation formula.

l_card(T) = h_vapour - h_condensate from kintera TV->H (move dn vapour -> condensate, central).
l_svp(T)  = R T^2 d ln p_sat/dT = R (beta T3 - gamma T) for an 'ideal' formula.
Consistent card: u_c(0) - u_v(0) = -beta T3 and cv_c = cv_v + 1 + gamma.
"""
import os
import tempfile

from common import thermo_x, species, version_line, kintera, torch

R = 8.31446  # kintera Rgas (constants.h)
RES = []
IDEAL = {"h2o_ideal": (273.16, 611.7, 24.845, 4.986009, 22.98, 0.52),  # vapor_functions.h copies
         "nh3_ideal": (195.4, 6060.0, 20.08, 5.62, 20.64, 1.43)}
TS = [200.0, 250.0, 273.16, 300.0]


def l_card_kintera(th, nsp, iv, ic, T):
    c = torch.full((1, nsp), 1.0)
    dn = 1e-3
    d = torch.zeros(1, nsp)
    d[0, iv], d[0, ic] = -dn, dn
    Tt = torch.tensor([T])
    dH = (th.compute("TV->H", [Tt, c + d]) - th.compute("TV->H", [Tt, c - d])) / (2 * dn)
    return -dH.item()


def l_svp(f, T):
    T3, P3, bl, gl, bs, gs = IDEAL[f]
    b, g = (bl, gl) if T > T3 else (bs, gs)
    return R * (b * T3 - g * T), b, g


def jupiter_cards():
    op, th = thermo_x()
    sp = species(op)
    nsp = len(sp)
    u0 = op.uref_R()  # already shifted by kintera to T = 0: u = R (u0 + cv T)
    cv = op.cref_R()
    print("jupiter.yaml cards (INFO; ratio 1 = consistent with the saturation curve):")
    for f, v, cd in (("h2o_ideal", "H2O", "H2O(l)"), ("nh3_ideal", "NH3", "NH3(s)")):
        iv, ic = sp.index(v), sp.index(cd)
        for T in TS:
            lk = l_card_kintera(th, nsp, iv, ic, T)
            la = R * ((u0[iv] + cv[iv] * T + T) - (u0[ic] + cv[ic] * T))
            ls, b, g = l_svp(f, T)
            br = "liquid" if T > IDEAL[f][0] else "solid"
            RES.append("INFO")
            print(f"   {cd:7s} T={T:7.2f} ({br:6s} branch): l_card={lk:10.3f} (YAML algebra {la:10.3f}) "
                  f"l_svp={ls:10.3f} J/mol  ratio={lk / ls:.6f}  INFO")
        e = max(abs(l_card_kintera(th, nsp, iv, ic, T) / (R * ((u0[iv] + cv[iv] * T + T)
                - (u0[ic] + cv[ic] * T))) - 1) for T in TS)
        RES.append("PASS" if e < 1e-10 else "FAIL")
        print(f"   {cd}: kintera TV->H latent vs YAML offset algebra, max rel {e:.3e}  tol 1e-10  {RES[-1]}")
        T3, P3, bl, gl, bs, gs = IDEAL[f]
        for br, b, g in (("liquid", bl, gl), ("solid", bs, gs)):
            print(f"   consistent {cd} card for {f} {br} branch: u_c(0)-u_v(0) = -beta*T3 = "
                  f"{-b * T3:.4f} K (x R), cv_c = cv_v + 1 + gamma = {cv[iv] + 1 + g:.6f} "
                  f"(card has {u0[ic] - u0[iv]:.1f}, {cv[ic]})")


def consistent_card(tmp):
    T3, P3, b, g = IDEAL["h2o_ideal"][:4]
    Tref, cvv = 300.0, 2.5
    cvc = cvv + 1.0 + g
    u0c = (cvc - cvv) * Tref - b * T3  # u0_R at Tref, vapour u0_R = 0
    path = os.path.join(tmp, "consistent.yaml")
    with open(path, "w") as fh:
        fh.write(f"""reference-state:
  Tref: {Tref}
  Pref: 1.e5
species:
  - name: dry
    composition: {{H: 1.5, He: 0.15}}
    cv_R: 2.5
  - name: H2O
    composition: {{H: 2, O: 1}}
    cv_R: {cvv}
    u0_R: 0.
  - name: H2O(l)
    composition: {{H: 2, O: 1}}
    cv_R: {cvc!r}
    u0_R: {u0c!r}
reactions:
  - equation: H2O <=> H2O(l)
    type: nucleation
    rate-constant: {{formula: ideal, T3: {T3}, P3: {P3}, beta: {b}, gamma: {g}}}
""")
    print(f"consistent card: cv_c = {cvc!r}, u0_R(Tref={Tref}) = {u0c!r}, single 'ideal' liquid branch")
    op, th = thermo_x(path)
    sp = species(op)
    worst = 0.0
    for T in [150.0, 200.0, 250.0, 273.16, 300.0, 350.0, 400.0]:
        lk = l_card_kintera(th, len(sp), sp.index("H2O"), sp.index("H2O(l)"), T)
        ls = R * (b * T3 - g * T)
        worst = max(worst, abs(lk / ls - 1))
        print(f"   T={T:7.2f}: l_card={lk:.6f} l_svp={ls:.6f} J/mol ratio-1={lk / ls - 1:.2e}")
    RES.append("PASS" if worst < 1e-10 else "FAIL")
    print(f"3 consistent card l_card/l_svp - 1, max over T: measured {worst:.3e}  tol 1e-10  {RES[-1]}")


if __name__ == "__main__":
    print(version_line())
    jupiter_cards()
    with tempfile.TemporaryDirectory() as tmp:
        consistent_card(tmp)
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "INFO")))
