"""Chapter 10 checks: dense kernels of src/math (dsolve_lu, ludcmp/lubksb, luminv, leastsq, psolve,
leastsq_kkt both policies, constrained_newton_step), compiled from the pinned headers into a scratch
shared library and called through ctypes. Oracles: numpy (solve, inv, lstsq, pinv) and a brute-force
enumeration of active sets for the convex constrained least-squares problem."""
import ctypes, itertools, os, shutil, subprocess, sys, tempfile
import numpy as np
from common import kintera, torch, version_line, WT  # noqa: F401
import pydisort

print(version_line())
SRC = r'''
#include <cmath>  // core.h uses fabs/sqrt without including <cmath> (S10-6)
#include <kintera/math/core.h>
#include <kintera/math/ludcmp.h>
#include <kintera/math/lubksb.h>
#include <kintera/math/luminv.h>
#include <kintera/math/leastsq.h>
#include <kintera/math/psolve.h>
#include <kintera/math/constrained_newton.h>
using namespace kintera;
extern "C" {
int k_dsolve(double* A, double* b, int n) { return dsolve_lu(A, b, n) ? 1 : 0; }
int k_lu(double* A, double* b, int n, double tol) {
  int indx[64]; int d = ludcmp(A, indx, n, nullptr, tol);
  if (d != 0) lubksb(b, A, indx, n); return d; }
int k_luminv(double* Y, double* A, int n) {
  int indx[64]; int d = ludcmp(A, indx, n); if (d != 0) luminv(Y, A, indx, n); return d; }
void k_leastsq(double* b, const double* a, int n1, int n2) { leastsq(b, a, n1, n2); }
void k_mmdot_t(double* r, const double* a, const double* b, int n1, int n2, int n3) { mmdot_t(r, a, b, n1, n2, n3); }
void k_psolve(double* b, const double* A, int n) { psolve(b, A, n); }
int k_kkt(double* b, const double* a, const double* c, const double* d, int n1, int n2, int n3, int neq,
          int* it, int policy) {
  return policy == 0 ? leastsq_kkt(b, a, c, d, n1, n2, n3, neq, it)
                     : leastsq_kkt_feasible_origin(b, a, c, d, n1, n2, n3, neq, it); }
int k_cnewton(double* b, const double* a, const double* c, const double* d, int n, int nc, int* it) {
  return constrained_newton_step(b, a, c, d, n, nc, it); }
}
'''
tmp = tempfile.mkdtemp()
try:
    with open(os.path.join(tmp, "h.cpp"), "w") as f:
        f.write(SRC)
    lib_path = os.path.join(tmp, "libk10.so")
    cmd = ["c++", "-std=c++17", "-O2", "-shared", "-fPIC", "-I", WT, "-I", os.path.join(WT, "build"),
           "-I", os.path.dirname(pydisort.__file__), os.path.join(tmp, "h.cpp"), "-o", lib_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:]); print("compile FAIL"); sys.exit(1)
    L = ctypes.CDLL(lib_path)
finally:
    pass
P = ctypes.POINTER(ctypes.c_double)
IP = ctypes.POINTER(ctypes.c_int)


def ptr(x):
    return x.ctypes.data_as(P)


def dsolve(A, b):
    A2 = np.ascontiguousarray(A, float).copy(); b2 = np.array(b, float)
    ok = L.k_dsolve(ptr(A2), ptr(b2), len(b2)); return ok, b2


def lu(A, b, tol=0.0):
    A2 = np.ascontiguousarray(A, float).copy(); b2 = np.array(b, float)
    d = L.k_lu(ptr(A2), ptr(b2), len(b2), ctypes.c_double(tol)); return d, b2


def kkt(A, b, C, d, neq=0, policy=0, max_iter=50):
    n1, n2 = A.shape; n3 = C.shape[0]
    bb = np.zeros(max(n1, n2)); bb[:n1] = b
    it = ctypes.c_int(max_iter)
    s = L.k_kkt(ptr(bb), ptr(np.ascontiguousarray(A, float)), ptr(np.ascontiguousarray(C, float)),
                ptr(np.ascontiguousarray(d, float)), n1, n2, n3, neq, ctypes.byref(it), policy)
    return s, bb[:n2], it.value


