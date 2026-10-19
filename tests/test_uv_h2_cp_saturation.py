"""use-h2-cp: the UV saturation adjustment must use the H2 rotational internal energy.

With `use-h2-cp: true`, VT->U and VU->T evaluate H2 with its rotational partition function,
so `ThermoY.forward` must do the same. One supersaturated H2 + vapour parcel at fixed
(rho, U), in both ortho/para modes: after forward, the host recovers T with VU->T from the
same U, and the vapour must then sit on its saturation curve, r = ln p_vap - ln svp(T) ~ 0.
Control: the same card with use-h2-cp off. CPU and, if present, CUDA.

Each card runs in its own interpreter: kintera's species registry is global.
"""

import json
import math
import subprocess
import sys

import pytest
import torch

CARD = """
reference-state: {Tref: 300.0, Pref: 1.0e5%(h2)s}
species:
- {name: H2, composition: {H: 2}, cv_R: 2.5}
- {name: %(v)s, composition: %(comp)s, cv_R: 2.5, u0_R: 0.}
- {name: %(v)s(c), composition: %(comp)s, cv_R: 9.0, u0_R: %(u0)s}
reactions:
- {equation: '%(v)s <=> %(v)s(c)', type: nucleation, rate-constant: {formula: %(f)s}}
dynamics: {equation-of-state: {max-iter: 50}}
"""

PROBE = r"""
import json, sys, torch
torch.set_default_dtype(torch.float64)
from kintera import ThermoY, ThermoOptions
th = ThermoY(ThermoOptions.from_yaml(sys.argv[1]))
dev = torch.device(sys.argv[2])
th.to(dev)
T0, xv = float(sys.argv[3]), float(sys.argv[4])
R = 8.314462618
mu = (1.0 / th.inv_mu).cpu()
x = torch.tensor([1 - xv, xv, 0.0])
y = (x * mu / (x * mu).sum())[1:].reshape(2, 1).clone().to(dev)
rho = torch.tensor([1e5 * (x * mu).sum().item() / (R * T0)], device=dev)
U = th.compute("VT->U", (th.compute("DY->V", (rho, y)), torch.tensor([T0], device=dev)))
d = torch.zeros(1, 1, device=dev)
th.forward(rho, U, y, False, d)
V1 = th.compute("DY->V", (rho, y))
T1 = th.compute("VU->T", (V1, U)).item()
c = V1[0].cpu() / mu
print(json.dumps({"diag": d.item(), "T": T1, "p_vap": (c[1] * R * T1).item(),
                  "cloud": c[2].item()}))
"""


def _logsvp_ideal(t, beta, gamma):
    return (1.0 - 1.0 / t) * beta - gamma * math.log(t)


def h2o_ideal(T):  # src/vapors/vapor_functions.h
    tr = 273.16
    return (_logsvp_ideal(T / tr, 24.845, 4.986009) if T > tr
            else _logsvp_ideal(T / tr, 22.98, 0.52)) + math.log(611.7)


def nh3_ideal(T):  # src/vapors/vapor_functions.h
    tr = 195.4
    return (_logsvp_ideal(T / tr, 20.08, 5.62) if T > tr
            else _logsvp_ideal(T / tr, 20.64, 1.43)) + math.log(6060.0)


CASES = [  # vapour, composition, cloud u0_R, svp, T0 [K], vapour mole fraction
    ("H2O", "{H: 2, O: 1}", -3430., h2o_ideal, 300.0, 0.05),
    ("NH3", "{N: 1, H: 3}", -5520., nh3_ideal, 160.0, 0.02),
    ("NH3", "{N: 1, H: 3}", -5520., nh3_ideal, 120.0, 0.002),
]
DEVICES = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("mode", [None, "normal", "equilibrium"])
@pytest.mark.parametrize("case", CASES, ids=lambda c: "%s-%gK" % (c[0], c[4]))
def test_uv_state_is_saturated_with_h2_cp(tmp_path, case, mode, device):
    v, comp, u0, svp, T0, xv = case
    card = tmp_path / ("%s_%s.yaml" % (v, mode or "off"))
    h2 = ", use-h2-cp: true, h2-cp-mode: %s" % mode if mode else ""
    card.write_text(CARD % dict(h2=h2, v=v, comp=comp, u0=u0, f=svp.__name__))
    res = subprocess.run([sys.executable, "-c", PROBE, str(card), device, str(T0), str(xv)],
                         capture_output=True, text=True, check=True, cwd=tmp_path)
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert out["diag"] > 0, out
    assert out["cloud"] > 0, out
    r = math.log(out["p_vap"]) - svp(out["T"])
    assert abs(r) < 1e-5, (r, out)
