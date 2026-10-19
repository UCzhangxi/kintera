"""Gas entropy follows use-nasa9-cp / use-h2-cp like the enthalpy does.

With the flag on, cp ("TV->cp") and h ("TV->H") are T-dependent; the entropy
("TPV->S") must satisfy the Gibbs relation T (ds/dT)_p = dh/dT = cp, keep its
value at T0 = 300 K (as U does), and the nucleation reaction stays at dG = 0
on the saturation curve. Flag off: s keeps cp ln T, so T ds/dT = cp exactly.
Each card runs in its own interpreter: kintera's species registry is global.
"""

import json
import subprocess
import sys

import numpy as np
import pytest

TEMPS = [250.0, 300.0, 400.0, 600.0, 900.0]
CARD = """
reference-state: {Tref: 300.0, Pref: 1.0e5%s}
species:
- {name: H2, composition: {H: 2}, cv_R: 2.5}
- {name: H2O, composition: {H: 2, O: 1}, cv_R: 3.0, u0_R: 0.}
- {name: H2O(l), composition: {H: 2, O: 1}, cv_R: 9.0, u0_R: -3430.}
reactions:
- {equation: H2O <=> H2O(l), type: nucleation, rate-constant: {formula: h2o_ideal}}
"""

PROBE = r"""
import json, sys, torch
torch.set_default_dtype(torch.float64)
from kintera import ThermoX, ThermoOptions
T, out, eps = torch.tensor(json.loads(sys.argv[1])), {}, 1e-5
p = 1e5 * torch.ones_like(T)
for key, card in zip(("on", "off"), sys.argv[2:]):
    tx = ThermoX(ThermoOptions.from_yaml(card))
    S = lambda t, pp, c: tx.compute("TPV->S", [t, pp, c])
    res = {}
    for i, name in enumerate(("H2", "H2O")):
        c = torch.zeros(T.shape + (3,)); c[..., i] = 1.0
        Tp, Tm = T * (1 + eps), T * (1 - eps)
        res[name] = {"cp": tx.compute("TV->cp", [T, c]).tolist(),
                     "Tdsdt": (T * (S(Tp, p, c) - S(Tm, p, c)) / (Tp - Tm)).tolist(),
                     "s": S(T, p, c).tolist()}
    # dG/RT of H2O <=> H2O(l) for pure vapour at p = svp (h2o_ideal)
    lnsvp = torch.tensor(json.loads(sys.argv[-1]))
    cv = torch.zeros(T.shape + (3,)); cv[..., 1] = 1.0
    cl = torch.zeros(T.shape + (3,)); cl[..., 2] = 1.0
    psat = lnsvp.exp()
    dh = tx.compute("TV->H", [T, cl]) - tx.compute("TV->H", [T, cv])
    ds = S(T, psat, cv + cl) - 2 * S(T, psat, cv)
    res["dG_RT"] = ((dh - T * ds) / (8.31446 * T)).tolist()
    out[key] = res
print(json.dumps(out))
"""


def h2o_ideal(t):  # src/vapors/vapor_functions.h
    b, g = (24.845, 4.986009) if t > 273.16 else (22.98, 0.52)
    x = t / 273.16
    return (1 - 1 / x) * b - g * np.log(x) + np.log(611.7)


@pytest.fixture(scope="module", params=["use-nasa9-cp", "use-h2-cp"])
def probe(request, tmp_path_factory):
    d = tmp_path_factory.mktemp(request.param)
    cards = []
    for key, flag in (("on", ", %s: true" % request.param), ("off", "")):
        cards.append(str(d / (key + ".yaml")))
        (d / (key + ".yaml")).write_text(CARD % flag)
    lnsvp = json.dumps([h2o_ideal(t) for t in TEMPS])
    res = subprocess.run([sys.executable, "-c", PROBE, json.dumps(TEMPS)] + cards + [lnsvp],
                         capture_output=True, text=True, check=True)
    return request.param, json.loads(res.stdout.strip().splitlines()[-1])


def test_gibbs_relation_with_flag_on(probe):  # rtol 1e-6 (central FD, eps 1e-5)
    flag, got = probe
    name = "H2" if flag == "use-h2-cp" else "H2O"
    on, off = got["on"][name], got["off"][name]
    assert np.abs(np.array(on["cp"]) - np.array(off["cp"])).max() > 0.5  # J/(mol K): flag is active
    np.testing.assert_allclose(on["Tdsdt"], on["cp"], rtol=1e-6, atol=0)


def test_entropy_reference_kept_at_T0(probe):
    flag, got = probe
    i300 = TEMPS.index(300.0)
    for name in ("H2", "H2O"):
        np.testing.assert_allclose(got["on"][name]["s"][i300], got["off"][name]["s"][i300],
                                   rtol=1e-12, atol=0)


def test_flag_off_and_saturation(probe):
    flag, got = probe
    for name in ("H2", "H2O"):
        np.testing.assert_allclose(got["off"][name]["Tdsdt"], got["off"][name]["cp"],
                                   rtol=1e-6, atol=0)
    for key in ("on", "off"):
        np.testing.assert_allclose(got[key]["dG_RT"], 0.0, rtol=0, atol=1e-9)
