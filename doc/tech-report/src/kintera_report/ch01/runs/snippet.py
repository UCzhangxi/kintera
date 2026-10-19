import torch
from kintera import ThermoOptions, ThermoX
torch.set_default_dtype(torch.float64)

op = ThermoOptions.from_yaml("examples/jupiter.yaml")
op.max_iter(30)
thermo = ThermoX(op)
species = op.species()
xfrac = torch.zeros((1, 1, len(species)))
for name, value in {"dry": 0.86, "H2O": 0.1, "NH3": 0.03, "H2S": 0.01}.items():
    xfrac[..., species.index(name)] = value
thermo.forward(torch.tensor([200.0]), torch.tensor([1.0e5]), xfrac)
print(species)
print(xfrac)
