"""Runs of the log-K equilibrium solver behind the data figures and numbers of chapter 5 (@sec-ch05).

Needs kintera built at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45 (CPU, or CUDA with --device cuda). The
inputs are small YAML files written below, not decks of another project. Run from any directory:

    python -P run_equilibrium.py <out_dir> [--device cpu|cuda]
    python -P run_equilibrium.py --compare <cpu_dir> <cuda_dir>

It writes four JSON files to <out_dir>, each with a `provenance` field: flash_binary.json (two-component ideal
solution against the closed-form flash), water_condensation.json (water vapour over a pure liquid phase),
h2o_dissociation.json (hot H-O gas with NASA-9 constants) and status_cases.json (one case per status code).
It prints the numbers the chapter quotes, one per line with a stable label.
"""
import argparse
import json
import platform
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch
import kintera
from kintera import EquilibriumOptions, EquilibriumTP
from kintera.equilibrium import Nasa9LogK

SHA = "0d9f67f97d841147e23283d2dcdab302238d2c45"
D = torch.float64

BINARY = """phases:
  - {name: gas, thermo: ideal-gas, species: [A, B]}
  - {name: liquid, thermo: ideal-solution, species: [A_l, B_l]}
species:
  - {name: A, composition: {X: 1}}
  - {name: B, composition: {Z: 1}}
  - {name: A_l, composition: {X: 1}}
  - {name: B_l, composition: {Z: 1}}
reactions:
  - {equation: "A <=> A_l", type: equilibrium}
  - {equation: "B <=> B_l", type: equilibrium}
"""

WATER = """phases:
  - {name: gas, thermo: ideal-gas, species: [N2, H2O]}
  - {name: liquid, thermo: pure, species: [H2O_l]}
species:
  - {name: N2, composition: {N: 2}}
  - {name: H2O, composition: {H: 2, O: 1}}
  - {name: H2O_l, composition: {H: 2, O: 1}}
reactions:
  - {equation: "H2O <=> H2O_l", type: equilibrium}
"""

HO = """phases:
  - {name: gas, thermo: ideal-gas, species: [H2, O2, H2O, OH, H, O]}
species:
  - {name: H2, composition: {H: 2}}
  - {name: O2, composition: {O: 2}}
  - {name: H2O, composition: {H: 2, O: 1}}
  - {name: OH, composition: {H: 1, O: 1}}
  - {name: H, composition: {H: 1}}
  - {name: O, composition: {O: 1}}
reactions:
  - {equation: "H2 + 0.5 O2 <=> H2O", type: equilibrium}
  - {equation: "H2 <=> 2 H", type: equilibrium}
  - {equation: "O2 <=> 2 O", type: equilibrium}
  - {equation: "0.5 H2 + 0.5 O2 <=> OH", type: equilibrium}
equilibrium: {max-iter: 100}
"""


def options(text):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(text)
    return EquilibriumOptions.from_yaml(f.name)


def on(module, dev):
    module.to(torch.device(dev))
    return module


def tens(x, dev):
    return torch.tensor(x, dtype=D, device=dev)


def provenance(dev, deck, command_args, cases):
    return {
        "sha": SHA,
        "deck": deck,
        "cases": cases,
        "command": "python -P src/kintera_report/ch05/runs/run_equilibrium.py " + command_args,
        "device": f"{dev.upper()}, double",
        "versions": f"kintera {kintera.__version__} source build, Python {platform.python_version()}, "
                    f"torch {torch.__version__}, numpy {np.__version__}",
    }


def flash_closed_form(z, psat, p):
    """Two-component ideal-solution flash: Rachford-Rice root by bisection; None outside the two-phase window."""
    k = psat / p
    f = lambda v: np.sum(z * (k - 1.0) / (1.0 + v * (k - 1.0)))
    if f(0.0) <= 0.0 or f(1.0) >= 0.0:
        return None
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) > 0.0 else (lo, mid)
    v = 0.5 * (lo + hi)
    return 1.0 - v, z / (1.0 + v * (k - 1.0))


