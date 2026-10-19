"""Batch-axis conventions of the public kintera calls (CPU, double) at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45."""
import os, torch, kintera as kt
torch.set_default_dtype(torch.float64)
JUP = os.path.join(os.environ["KINTERA_REPO"], "tests", "jupiter.yaml")
kin = kt.Kinetics(kt.KineticsOptions.from_yaml(JUP)); n = len(kin.options.species())
r, _, _ = kin.forward(torch.full((2, 3), 200.0), torch.full((2, 3), 1e5), torch.full((2, 3, n), 1e-3))
print(f"Kinetics.forward: temp (2,3), pres (2,3), conc (2,3,{n}) -> rate {tuple(r.shape)}")
try:
    kin.forward(torch.full((3,), 200.0), torch.full((3,), 1e5), torch.full((2, 3, n), 1e-3)); print("Kinetics broadcast temp (3,) vs conc (2,3,n): OK")
except Exception as e:
    print("Kinetics broadcast temp (3,) vs conc (2,3,n):", type(e).__name__, str(e).splitlines()[0][:120])
thx = kt.ThermoX(kt.ThermoOptions.from_yaml(JUP)); names = thx.options.species()
x = torch.zeros(2, 3, len(names)); x[..., names.index("H2O")] = 3e-3; x[..., names.index("dry")] = 1 - 3e-3
g = thx.forward(torch.full((2, 3), 250.0), torch.full((2, 3), 1e5), x)
print(f"ThermoX.forward: temp (2,3), pres (2,3), xfrac (2,3,{len(names)}) -> xfrac in place, gain {tuple(g.shape)}")
thy = kt.ThermoY(kt.ThermoOptions.from_yaml(JUP)); ny = len(names) - 1
rho = torch.full((2, 3), 0.2); y = torch.full((ny, 2, 3), 1e-4)
ivol = thy.compute("DY->V", [rho, y]); U = thy.compute("VT->U", [ivol, torch.full((2, 3), 250.0)])
gy = thy.forward(rho, U, y)
print(f"ThermoY.forward: rho (2,3), intEng (2,3), yfrac ({ny},2,3) species-first -> gain {tuple(gy.shape)}")
eq = kt.EquilibriumTP(kt.EquilibriumOptions().components(["A", "B"]).phases(["gas"]).phase_ids([0, 0]).reactions(["A <=> B"]).gas_phase(0))
m, gain, d = eq(torch.tensor([1000.0, 1200.0, 1500.0]), torch.tensor(1e5), torch.tensor([0.8, 0.2]), torch.zeros(1))
print(f"EquilibriumTP: temp (3,), pres (), moles (2,), log_k (1,) broadcast -> moles {tuple(m.shape)}, gain {tuple(gain.shape)}, diag {tuple(d.shape)}")
