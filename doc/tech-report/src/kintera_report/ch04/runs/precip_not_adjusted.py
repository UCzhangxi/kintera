"""A condensate outside every nucleation reaction is not adjusted (@sec-ch04-conditions): one ThermoX cell of
tests/jupiter.yaml at 300 K and 1e5 Pa with x(H2O) = x(H2O(l,p)) = 1e-3.

    KINTERA_REPO=<kintera checkout> python -P precip_not_adjusted.py
"""
import sys
from pathlib import Path
import torch
import kintera as kt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # common.py sits next to this script
from common import jupiter, log_rh_x

th = kt.ThermoX(kt.ThermoOptions.from_yaml(jupiter()))
names = th.options.species()
T = torch.tensor([300.])
P = torch.tensor([1e5])
x = torch.zeros(1, len(names))
x[0, names.index("H2O")] = 1e-3
x[0, names.index("H2O(l,p)")] = 1e-3
x[0, names.index("dry")] = 1 - x.sum()
before = x.clone()
d = torch.zeros(1, 1)
th.forward(T, P, x, False, d)
print("diag", d[0, 0].item())
print("x(H2O) before/after", before[0, names.index("H2O")].item(), x[0, names.index("H2O")].item())
print("x(H2O(l,p)) before/after", before[0, names.index("H2O(l,p)")].item(), x[0, names.index("H2O(l,p)")].item())
print("ln RH(H2O) after", log_rh_x(th, T, P, x)[0, 0].item())