def run_binary(dev):
    op = options(BINARY)
    eq = on(EquilibriumTP(op), dev)
    psat = np.array([4.0e4, 1.6e5])
    z = np.array([0.5, 0.5])
    p0 = op.standard_pressure()
    log_k = tens(np.log(p0 / psat).tolist(), dev)
    rows = {"p": [], "liquid_fraction": [], "x_A_liquid": [], "closed_liquid_fraction": [], "closed_x_A_liquid": [],
            "status": [], "iterations": [], "error": []}
    for p in np.round(np.arange(0.40e5, 1.301e5, 0.025e5), 1):
        n0 = tens([0.25, 0.25, 0.25, 0.25], dev)
        n, _, diag = eq(tens(300.0, dev), tens(float(p), dev), n0, log_k)
        n = n.cpu().numpy()
        diag = diag.cpu().tolist()
        closed = flash_closed_form(z, psat, p)
        rows["p"].append(float(p))
        rows["liquid_fraction"].append(float(n[2] + n[3]))
        rows["x_A_liquid"].append(float(n[2] / (n[2] + n[3])))
        rows["closed_liquid_fraction"].append(None if closed is None else float(closed[0]))
        rows["closed_x_A_liquid"].append(None if closed is None else float(closed[1][0]))
        rows["status"].append(diag[0])
        rows["iterations"].append(diag[1])
        rows["error"].append(diag[2])
    ok = [i for i, c in enumerate(rows["closed_liquid_fraction"]) if c is not None]
    dev_l = max(abs(rows["liquid_fraction"][i] - rows["closed_liquid_fraction"][i]) for i in ok)
    dev_x = max(abs(rows["x_A_liquid"][i] - rows["closed_x_A_liquid"][i]) for i in ok)
    print(f"[R1] binary two-phase cells: {len(ok)}, all status 0: "
          f"{all(rows['status'][i] == 0 for i in ok)}, max iterations {max(rows['iterations'][i] for i in ok):.0f}")
    print(f"[R2] binary max |liquid fraction - closed form| = {dev_l:.2e}, max |x_A,liquid - closed form| = {dev_x:.2e}")
    one = [i for i in range(len(rows["p"])) if i not in ok]
    print(f"[R3] binary one-phase cells: {len(one)}, statuses {sorted(set(rows['status'][i] for i in one))}, "
          f"min error {min(rows['error'][i] for i in one):.2e}")
    for i in one:
        print(f"     p={rows['p'][i]:.0f} status={rows['status'][i]:.0f} it={rows['iterations'][i]:.0f} "
              f"err={rows['error'][i]:.3e} liquid={rows['liquid_fraction'][i]:.3e}")
    cases = ("T = 300 K; p = 0.400e5 to 1.300e5 Pa in steps of 2.5e3 Pa; ln K = ln(p_std/p_sat) with p_sat(A) = 4e4 Pa, "
             "p_sat(B) = 1.6e5 Pa; start 0.25 mol of each of A, B, A_l, B_l; default options")
    rows["provenance"] = provenance(dev, "BINARY in run_equilibrium.py", "<out_dir>", cases)
    return rows