def brute(A, b, C, d, neq=0):
    """Global minimum of 1/2|Ax-b|^2 s.t. C x <= d (first neq rows equal) by enumerating active sets."""
    n3, n2 = C.shape; best = None
    for k in range(n3 - neq + 1):
        for W in itertools.combinations(range(neq, n3), k):
            rows = list(range(neq)) + list(W)
            if len(rows) > n2:
                continue
            Cw = C[rows]
            K = np.block([[A.T @ A, Cw.T], [Cw, np.zeros((len(rows), len(rows)))]])
            try:
                sol = np.linalg.solve(K, np.concatenate([A.T @ b, d[rows]]))
            except np.linalg.LinAlgError:
                continue
            x = sol[:n2]
            if np.all(C[neq:] @ x <= d[neq:] + 1e-10) and np.allclose(C[:neq] @ x, d[:neq], atol=1e-10):
                f = 0.5 * np.sum((A @ x - b) ** 2)
                if best is None or f < best[0] - 1e-14:
                    best = (f, x)
    return best[1]


def kkt_residuals(A, b, C, d, x, neq=0):
    """Stationarity, dual feasibility, complementarity, primal feasibility (unscaled, relative)."""
    g = A.T @ (A @ x - b); s = C @ x - d
    act = [i for i in range(len(d)) if i < neq or abs(s[i]) <= 1e-9 * (1 + abs(d[i]))]
    mu = np.linalg.lstsq(C[act].T, -g, rcond=None)[0] if act else np.zeros(0)
    stat = np.linalg.norm(g + C[act].T @ mu) / (1 + np.linalg.norm(A.T @ b))
    dual = -min([0.0] + [mu[j] for j, i in enumerate(act) if i >= neq])
    prim = max(0.0, np.max(s[neq:])) if len(d) > neq else 0.0
    comp = max([0.0] + [abs(mu[j] * s[i]) for j, i in enumerate(act)])
    return stat, dual, comp, prim


rng = np.random.default_rng(10)
eps = np.finfo(float).eps

# (a) dsolve_lu backward error
be = 0.0; fe = 0.0
for _ in range(300):
    n = int(rng.integers(2, 9)); A = rng.normal(size=(n, n)); b = rng.normal(size=n)
    ok, x = dsolve(A, b)
    be = max(be, np.linalg.norm(A @ x - b, np.inf) / (np.linalg.norm(A, np.inf) * np.linalg.norm(x, np.inf) + np.linalg.norm(b, np.inf)))
    fe = max(fe, np.linalg.norm(x - np.linalg.solve(A, b)) / np.linalg.norm(x) / np.linalg.cond(A))
print(f"(a) dsolve_lu, 300 random systems n=2..8: max normwise backward error {be:.2e} (tol 64 eps = {64*eps:.1e}); "
      f"max forward error / cond {fe:.2e} vs numpy.linalg.solve (tol 1e-13) {'PASS' if be < 64*eps and fe < 1e-13 else 'FAIL'}")

# (b) singularity detection: exact zero only, scale invariant
ok1, _ = dsolve(np.array([[1., 2.], [2., 4.]]), [1., 1.])
ok2, x2 = dsolve(1e-300 * np.array([[2., 1.], [1., 3.]]), [1e-300, 1e-300])
u = rng.normal(size=3); v = rng.normal(size=3)
ok3, x3 = dsolve(np.outer(u, v), [1., 2., 3.])
print(f"(b1) dsolve_lu returns false on an exactly singular 2x2 ({ok1 == 0}) and true on a regular matrix scaled by 1e-300 "
      f"(x err {np.max(np.abs(x2 - np.linalg.solve([[2., 1.], [1., 3.]], [1., 1.]))):.1e}) {'PASS' if ok1 == 0 and ok2 == 1 else 'FAIL'}")
print(f"(b2) rank-1 3x3 (numerically singular, round-off pivots): dsolve_lu returns {bool(ok3)}, max|x| = {np.max(np.abs(x3)):.1e}; "
      f"no fallback to psolve is triggered for this case INFO")

