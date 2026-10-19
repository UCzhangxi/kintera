"""Ch. 9 (python/atm2d) numeric checks: transport operators, Ros2 order, atomic-budget projection."""
import math
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, WT, kintera, torch  # noqa: E402,F401
import kintera.atm2d as a2  # noqa: E402
from kintera.atm2d.transport import build_kb_exponential_vertical_matrix  # noqa: E402
from kintera.atm2d.conservation import project_atomic_budget  # noqa: E402
from kintera.atm2d.sources import LocalSourceLinearization  # noqa: E402

warnings.filterwarnings("ignore", message="Sparse CSR tensor support")
print(version_line())
torch.manual_seed(9)
R, G, T0 = 8.31446261815324e7, 980.665, 200.0


def verdict(val, tol, ok=None):
    ok = (val <= tol) if ok is None else ok
    return f"{val:.3e} tol {tol:.1e} {'PASS' if ok else 'FAIL'}"


def state(x1f, conc):
    nl = x1f.numel() - 1
    return a2.AtmState2D(x1f=x1f, x2f=torch.tensor([0.0, 1.0]), temperature=torch.full((1, nl), T0),
                         pressure=torch.ones(1, nl), concentration=conc)


# a. eddy diffusion, mixing-ratio form, random non-uniform grid, random n and K
nl = 30
x1f = torch.cat([torch.zeros(1), torch.cumsum(1e5 * (0.5 + torch.rand(nl)), 0)])
n = 1e15 * torch.exp(torch.randn(1, nl))
kzz = 1e6 * (0.5 + torch.rand(1, nl))
st = state(x1f, (3e-4 * n).unsqueeze(-1))
M = a2.build_eddy_diffusion_matrix(st, kzz, form="mr_diffusion", density=n)
dz = st.dx1f
scale = (kzz * st.concentration[..., 0] / dz ** 2).max()
print("a1 mr eddy, uniform mixing ratio: max|M c|/max(K c/dz^2) =",
      verdict((M.matvec(st.concentration).abs().max() / scale).item(), 1e-13))
c = n.unsqueeze(-1) * torch.rand(1, nl, 1)
tend = M.matvec(c)[0, :, 0]
print("a2 mr eddy, random c: |sum(dz*dc/dt)|/sum|dz*dc/dt| =",
      verdict(((dz * tend).sum().abs() / (dz * tend).abs().sum()).item(), 1e-13))


# b. molecular diffusion, isothermal, K=0, D diagonal
def mol_mats(mu, conc, x1f, nden):
    st = state(x1f, conc)
    nl, ns = conc.shape[1], conc.shape[2]
    D = 1e5 * torch.eye(ns).expand(1, nl, ns, ns).clone()
    mu = torch.tensor(mu)
    mr = a2.build_binary_diffusion_matrix(st, D, mu, form="mr_diffusion", density=nden)
    cf = a2.build_binary_diffusion_matrix(st, D, mu, form="c_diffusion", density=nden)
    ex = build_kb_exponential_vertical_matrix(st, torch.zeros(1, nl), D, mu, density=nden)
    return st, mr, cf, ex


def rel_tend(Mx, conc, k, H, rows=slice(None)):
    """max over rows of |dc_k/dt| / (D c_k / H^2)."""
    return (Mx.matvec(conc)[0, rows, k].abs() / (1e5 * conc[0, rows, k] / H ** 2)).max().item()


mu_b = 2.0
Hb = R * T0 / (mu_b * G)
x1f = torch.linspace(0.0, 4 * Hb, 9)  # dz = H/2: coarse
z = 0.5 * (x1f[:-1] + x1f[1:])
c1 = (1e15 * torch.exp(-z / Hb)).view(1, -1, 1)
st, mr, cf, ex = mol_mats([mu_b], c1, x1f, c1[..., 0])
print("b1 single species, c=exp(-z/H), dz=H/2, |dc/dt|/(D c/H^2):")
print("   mr centred :", verdict(rel_tend(mr, c1, 0, Hb), 1e-12))
print("   mr exp     :", verdict(rel_tend(ex, c1, 0, Hb), 1e-12))
v = rel_tend(cf, c1, 0, Hb)
print(f"   c-form     : {v:.3e} (expected O(1), nonzero) {'PASS' if v > 0.1 else 'FAIL'}")

