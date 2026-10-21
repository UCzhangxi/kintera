"""CUDA sparse QR solve (cuda_csr_solve_cusolver) against torch.linalg.solve on random diagonally dominant CSR systems,
and its singularity report at tol = 0 and tol > 0 on a rank-deficient matrix; needs a -DCUDA=ON build at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45."""
import torch, kintera as kt
torch.manual_seed(0)
print("kintera", kt.__version__, torch.cuda.get_device_name(0))
for n, dens in [(10, 0.3), (100, 0.05), (1000, 0.005)]:
    worst = 0.0
    for t in range(5):
        A = torch.rand(n, n, dtype=torch.float64) * (torch.rand(n, n) < dens)
        A += torch.diag(A.abs().sum(1) + 1.0)
        b = torch.randn(n, dtype=torch.float64)
        c = A.cuda().to_sparse_csr()
        x = kt.cuda_csr_solve_cusolver(c.crow_indices().int(), c.col_indices().int(), c.values(), b.cuda(), 0.0, 0).cpu()
        ref = torch.linalg.solve(A, b)
        worst = max(worst, ((x - ref).norm() / ref.norm()).item())
    print(f"n={n:5d} density {dens}: max rel |x - x_dense| over 5 systems = {worst:.2e}")
# rank-deficient: two equal rows
A = torch.tensor([[1., 2., 0.], [1., 2., 0.], [0., 1., 3.]], dtype=torch.float64)
b = torch.tensor([1., 1., 2.], dtype=torch.float64)
csr = A.to_sparse_csr()
for tol in (0.0, 1e-12):
    try:
        x = kt.cuda_csr_solve_cusolver(csr.crow_indices().int().cuda(), csr.col_indices().int().cuda(),
                                       csr.values().cuda(), b.cuda(), tol, 0)
        print(f"singular 3x3, tol={tol:g}: returned x = {None if x is None else x.cpu().tolist()}")
    except Exception as e:
        print(f"singular 3x3, tol={tol:g}: raised: {str(e).splitlines()[0][:150]}")
b2 = torch.tensor([1., 2., 2.], dtype=torch.float64)   # inconsistent with the two equal rows
try:
    x = kt.cuda_csr_solve_cusolver(csr.crow_indices().int().cuda(), csr.col_indices().int().cuda(), csr.values().cuda(), b2.cuda(), 0.0, 0).cpu()
    print(f"singular 3x3, inconsistent b, tol=0: returned x = {x.tolist()}, residual |Ax-b| = {(A @ x - b2).norm():.3e}, finite {bool(torch.isfinite(x).all())}")
except Exception as e:
    print(f"singular 3x3, inconsistent b, tol=0: raised: {str(e).splitlines()[0][:150]}")
