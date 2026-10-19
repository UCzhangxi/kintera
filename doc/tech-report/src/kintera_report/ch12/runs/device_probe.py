"""Device and dtype contract of kintera modules on a CUDA build at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45.
python -P device_probe.py <case>   (one case per process: an illegal access poisons the CUDA context)"""
import os, sys, torch, kintera as kt
JUP = os.path.join(os.environ["KINTERA_REPO"], "tests", "jupiter.yaml")
case = sys.argv[1]
cuda = torch.device("cuda")

def thermo_x_inputs(th, dev, dtype):
    names = th.options.species()
    T = torch.tensor([200.0], dtype=dtype, device=dev); P = torch.tensor([1e5], dtype=dtype, device=dev)
    x = torch.zeros(1, len(names), dtype=dtype, device=dev)
    x[0, names.index("H2O")] = 3e-3; x[0, names.index("dry")] = 1 - 3e-3
    return T, P, x

def report(f):
    try:
        out = f()
        if case.startswith("to_"):
            print(f"{case}: returned {type(out).__name__}"); return
        torch.cuda.synchronize()
        print(f"{case}: OK")
    except Exception as e:
        print(f"{case}: {type(e).__name__}: {str(e).splitlines()[0][:160]}")

if case.startswith("to_"):
    kind, arg = case[3:].split(":")
    mk = {"thermox": lambda: kt.ThermoX(kt.ThermoOptions.from_yaml(JUP)),
          "thermoy": lambda: kt.ThermoY(kt.ThermoOptions.from_yaml(JUP)),
          "kinetics": lambda: kt.Kinetics(kt.KineticsOptions.from_yaml(JUP)),
          "equilibrium": lambda: kt.EquilibriumTP(kt.EquilibriumOptions().components(["A", "B"]).phases(["gas"])
                                                  .phase_ids([0, 0]).reactions(["A <=> B"]).gas_phase(0))}[kind]()
    a = {"device": cuda, "str": "cuda", "dtype": torch.float32}[arg]
    def f():
        r = mk.to(a)
        print(f"   after .to({arg}): stoich on {mk.buffer('stoich').device}, dtype {mk.buffer('stoich').dtype}")
        return r
    report(f)
elif case == "thermox_module_cpu_inputs_cuda":
    th = kt.ThermoX(kt.ThermoOptions.from_yaml(JUP))
    report(lambda: th.forward(*thermo_x_inputs(th, cuda, torch.float64)))
elif case == "thermox_both_cuda":
    th = kt.ThermoX(kt.ThermoOptions.from_yaml(JUP)); th.to(cuda)
    report(lambda: th.forward(*thermo_x_inputs(th, cuda, torch.float64)))
elif case == "thermox_cuda_float32_inputs":
    th = kt.ThermoX(kt.ThermoOptions.from_yaml(JUP)); th.to(cuda)
    report(lambda: th.forward(*thermo_x_inputs(th, cuda, torch.float32)))
elif case == "thermox_cuda_both_float32":
    th = kt.ThermoX(kt.ThermoOptions.from_yaml(JUP)); th.to(cuda); th.to(torch.float32)
    report(lambda: th.forward(*thermo_x_inputs(th, cuda, torch.float32)))
elif case == "thermox_cpu_half":
    th = kt.ThermoX(kt.ThermoOptions.from_yaml(JUP))
    report(lambda: th.forward(*thermo_x_inputs(th, "cpu", torch.float16)))
elif case == "equilibrium_module_cpu_inputs_cuda":
    eq = kt.EquilibriumTP(kt.EquilibriumOptions().components(["A", "B"]).phases(["gas"]).phase_ids([0, 0])
                          .reactions(["A <=> B"]).gas_phase(0))
    t = lambda v: torch.tensor(v, dtype=torch.float64, device=cuda)
    report(lambda: eq(t(1000.0), t(1e5), t([0.8, 0.2]), t([0.0])))
elif case == "equilibrium_mixed_devices":
    eq = kt.EquilibriumTP(kt.EquilibriumOptions().components(["A", "B"]).phases(["gas"]).phase_ids([0, 0])
                          .reactions(["A <=> B"]).gas_phase(0))
    report(lambda: eq(torch.tensor(1000.0, dtype=torch.float64), torch.tensor(1e5, dtype=torch.float64, device=cuda),
                      torch.tensor([0.8, 0.2], dtype=torch.float64, device=cuda), torch.zeros(1, dtype=torch.float64, device=cuda)))
elif case == "kinetics_module_cpu_inputs_cuda":
    kin = kt.Kinetics(kt.KineticsOptions.from_yaml(JUP))
    n = len(kin.options.species())
    report(lambda: kin.forward(torch.tensor([200.0], dtype=torch.float64, device=cuda),
                               torch.tensor([1e5], dtype=torch.float64, device=cuda),
                               torch.full((1, n), 1e-3, dtype=torch.float64, device=cuda)))
elif case == "kinetics_both_cuda":
    kin = kt.Kinetics(kt.KineticsOptions.from_yaml(JUP)); kin.to(cuda)
    n = len(kin.options.species())
    report(lambda: kin.forward(torch.tensor([200.0], dtype=torch.float64, device=cuda),
                               torch.tensor([1e5], dtype=torch.float64, device=cuda),
                               torch.full((1, n), 1e-3, dtype=torch.float64, device=cuda)))
elif case == "thermoy_module_cpu_inputs_cuda":
    th = kt.ThermoY(kt.ThermoOptions.from_yaml(JUP))
    ny = len(th.options.species()) - 1
    rho = torch.tensor([0.2], dtype=torch.float64, device=cuda)
    y = torch.full((ny, 1), 1e-3, dtype=torch.float64, device=cuda)
    report(lambda: th.forward(rho, torch.tensor([1.0e5], dtype=torch.float64, device=cuda), y))