def run_water(dev):
    op = options(WATER)
    eq = on(EquilibriumTP(op), dev)
    lk = Nasa9LogK(op, ["N2", "H2O", "H2O_l_s"])
    rows = {"T": [], "psat_from_K": [], "p_h2o": [], "liquid": [], "status": [], "iterations": [], "error": []}
    p = 1.0e5
    for t in np.arange(270.0, 330.1, 2.5):
        log_k = lk(tens(float(t), dev), tens(p, dev))
        n0 = tens([1.0, 0.02, 0.02], dev)
        n, _, diag = eq(tens(float(t), dev), tens(p, dev), n0, log_k)
        n = n.cpu().numpy()
        diag = diag.cpu().tolist()
        rows["T"].append(float(t))
        rows["psat_from_K"].append(float(op.standard_pressure() * np.exp(-log_k.item())))
        rows["p_h2o"].append(float(p * n[1] / (n[0] + n[1])))
        rows["liquid"].append(float(n[2]))
        rows["status"].append(diag[0])
        rows["iterations"].append(diag[1])
        rows["error"].append(diag[2])
    i300 = rows["T"].index(300.0)
    print(f"[R4] water: p_sat from NASA-9 ln K at 300 K = {rows['psat_from_K'][i300]:.1f} Pa")
    two = [i for i, s in enumerate(rows["status"]) if s == 0]
    print(f"[R5] water: status 0 for T <= {max(rows['T'][i] for i in two):.1f} K; "
          f"max |p_H2O/p_sat - 1| there = {max(abs(rows['p_h2o'][i] / rows['psat_from_K'][i] - 1) for i in two):.1e}")
    bad = [i for i, s in enumerate(rows["status"]) if s != 0]
    print(f"[R6] water: statuses {sorted(set(rows['status'][i] for i in bad))} for T >= "
          f"{min(rows['T'][i] for i in bad):.1f} K; max liquid left {max(rows['liquid'][i] for i in bad):.1e} mol; "
          f"error at {rows['T'][bad[0]]:.1f} K {rows['error'][bad[0]]:.3f}, at {rows['T'][bad[-1]]:.1f} K {rows['error'][bad[-1]]:.3f}")
    cases = ("T = 270 to 330 K in steps of 2.5 K, p = 1e5 Pa; start N2 1, H2O 0.02, H2O_l 0.02 mol; ln K from "
             "Nasa9LogK with NASA-9 names N2, H2O, H2O_l_s; default options")
    rows["provenance"] = provenance(dev, "WATER in run_equilibrium.py", "<out_dir>", cases)
    return rows


def run_ho(dev):
    op = options(HO)
    eq = on(EquilibriumTP(op), dev)
    lk = Nasa9LogK(op)
    comp = np.array([[2, 0], [0, 2], [2, 1], [1, 1], [1, 0], [0, 1]], dtype=float)
    rows = {"T": [], "log_k": [], "x": [], "status": [], "iterations": [], "error": [], "element_drift": []}
    p = 1.0e5
    n0l = [2.0, 1.0, 1.0e-6, 1.0e-6, 1.0e-6, 1.0e-6]
    for t in np.arange(1500.0, 5001.0, 250.0):
        log_k = lk(tens(float(t), dev), tens(p, dev))
        n, _, diag = eq(tens(float(t), dev), tens(p, dev), tens(n0l, dev), log_k)
        n = n.cpu().numpy()
        diag = diag.cpu().tolist()
        drift = np.max(np.abs(n @ comp - np.array(n0l) @ comp) / (np.array(n0l) @ comp))
        rows["T"].append(float(t))
        rows["log_k"].append(log_k.cpu().tolist())
        rows["x"].append((n / n.sum()).tolist())
        rows["status"].append(diag[0])
        rows["iterations"].append(diag[1])
        rows["error"].append(diag[2])
        rows["element_drift"].append(float(drift))
    print(f"[R7] H-O gas: {len(rows['T'])} temperatures, statuses {sorted(set(rows['status']))}, iterations "
          f"{min(rows['iterations']):.0f} to {max(rows['iterations']):.0f}, max error {max(rows['error']):.1e}")
    print(f"[R8] H-O gas: max relative element drift {max(rows['element_drift']):.1e}")
    i = rows["T"].index(3500.0)
    print(f"[R9] H-O gas at 3500 K: x(H2O) = {rows['x'][i][2]:.3f}, x(OH) = {rows['x'][i][3]:.3f}, "
          f"x(H) = {rows['x'][i][4]:.3f}")
    cases = ("T = 1500 to 5000 K in steps of 250 K, p = 1e5 Pa; start H2 2, O2 1 and 1e-6 mol of H2O, OH, H, O; "
             "ln K from Nasa9LogK; max-iter 100")
    rows["provenance"] = provenance(dev, "HO in run_equilibrium.py", "<out_dir>", cases)
    return rows


