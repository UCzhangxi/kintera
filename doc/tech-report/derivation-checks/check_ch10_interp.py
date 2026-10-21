"""Chapter 10 check: interpn (src/math/interpolation.cpp) compiled into a scratch torch extension.
Oracle: multilinear functions are reproduced exactly; clamping and linear extrapolation by hand."""
import os, shutil, tempfile, warnings
from common import kintera, torch, version_line, WT  # noqa: F401

print(version_line())
warnings.filterwarnings("ignore")
tmp = tempfile.mkdtemp()
src = ('#include <torch/extension.h>\n#include "interpolation.cpp"\n'
       'torch::Tensor f(std::vector<torch::Tensor> q, std::vector<torch::Tensor> c, torch::Tensor l, bool e)'
       '{ return kintera::interpn(q, c, l, e); }\n'
       'PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) { m.def("interpn", &f); }\n')
with open(os.path.join(tmp, "k10.cpp"), "w") as fh:
    fh.write(src)
from torch.utils.cpp_extension import load  # noqa: E402
mod = load("k10interp", [os.path.join(tmp, "k10.cpp")], extra_include_paths=[os.path.join(WT, "src", "math")],
           build_directory=tmp, verbose=False, extra_cflags=["-O1"])
g = torch.Generator().manual_seed(10)
x = torch.tensor([0.0, 0.3, 1.1, 2.0, 3.5])           # increasing, non-uniform
y = torch.tensor([10.0, 7.0, 6.5, 2.0])               # decreasing
X, Y = torch.meshgrid(x, y, indexing="ij")
f = lambda a, b: 1.5 + 2.0 * a - 0.7 * b + 0.3 * a * b  # multilinear
tab = torch.stack([f(X, Y), 2 * f(X, Y)], -1)          # (5, 4, 2)
qx = torch.rand(200, generator=g) * 3.5; qy = 2 + torch.rand(200, generator=g) * 8
out = mod.interpn([qx, qy], [x, y], tab, False)
e = (out[:, 0] - f(qx, qy)).abs().max().item(); e2 = (out[:, 1] - 2 * f(qx, qy)).abs().max().item()
print(f"(a) bilinear table, increasing x and decreasing y grids, 200 interior queries: max error {e:.1e}, {e2:.1e} "
      f"(tol 1e-12) {'PASS' if max(e, e2) < 1e-12 else 'FAIL'}")
nodes = mod.interpn([X.flatten(), Y.flatten()], [x, y], tab, False)[:, 0]
en = (nodes - f(X, Y).flatten()).abs().max().item()
print(f"(b) all 20 grid nodes, including the last node of each axis: max error {en:.1e} (tol 1e-13) {'PASS' if en < 1e-13 else 'FAIL'}")
qo = torch.tensor([-1.0, 5.0]); qyo = torch.tensor([12.0, 0.0])
cl = mod.interpn([qo, qyo], [x, y], tab, False)[:, 0]; ex = mod.interpn([qo, qyo], [x, y], tab, True)[:, 0]
ref_cl = f(qo.clamp(0, 3.5), qyo.clamp(2, 10)); ref_ex = f(qo, qyo)
ec = (cl - ref_cl).abs().max().item(); ee = (ex - ref_ex).abs().max().item()
print(f"(c) outside the grid: extrapolate=False gives the clamped-coordinate value (err {ec:.1e}); extrapolate=True continues "
      f"the end cells linearly, exact for a bilinear table (err {ee:.1e}) (tol 1e-12) {'PASS' if max(ec, ee) < 1e-12 else 'FAIL'}")
xq = torch.linspace(0, 1, 9); q = torch.tensor([0.37])
eq = (mod.interpn([q], [xq], (xq ** 2).unsqueeze(-1), False)[0, 0] - q[0] ** 2).abs().item()
print(f"(d) quadratic on h = 1/8: error {eq:.3e}, bound h^2/8 = {1/512:.3e} {'PASS' if eq <= 1/512 else 'FAIL'}")
xf = torch.tensor([1.0, 1.0 + 1e-9, 2.0, 3.0]); vf = torch.tensor([[0.0], [1.0], [2.0], [3.0]])
r = mod.interpn([torch.tensor([2.5])], [xf], vf, False)[0, 0].item()
print(f"(e) increasing grid whose first two nodes differ by 1e-9 (equal in float32): interpn(2.5) = {r:.3f}, "
      f"exact 2.500 {'PASS' if abs(r - 2.5) < 1e-9 else 'EXPECTED-FAIL (S10-7: direction test casts to float)'}")
shutil.rmtree(tmp, ignore_errors=True)