# (c) ludcmp + lubksb backward error and permutation sign
be = 0.0; sgn_ok = True
for _ in range(300):
    n = int(rng.integers(2, 9)); A = rng.normal(size=(n, n)); b = rng.normal(size=n)
    d, x = lu(A, b)
    be = max(be, np.linalg.norm(A @ x - b, np.inf) / (np.linalg.norm(A, np.inf) * np.linalg.norm(x, np.inf) + np.linalg.norm(b, np.inf)))
    # sign check: det(A) = d * prod(diag(U)); U is the upper triangle left in A2 by ludcmp
    A3 = np.ascontiguousarray(A).copy(); dd = L.k_lu(ptr(A3), ptr(np.zeros(n)), n, ctypes.c_double(0.0))
    sgn_ok &= np.isclose(dd * np.prod(np.diag(A3)), np.linalg.det(A), rtol=1e-10)
print(f"(c) ludcmp+lubksb, 300 random systems: max backward error {be:.2e} (tol {64*eps:.1e}); "
      f"d * prod(diag U) = det(A) to 1e-10 in all cases: {sgn_ok} {'PASS' if be < 64*eps and sgn_ok else 'FAIL'}")

# (d) pivot tolerance is relative to the row scale
B = np.array([[1., 1., 0.], [1., 1. + 1e-13, 0.], [0., 0., 1.]])
d0, _ = lu(B, np.ones(3), 0.0); d1, _ = lu(B, np.ones(3), 1e-12)
S = np.diag([1e150, 1e-150, 1e100]) @ B
d2, _ = lu(S, np.ones(3), 1e-12); d3, _ = lu(S, np.ones(3), 0.0)
print(f"(d) ludcmp scaled pivot ~1e-13: accepted at tol 0 ({d0 != 0}), refused at tol 1e-12 ({d1 == 0}); after scaling rows "
      f"by 1e150, 1e-150, 1e100 the same verdicts ({d3 != 0}, {d2 == 0}) {'PASS' if d0 and not d1 and d3 and not d2 else 'FAIL'}")

# (e) luminv and leastsq against numpy
A = rng.normal(size=(5, 5)); Y = np.zeros((5, 5)); A2 = A.copy()
L.k_luminv(ptr(Y), ptr(A2), 5)
e1 = np.max(np.abs(Y - np.linalg.inv(A))) / np.max(np.abs(np.linalg.inv(A)))
A = rng.normal(size=(8, 3)); b = rng.normal(size=8); bb = b.copy()
L.k_leastsq(ptr(bb), ptr(np.ascontiguousarray(A)), 8, 3)
e2 = np.max(np.abs(bb[:3] - np.linalg.lstsq(A, b, rcond=None)[0]))
print(f"(e) luminv vs numpy.linalg.inv rel {e1:.1e}; leastsq (normal equations) vs numpy.linalg.lstsq {e2:.1e} (tol 1e-12) "
      f"{'PASS' if e1 < 1e-12 and e2 < 1e-12 else 'FAIL'}")

# (f) mmdot_t
a = rng.normal(size=(3, 4)); bm = rng.normal(size=(2, 4)); r = np.zeros((3, 2))
L.k_mmdot_t(ptr(r), ptr(a), ptr(bm), 3, 4, 2)
e = np.max(np.abs(r - a @ bm.T))
print(f"(f) mmdot_t against a b^T: max error {e:.2e} (tol 1e-14) {'PASS' if e < 1e-14 else 'EXPECTED-FAIL (S10-1, already in the report Limits)'}")


# (g) psolve against numpy pinv
def psolve(A, b):
    bb = np.array(b, float); L.k_psolve(ptr(bb), ptr(np.ascontiguousarray(A, float)), len(bb)); return bb


def perr(A, b):
    ref = np.linalg.pinv(A, rcond=1e-6) @ b
    return np.linalg.norm(psolve(A, b) - ref) / np.linalg.norm(ref)


A4 = rng.normal(size=(4, 4)); b4 = rng.normal(size=4)
R3 = rng.normal(size=(4, 3)) @ rng.normal(size=(3, 4))
print(f"(g1) psolve n=4 full rank rel err {perr(A4, b4):.1e}; rank-3 4x4 vs pinv (cut sigma/sigma_max 1e-6) {perr(R3, b4):.1e} "
      f"(tol 1e-8) {'PASS' if perr(A4, b4) < 1e-8 and perr(R3, b4) < 1e-8 else 'FAIL'}")
errs = {}
for n in (6, 8, 10, 12, 16):
    errs[n] = max(perr(np.eye(n) + 0.5 * rng.normal(size=(n, n)), rng.normal(size=n)) for _ in range(5))
