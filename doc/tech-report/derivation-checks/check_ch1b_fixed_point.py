"""Ch. 1b (parcel model, Step 2 of the shared section): the evaporation kinetics evaluated on the phase solver's output.

a. TP path: ThermoX.forward on tests/jupiter.yaml (max_iter 100, T = 130..280 K, p = 1e5 Pa), then
   Kinetics.forward on the returned state with the deck's own evaporation reactions (H2O(l,p) => H2O, h2o_ideal;
   NH3(s,p) => NH3, nh3_ideal: the formulas of the nucleation reactions). The precipitating condensate is given the
   amount of the cloud the solver returned. Measured: rate / rate at c_v = 0, i.e. max(1 - RH, 0), where the cloud is
   present.
b. UV path: ThermoY.forward on a one-vapour card (dry, H2O, H2O(l), H2O(l,p); h2o_ideal in both reactions), T from
   compute("VU->T"), then the same measure.
   Both (a) and (b) also gate |RH - 1|, because the rate is clamped at zero above saturation, and gate coverage
   (at least one cloudy pair; every UV case cloudy) and convergence (diag >= 0). A FAIL line makes the exit status 1.
c. INFO: as (a), but the H2O evaporation reaction is given the inline `ideal` formula with the liquid-branch
   parameters of h2o_ideal. Below 273.16 K (every cloudy cell of (a)) the two curves differ, so the kinetic fixed
   point is not the equilibrium: nothing in the code ties the two reactions' formulas.
"""
import math
import os
import sys
import tempfile
import warnings

from common import thermo_x, species, jupiter_x, version_line, DECK, kintera, torch

warnings.simplefilter("ignore")
RES = []
TMP = tempfile.mkdtemp(prefix="ch1b_")
TOL = 1e-6  # the solver tolerance of check_ch3_species_functions.py line 1d


def worst_of(a, b):
    """max that propagates NaN: Python's max(0.0, nan) is 0.0, which would hide a NaN and let the line PASS."""
    return a if a != a else (b if b != b else max(a, b))


def report(name, val, tol, ok, tag=None):
    tag = tag or ("PASS" if ok and math.isfinite(val) else "FAIL")
    RES.append(tag)
    print(f"{name}: measured {val:.3e}  tol {tol:.0e}  {tag}")


def evap_columns(kin, names):
    """{(condensate, vapour): column} of the evaporation reactions X(p) => X."""
    S, out = kin.stoich, {}
    for j in range(S.shape[1]):
        col = {names[i]: S[i, j].item() for i in range(len(names)) if S[i, j] != 0}
        if len(col) == 2 and sorted(col.values()) == [-1.0, 1.0]:
            src = next(n for n, v in col.items() if v < 0)
            dst = next(n for n, v in col.items() if v > 0)
            if "(" in src and "(" not in dst:
                out[src, dst] = j
    return out


def deficit_ratio(kin, names, T, c, cloud_of):
    """rate / rate with the vapour removed, per evaporation column, at state c (dict name -> tensor[n])."""
    cols = evap_columns(kin, names)
    n = T.numel()
    full = torch.stack([c.get(s, torch.zeros(n)) for s in names], -1)
    for p_name, cloud in cloud_of.items():
        full[:, names.index(p_name)] = c[cloud]
    rate = kin.forward(T, torch.full_like(T, 1e5), full)[0]
    out = {}
    for (src, dst), j in cols.items():
        dry = full.clone()
        dry[:, names.index(dst)] = 0.0
        ref = kin.forward(T, torch.full_like(T, 1e5), dry)[0][:, j]
        out[dst] = (rate[:, j] / ref, cloud_of[src])
    return out


def tp_states():
    op, th = thermo_x(max_iter=100)
    Ts = torch.tensor([130., 140., 160., 180., 200., 220., 240., 260., 280.])
    sp, x = jupiter_x(op, n=len(Ts))
    P = torch.full_like(Ts, 1e5)
    diag = torch.zeros(len(Ts), 1)
    th.forward(Ts, P, x, diag=diag)
    c = th.compute("TPX->V", [Ts, P, x])
    rh = kintera.relative_humidity(Ts, c, th.buffer("stoich"), op.nucleation(), len(op.vapor_ids()))
    return Ts, {s: c[:, i] for i, s in enumerate(sp)}, rh, int((diag < 0).sum())


def check_tp(deck, label, info=False):
    Ts, c, rh, nfail = tp_states()
    op = kintera.KineticsOptions.from_yaml(deck)
    kin = kintera.Kinetics(op)
    names = op.species()
    res = deficit_ratio(kin, names, Ts, c, {"H2O(l,p)": "H2O(l)", "NH3(s,p)": "NH3(s)"})
    worst, worst_rh, n = 0.0, 0.0, 0
    for vap, (ratio, cloud) in res.items():
        j = ("H2O", "NH3").index(vap)
        m = c[cloud] > 0
        n += int(m.sum())
        for k in torch.nonzero(m).flatten().tolist():
            r = ratio[k].item()
            print(f"   {label} T={Ts[k].item():.0f} {vap}: RH - 1 = {rh[k, j].item() - 1:+.3e}, "
                  f"rate / rate(c_v = 0) = {r:.3e}")
            worst = worst_of(worst, abs(r))
            worst_rh = worst_of(worst_rh, abs(rh[k, j].item() - 1))
    print(f"   {label}: {n} (cell, reaction) pairs with condensate; {nfail} cells report non-convergence")
    return worst, worst_rh, n, nfail