def run_status(dev):
    out = {}
    op = options(WATER)
    lk = Nasa9LogK(op, ["N2", "H2O", "H2O_l_s"])
    t, p = tens(300.0, dev), tens(1.0e5, dev)
    log_k = lk(t, p)
    eq = on(EquilibriumTP(op), dev)

    def case(name, solver, n0, note):
        n, gain, diag = solver(t, p, tens(n0, dev), log_k)
        out[name] = {"start": n0, "result": n.cpu().tolist(), "gain": gain.cpu().flatten().tolist(),
                     "diag": diag.cpu().tolist(), "note": note}
        print(f"[S] {name}: diag {[float(f'{v:.3g}') for v in out[name]['diag']]}, "
              f"gain {[float(f'{v:.4g}') for v in out[name]['gain']]}, result {[float(f'{v:.4g}') for v in out[name]['result']]}")
        return n

    n_eq = case("converged", eq, [1.0, 0.1, 0.1], "default options")
    case("restart_from_solution", eq, n_eq.cpu().tolist(), "input is the converged state")
    case("zero_amount", eq, [1.0, 0.1, 0.0], "one amount not above mole-floor")
    eq1 = on(EquilibriumTP(options(WATER.replace("reactions:", "equilibrium: {max-iter: 1}\nreactions:"))), dev)
    case("max_iter_1", eq1, [1.0, 0.1, 0.1], "max-iter 1")
    case("phase_must_vanish", eq, [1.0, 0.01, 0.01], "total water below saturation")
    w = eq(t, p, tens([1.0, 0.1, 0.1], dev), log_k, True)[0]
    print(f"[S] warm_start=True changes the result by {float((w - n_eq).abs().max()):.1e}")
    out["provenance"] = provenance(dev, "WATER in run_equilibrium.py", "<out_dir>",
                                   "T = 300 K, p = 1e5 Pa, ln K from Nasa9LogK; starts as listed per case")
    return out


def compare(dir_a, dir_b):
    """Status, iteration and result differences between two runs, for example CPU against CUDA."""
    load = lambda d, n: json.loads((Path(d) / f"{n}.json").read_text())
    a, b = load(dir_a, "flash_binary"), load(dir_b, "flash_binary")
    ok = [i for i, s in enumerate(a["status"]) if s == 0]
    print(f"[X1] binary: statuses equal {a['status'] == b['status']}; iteration counts differ in "
          f"{sum(x != y for x, y in zip(a['iterations'], b['iterations']))} of {len(a['p'])} cells, all with status "
          f"{sorted(set(a['status'][i] for i in range(len(a['p'])) if a['iterations'][i] != b['iterations'][i]))}")
    print(f"[X2] binary status-0 cells: max |liquid fraction difference| = "
          f"{max(abs(a['liquid_fraction'][i] - b['liquid_fraction'][i]) for i in ok):.1e}")
    a, b = load(dir_a, "h2o_dissociation"), load(dir_b, "h2o_dissociation")
    print(f"[X3] H-O gas: iterations equal {a['iterations'] == b['iterations']}; max |mole fraction difference| = "
          f"{np.abs(np.array(a['x']) - np.array(b['x'])).max():.1e}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("other_dir", nargs="?")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args()
    if a.compare:
        return compare(a.out_dir, a.other_dir)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    print(f"kintera {kintera.__version__}, torch {torch.__version__}, Python {platform.python_version()}, {a.device}")
    for name, fn in [("flash_binary", run_binary), ("water_condensation", run_water),
                     ("h2o_dissociation", run_ho), ("status_cases", run_status)]:
        data = fn(a.device)
        (out / f"{name}.json").write_text(json.dumps(data, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