print("(g2) psolve vs pinv, worst of 5 well-conditioned matrices per n: " + ", ".join(f"n={n} {e:.1e}" for n, e in errs.items())
      + f" (tol 1e-8) {'PASS' if max(errs.values()) < 1e-8 else 'EXPECTED-FAIL (S10-2: 100 Jacobi rotations in total)'}")
sc = {s: perr(s * A4, s * b4) for s in (1e-3, 1e-6, 1e-7, 1e-9)}
print("(g3) psolve on A scaled by s (exact answer unchanged): " + ", ".join(f"s={s:.0e} {e:.1e}" for s, e in sc.items())
      + f" (tol 1e-8) {'PASS' if max(sc.values()) < 1e-8 else 'EXPECTED-FAIL (S10-3: absolute 1e-12 off-diagonal stop)'}")

# (h) leastsq_kkt general policy against brute-force active-set enumeration; KKT conditions
nok = 0; worst = 0.0; kres = np.zeros(4); stat_counts = {}; fails = []
for t in range(60):
    n1, n2, n3 = 6, 4, 5
    A = rng.normal(size=(n1, n2)); b = 3 * rng.normal(size=n1); C = rng.normal(size=(n3, n2)); d = rng.uniform(0.1, 1, n3)
    s, x, it = kkt(A, b, C, d)
    stat_counts[s] = stat_counts.get(s, 0) + 1
    if s == 0:
        xr = brute(A, b, C, d); worst = max(worst, np.max(np.abs(x - xr)) / (1 + np.max(np.abs(xr))))
        kres = np.maximum(kres, kkt_residuals(A, b, C, d, x)); nok += 1
    else:
        fails.append((A, b, C, d))
print(f"(h1) leastsq_kkt (general), 60 random 6x4 problems with 5 inequalities (x = 0 feasible): status counts {stat_counts}; "
      f"converged cases: max rel diff to brute-force optimum {worst:.1e} (tol 1e-9) {'PASS' if worst < 1e-9 else 'FAIL'}")
still = [kkt(*f, max_iter=1000) for f in fails]
gap = [np.max(np.abs(r[1] - brute(*f))) for r, f in zip(still, fails)]
print(f"(h1c) the {len(fails)} non-converged problems rerun with max_iter=1000: statuses {[r[0] for r in still]}, "
      f"distance of the returned x to the optimum {', '.join(f'{g:.2f}' for g in gap)} (every convex problem with x = 0 "
      f"feasible should converge) {'PASS' if all(r[0] == 0 for r in still) else 'EXPECTED-FAIL (S10-4: active-set cycling)'}")
print(f"(h2) KKT residuals of those results: stationarity {kres[0]:.1e}, dual infeasibility {kres[1]:.1e}, "
      f"complementarity {kres[2]:.1e}, primal infeasibility {kres[3]:.1e} (tol 1e-9) {'PASS' if np.all(kres < 1e-9) else 'FAIL'}")
# equality + inequality
A = rng.normal(size=(5, 3)); b = rng.normal(size=5); C = rng.normal(size=(3, 3)); d = np.array([0.3, 0.2, 0.1])
s, x, it = kkt(A, b, C, d, neq=1); xr = brute(A, b, C, d, neq=1)
print(f"(h3) one equality + two inequalities: status {s}, diff to brute force {np.max(np.abs(x - xr)):.1e} (tol 1e-10) "
      f"{'PASS' if s == 0 and np.max(np.abs(x - xr)) < 1e-10 else 'FAIL'}")
# scaling invariance: units of columns and of constraint rows must not matter
A = rng.normal(size=(6, 4)); b = 3 * rng.normal(size=6); C = rng.normal(size=(5, 4)); d = rng.uniform(0.1, 1, 5)
Dc = np.diag([1e-6, 1., 1e4, 1e8]); Dr = np.diag([1e5, 1., 1e-7, 1., 1e3])
s0, x0, _ = kkt(A, b, C, d); s1, x1, _ = kkt(A @ Dc, b, Dr @ C @ Dc, Dr @ d)
e = np.max(np.abs(Dc @ x1 - x0)) / np.max(np.abs(x0))
print(f"(h4) column scaling 1e-6..1e8 and row scaling 1e-7..1e5: status {s0},{s1}, rel diff {e:.1e} (tol 1e-9) "
      f"{'PASS' if s0 == 0 and s1 == 0 and e < 1e-9 else 'FAIL'}")