mu_i = 4.0  # minor species, H_i = H_b/2
Hi = R * T0 / (mu_i * G)
errs = []
for nlb in (16, 32, 64):  # dz = H_b/4, H_b/8, H_b/16 over a fixed 4 H_b column
    x1f = torch.linspace(0.0, 4 * Hb, nlb + 1)
    z = 0.5 * (x1f[:-1] + x1f[1:])
    conc = torch.stack([1e15 * torch.exp(-z / Hb), 1e5 * torch.exp(-z / Hi)], -1).unsqueeze(0)
    st, mr, cf, ex = mol_mats([mu_b, mu_i], conc, x1f, conc.sum(-1))
    errs.append((rel_tend(mr, conc, 1, Hi, slice(1, -1)), rel_tend(mr, conc, 1, Hi), rel_tend(ex, conc, 1, Hi)))
print("b2 minor species mu_i=2*mu_b, c_i=exp(-z/H_i), |dc_i/dt|/(D c_i/H_i^2):")
print("   mr exp, worst of 3 grids :", verdict(max(e[2] for e in errs), 1e-12))
print("   mr centred interior errs :", ", ".join(f"{e[0]:.3e}" for e in errs))
for j in (1, 2):
    r = errs[j - 1][0] / errs[j][0]
    print(f"   centred interior ratio dz=H_b/{2 ** (j + 1)}->H_b/{2 ** (j + 2)}: {r:.3f} expect 4 tol 10% "
          f"{'PASS' if abs(r - 4) < 0.4 else 'FAIL'}")
print("   centred incl. boundary cells, ratio (info, one-sided rows):",
      ", ".join(f"{errs[j][1] / errs[j + 1][1]:.3f}" for j in (0, 1)))


# c. Ros2 order on dc/dt = -c, exact and 0.5x Jacobians
class Decay:
    def __init__(self, jscale):
        self.jscale = jscale

    def linearize(self, st):
        return LocalSourceLinearization(tendency=-st.concentration.clone(),
                                        jacobian=-self.jscale * torch.ones(1, 1, 1, 1))


def ros2_err(nstep, jscale):
    st = state(torch.tensor([0.0, 1.0]), torch.ones(1, 1, 1))
    for _ in range(nstep):
        r = a2.rosenbrock2_step(st, 1.0 / nstep, kzz=torch.zeros(1, 1), source_terms=[Decay(jscale)])
        st.concentration = r.concentration
    return abs(st.concentration.item() - math.exp(-1.0))


for js, lab in ((1.0, "exact J"), (0.5, "J*0.5  ")):
    e1, e2 = ros2_err(40, js), ros2_err(80, js)  # 20->40 gives 3.7 (pre-asymptotic)
    r = e1 / e2
    print(f"c  Ros2 {lab}: err(dt=1/40)={e1:.3e} err(dt=1/80)={e2:.3e} ratio {r:.3f} expect 4 tol 10% "
          f"{'PASS' if abs(r - 4) < 0.4 else 'FAIL'}")

# d. atomic-budget projection: element C, species [A (C1), B (C2), N2 fixed]
cnt = {"C": torch.tensor([1.0, 2.0, 0.0])}
fixed = torch.tensor([False, False, True])
conc = torch.stack([5e10 * (1 + torch.rand(1, 4)), 1e9 * (1 + torch.rand(1, 4)), torch.full((1, 4), 1e12)], -1)
cur = (conc * cnt["C"]).sum(-1, keepdim=True)
bud = 0.8 * cur
out = project_atomic_budget(conc, atom_counts=cnt, fixed_mask=fixed, budget={"C": bud})
v = ((out * cnt["C"]).sum(-1, keepdim=True) / bud - 1).abs().max().item()
print("d  hog total >= 1: max|total_after/budget - 1| =", verdict(v, 1e-13))
small = torch.tensor([[[0.5, 0.005, 1.0]]])
outs = project_atomic_budget(small, atom_counts=cnt, fixed_mask=fixed, budget={"C": torch.tensor([[[0.3]]])})
print(f"d' (info) hog total 0.5 < 1: total_after = {(outs * cnt['C']).sum().item():.4f} vs budget 0.3 "
      "(hog_total is clamped to >= 1, so trimming is partial below 1)")