def check_uv():
    card = """reference-state: {Tref: 300., Pref: 1.e5}
species:
  - {name: dry, composition: {H: 1.5, He: 0.15}, cv_R: 2.5}
  - {name: H2O, composition: {H: 2, O: 1}, cv_R: 2.5, u0_R: 0.}
  - {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
  - {name: "H2O(l,p)", composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
  - {equation: H2O <=> H2O(l), type: nucleation, rate-constant: {formula: h2o_ideal}}
  - equation: H2O(l) => H2O(l,p)
    type: coagulation
    rate-constant: {A: 0.001, b: 0, Ea_R: 1.}
  - equation: H2O(l,p) => H2O
    type: evaporation
    rate-constant: {formula: h2o_ideal, diff_c: 0.2e-4, diff_T: 1.75, diff_P: -1., vm: 18.e-6, diameter: 1.0e-2}
"""
    path = os.path.join(TMP, "uv.yaml")
    with open(path, "w") as f:
        f.write(card)
    top = kintera.ThermoOptions.from_yaml(path)
    top.max_iter(100)
    th = kintera.ThermoY(top)
    sp = species(top)
    kop = kintera.KineticsOptions.from_yaml(path)
    kin = kintera.Kinetics(kop)
    names = kop.species()
    worst, worst_rh, n, nfail = 0.0, 0.0, 0, 0
    for T0, yv in [(280.0, 0.02), (250.0, 0.01), (220.0, 0.005)]:
        rho = torch.tensor([1.0])
        y = torch.zeros(len(sp) - 1, 1)
        y[sp.index("H2O") - 1] = yv
        inv_mu = th.buffer("inv_mu")
        V0 = th.compute("DY->V", [rho, y])
        U = th.compute("VT->U", [V0, torch.tensor([T0])])
        diag = torch.zeros(1, 1)
        th.forward(rho, U, y, False, diag)
        V1 = th.compute("DY->V", [rho, y])
        T1 = th.compute("VU->T", [V1, U])
        c1 = (V1 * inv_mu)[0]
        c = {s: c1[i].reshape(1) for i, s in enumerate(sp)}
        nfail += int(diag.item() < 0)
        if c["H2O(l)"].item() <= 0:
            print(f"   UV T0={T0:.0f}: no condensate after forward (counted as missing coverage)")
            continue
        n += 1
        ratio, _ = deficit_ratio(kin, names, T1.reshape(1), c, {"H2O(l,p)": "H2O(l)"})["H2O"]
        cv = torch.stack([c[s] for s in sp], -1)
        rh = kintera.relative_humidity(T1.reshape(1), cv, th.buffer("stoich"), top.nucleation(),
                                       len(top.vapor_ids()))[0, 0].item()
        print(f"   UV T0={T0:.0f} yv={yv}: diag={diag.item():.0f} T={T1.item():.6f}, RH - 1 = {rh - 1:+.3e}, "
              f"rate / rate(c_v = 0) = {ratio.item():.3e}")
        worst, worst_rh = worst_of(worst, abs(ratio.item())), worst_of(worst_rh, abs(rh - 1))
    return worst, worst_rh, n, nfail, 3


if __name__ == "__main__":
    print(version_line())
    # the rate is clamped at zero above saturation, so |RH - 1| is gated too: a zero rate alone could be supersaturation
    # coverage and convergence are gated as well: an empty set or an unconverged cell would make the maxima vacuous
    w, wr, n, nfail = check_tp(DECK, "TP")
    report("(a) TP: cloudy (cell, reaction) pairs (must be > 0) and non-converged cells (must be 0); missing",
           float((n == 0) + nfail), 0, n > 0 and nfail == 0)
    report("(a) TP: worst |rate| / rate(c_v = 0) on the phase solver's output, same formulas", w, TOL, w <= TOL)
    report("(a) TP: worst |RH - 1| at the same states", wr, TOL, wr <= TOL)
    w, wr, n, nfail, ncase = check_uv()
    report("(b) UV: cases without condensate or not converged (must be 0)", float(ncase - n + nfail), 0,
           n == ncase and nfail == 0)
    report("(b) UV: worst |rate| / rate(c_v = 0) on the phase solver's output, same formula", w, TOL, w <= TOL)
    report("(b) UV: worst |RH - 1| at the same states, T from VU->T", wr, TOL, wr <= TOL)
    with open(DECK) as f:
        text = f.read()
    old = "formula: h2o_ideal, diff_c"
    assert text.count(old) == 1
    path = os.path.join(TMP, "mismatch.yaml")
    with open(path, "w") as f:
        f.write(text.replace(old, "formula: ideal, T3: 273.16, P3: 611.7, beta: 24.845, gamma: 4.986009, diff_c"))
    w, _, _, _ = check_tp(path, "mismatch")
    print(f"(c) H2O evaporation with the inline liquid-branch curve (all cloudy cells are below 273.16 K): "
          f"worst rate / rate(c_v = 0) {w:.3e}  INFO")
    RES.append("INFO")
    print("SUMMARY: " + ", ".join(f"{RES.count(k)} {k}" for k in ("PASS", "FAIL", "INFO")))
    sys.exit(1 if "FAIL" in RES else 0)
