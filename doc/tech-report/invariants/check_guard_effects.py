"""Native effects for selected guards; not blanket source branch coverage."""
import json
from pathlib import Path
import torch
import kintera as kt

torch.set_default_dtype(torch.float64)
D = Path(__file__).resolve().parent
op = kt.KineticsOptions.from_yaml(str(D/'reaction.yaml'))
kin = kt.Kinetics(op)
a = op.species().index('A')
c = torch.ones(3, 2)
c[:, a] = torch.tensor([-1., 0., 1.])
T, P = torch.full((3,), 300.), torch.full((3,), 1e5)
rate, dc, _, k = kin.forward_with_rate_constants(T, P, c)
assert rate[:, 0].tolist() == [0., 0., 1.]
jac = kin.jacobian(T, c, torch.ones(3), rate, dc, None, k)
assert torch.isfinite(jac).all()
assert jac[1, 0, a].item() == 1.
th = kt.ThermoX(kt.ThermoOptions.from_yaml(str(D/'condensation.yaml')))
x = torch.tensor([[1., 0., 0.]])
v = th.compute('TPX->V', [torch.tensor([280.]), torch.tensor([1e5]), x])
# ThermoX applies the configured positive floor to an absent gas, not a cloud.
assert v[0, 1].item() == 1e-20
assert v[0, 2].item() == 0.
print(json.dumps(dict(kintera=kt.__version__, negative_zero_positive_rates=rate[:,0].tolist(),
                     derivative_at_zero=jac[1,0,a].item(), gas_floor_output=v.tolist(),
                     covered=['kinetics.cpp:327/578 concentration clamp family',
                              'thermo_x.cpp:332 gas_floor'],
                     gaps='Other source guard effects are not inferred from these checks.'), indent=2))