# max_iter exhaustion is reported, not silent
A = rng.normal(size=(6, 4)); b = 3 * rng.normal(size=6); C = rng.normal(size=(5, 4)); d = rng.uniform(0.1, 1, 5)
s_full, _, it_full = kkt(A, b, C, d); s1, _, it1 = kkt(A, b, C, d, max_iter=1)
print(f"(h5) iteration cap: full run status {s_full} in {it_full} iterations; with max_iter=1 status {s1} "
      f"(2 expected when more than 1 iteration is needed) {'PASS' if (it_full == 1 or s1 == 2) else 'FAIL'}")

# (i) feasible-origin policy (square A: direct form first)
worst = 0.0; nok = 0; stat_counts = {}; fails = []
for t in range(60):
    n = 4; A = rng.normal(size=(n, n)); b = 3 * rng.normal(size=n); C = rng.normal(size=(5, n)); d = rng.uniform(0.0, 1, 5)
    s, x, it = kkt(A, b, C, d, policy=1)
    stat_counts[s] = stat_counts.get(s, 0) + 1
    if s == 0:
        xr = brute(A, b, C, d); worst = max(worst, np.max(np.abs(x - xr)) / (1 + np.max(np.abs(xr)))); nok += 1
    else:
        fails.append((A, b, C, d))
print(f"(i1) leastsq_kkt_feasible_origin, 60 random square problems, 5 generic inequalities, d >= 0: status counts "
      f"{stat_counts}; converged cases: max rel diff to brute force {worst:.1e} (tol 1e-9) {'PASS' if worst < 1e-9 else 'FAIL'}")
still = [kkt(*f, policy=1, max_iter=1000) for f in fails]
print(f"(i1c) the {len(fails)} non-converged problems rerun with max_iter=1000: statuses {[r[0] for r in still]} "
      f"{'PASS' if all(r[0] == 0 for r in still) else 'EXPECTED-FAIL (S10-5: active-set cycling, policy used by equilibrate_tp/uv)'}")
A = np.array([[2., 1.], [1., 3.]]); C = np.array([[1., 0.], [0., 1.]]); dneg = np.array([-1e-3, 1.])
s, x, _ = kkt(A, np.array([1., 1.]), C, dneg, policy=1)
print(f"(i2) x = 0 infeasible (d_0 = -1e-3): status {s} (1 expected) {'PASS' if s == 1 else 'FAIL'}")
# bound snapping: x_j returned exactly on its bound
A = np.array([[1., 0.2], [0.1, 1.]]); C = np.array([[1., 0.], [0., 1.]]); d = np.array([0.3, 7.0])
s, x, _ = kkt(A, np.array([5., 0.]), C, d, policy=1)
print(f"(i3) single-coefficient active row: x_0 = {float(x[0])!r} (bound 0.3 exactly) {'PASS' if s == 0 and x[0] == 0.3 else 'FAIL'}")

# (j) constrained_newton_step
A = rng.normal(size=(3, 3)) + 3 * np.eye(3); g = rng.normal(size=3)
C = -np.eye(3); dlim = np.array([0.5, 0.5, 0.5])
bb = g.copy(); it = ctypes.c_int(20)
s = L.k_cnewton(ptr(bb), ptr(A), ptr(np.ascontiguousarray(C)), ptr(dlim), 3, 3, ctypes.byref(it))
e1 = np.max(np.abs(bb - np.linalg.solve(A, g)))
p = np.linalg.solve(A, g); dz = np.where(-p > 0, 0.0, 1.0)  # rows pointing out of a zero-slack bound
bb2 = g.copy(); it2 = ctypes.c_int(20)
s2 = L.k_cnewton(ptr(bb2), ptr(A), ptr(np.ascontiguousarray(C)), ptr(dz), 3, 3, ctypes.byref(it2))
xr = brute(A, g, C, dz)
e2 = np.max(np.abs(bb2 - xr))
print(f"(j) constrained_newton_step: bounds with slack keep the direct solve (status {s}, iters {it.value}, diff {e1:.1e}); "
      f"zero-slack bounds crossed -> KKT (status {s2}, diff to brute force {e2:.1e}) (tol 1e-10) "
      f"{'PASS' if s == 0 and it.value == 1 and e1 < 1e-10 and s2 == 0 and e2 < 1e-10 else 'FAIL'}")
shutil.rmtree(tmp, ignore_errors=True)
