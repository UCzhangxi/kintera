"""Chapter 8 checks: the C++ eddy-diffusion operator (src/diffusion) and the boundary/diffusivity helpers.

Oracles are independent: a numpy finite-volume operator written from the flux formula, analytic profiles,
finite-difference Jacobians, and the textbook binary-diffusion formula. Section j adds the CPU/CUDA comparison, the
face-flux identity with the atm2d matrix on a stretched grid, the Jacobian on perturbations that keep every level
total, the limits of the C++ operator (INFO), and the ignored species_diffusion_scale of the binary-diffusion
matrix (EXPECTED-FAIL, row K27 of UCzhangxi/kintera#54).
"""
import warnings
import numpy as np
warnings.filterwarnings("ignore", message="Sparse CSR")

from common import kintera, torch, version_line

kt = kintera
print(version_line())
rng = np.random.default_rng(8)


def fv_numpy(y, K, h):
    """Independent FV operator: F = -K nbar (X_{j+1}-X_j)/h, widths: mean of spacings inside, h at the ends."""
    nz = y.shape[0]
    n = y.sum(1)
    X = y / n[:, None]
    nbar = 0.5 * (n[1:] + n[:-1])
    F = -(K * nbar / h)[:, None] * (X[1:] - X[:-1])          # (nz-1, ns), face j+1/2
    w = np.empty(nz)
    w[0], w[-1] = h[0], h[-1]
    w[1:-1] = 0.5 * (h[1:] + h[:-1])
    Fpad = np.vstack([np.zeros((1, y.shape[1])), F, np.zeros((1, y.shape[1]))])
    return -(Fpad[1:] - Fpad[:-1]) / w[:, None], w


def cpp(y, K, h):
    return kt.diffusion_tendency(torch.tensor(y), torch.tensor(K), torch.tensor(h)).numpy()


TAGS = []


def report(label, ok, text, expected_fail=None):
    if ok is None:
        tag = "INFO"
    elif expected_fail:
        tag = "EXPECTED-FAIL" if not ok else "FAIL"
    else:
        tag = "PASS" if ok else "FAIL"
    TAGS.append(tag)
    print(f"{label} {text} {tag}" + (f" ({expected_fail})" if tag == "EXPECTED-FAIL" else ""))


# ---- a: operator against the numpy FV oracle on a random non-uniform grid --------------------------
nz, ns = 17, 4
h = rng.uniform(0.3, 3.0, nz - 1) * 1e5            # cm
K = rng.uniform(1e4, 1e7, nz - 1)                  # cm^2/s
y = rng.uniform(0.1, 1.0, (nz, ns)) * np.exp(-np.arange(nz) / 4.0)[:, None] * 1e15
ref, w = fv_numpy(y, K, h)
got = cpp(y, K, h)
scale = np.abs(ref).max()
err = np.abs(got - ref).max() / scale
report("a", err < 1e-13, f"tendency vs numpy FV oracle, random grid: max rel err {err:.1e} (tol 1e-13)")
A, B, C = [t.numpy() for t in kt.diffusion_coefficients(torch.tensor(y), torch.tensor(K), torch.tensor(h))]
report("a2", A.shape == (nz,) and C[0] == 0.0 and B[-1] == 0.0,
       f"coefficient shapes {A.shape}, C_0 = {C[0]}, B_N-1 = {B[-1]} (exact)")

# ---- b, c, d: identities ---------------------------------------------------------------------------
Xu = rng.uniform(0.1, 1.0, ns)
yu = y.sum(1)[:, None] * Xu[None, :] / Xu.sum()
eb = np.abs(cpp(yu, K, h)).max() / scale
report("b", eb < 1e-13, f"uniform mixing ratio: max |tendency| / scale {eb:.1e} (tol 1e-13)")
ec = np.abs(got.sum(1)).max() / scale
report("c", ec < 1e-13, f"level total sum_s dy/dt: max / scale {ec:.1e} (tol 1e-13)")
ew = np.abs((w[:, None] * got).sum(0)).max() / (scale * w.max())
report("d1", ew < 1e-13, f"weighted column sum_j w_j dy/dt (w = h_1/2, Delta_j, h_N-3/2): {ew:.1e} (tol 1e-13)")
eu = np.abs(got.sum(0)).max() / scale
report("d2", None, f"unweighted column sum_j dy/dt on the same grid: {eu:.1e} of scale (non-zero by design)")
# atm2d cell widths for the same centres (faces at midpoints, outer faces mirrored): which total is kept?
zc = np.concatenate([[0.0], np.cumsum(h)])
zf = np.concatenate([[zc[0] - h[0] / 2], 0.5 * (zc[1:] + zc[:-1]), [zc[-1] + h[-1] / 2]])
report("d3", np.allclose(np.diff(zf), w, rtol=1e-14, atol=0),
       "C++ weights equal the widths of cells with faces at centre midpoints and outer faces h/2 beyond the end centres")

# ---- e: order of accuracy on a smooth stretched grid ----------------------------------------------
L, Hn = 1.0, 0.35


def kfun(z):
    return 1.0 + 0.5 * np.sin(2.0 * z)


def order_case(N, jitter=0.0, symmetric=False):
    s = np.linspace(0.0, 1.0, N)
    zc = L * (np.exp(1.5 * s) - 1) / (np.exp(1.5) - 1)
    if jitter:
        r = np.random.default_rng(N).uniform(-jitter, jitter, N)
        r[0] = r[-1] = 0.0
        zc = zc + r * np.gradient(zc)
    hh = np.diff(zc)
    zb, zt = zc[0] - hh[0] / 2, zc[-1] + hh[-1] / 2
    lam = np.pi / (zt - zb)
    n = np.exp(-zc / Hn)
    u = (zc - zb) / (zt - zb)
    if symmetric:   # zero gradient and zero third derivative at zb, zt
        X1 = 0.5 + 0.3 * np.cos(lam * (zc - zb))
    else:           # zero gradient at zb, zt (zero boundary flux), third derivative non-zero there
        X1 = 0.5 + 0.2 * (u**2 / 2 - u**3 / 3)
    yy = np.stack([n * X1, n * (1 - X1)], 1)
    zf = 0.5 * (zc[1:] + zc[:-1])
    tend = cpp(yy, kfun(zf), hh)[:, 0]
    # exact d/dz (K n dX/dz)
    if symmetric:
        Xp = -0.3 * lam * np.sin(lam * (zc - zb))
        Xpp = -0.3 * lam**2 * np.cos(lam * (zc - zb))
    else:
        Lt = zt - zb
        Xp = 0.2 * (u - u**2) / Lt
        Xpp = 0.2 * (1 - 2 * u) / Lt**2
    Kz, Kp = kfun(zc), np.cos(2.0 * zc)
    exact = Kp * n * Xp + Kz * (-n / Hn) * Xp + Kz * n * Xpp
    e = np.abs(tend - exact)
    return e[1:-1].max(), max(e[0], e[-1])


ein, ebd = zip(*[order_case(N) for N in (41, 81, 161, 321)])
rin = [ein[i] / ein[i + 1] for i in range(3)]
rbd = [ebd[i] / ebd[i + 1] for i in range(3)]
report("e1", abs(rin[-1] - 4.0) < 0.4,
       f"interior error ratio per halving, smooth stretched grid: {', '.join(f'{r:.2f}' for r in rin)} (expect 4 +- 10%)")
report("e2", abs(rbd[-1] - 2.0) < 0.3,
       f"boundary-row error ratio per halving: {', '.join(f'{r:.2f}' for r in rbd)} (expect 2, first order, +- 15%)")
ebs = [order_case(N, symmetric=True)[1] for N in (81, 161, 321)]
report("e2b", None, f"boundary-row ratio for a profile also flat in its third derivative at the wall: "
       f"{ebs[0]/ebs[1]:.2f}, {ebs[1]/ebs[2]:.2f} (second order only by symmetry)")
ejt = [order_case(N, 0.2)[0] for N in (81, 161, 321)]
report("e3", None, f"interior error ratio with 20% random jitter: {ejt[0]/ejt[1]:.2f}, {ejt[1]/ejt[2]:.2f} "
       "(first order expected on a rough grid)")

# ---- f: relation to the atm2d eddy matrix --------------------------------------------------------
def atm2d_tend(x1f, conc, kzz_c, form, density=None):
    st = kt.AtmState2D(x1f=torch.tensor(x1f), x2f=torch.tensor([0.0, 1.0]),
                       temperature=torch.full((1, len(x1f) - 1), 200.0),
                       pressure=torch.full((1, len(x1f) - 1), 1e5),
                       concentration=torch.tensor(conc)[None])
    m = kt.build_eddy_diffusion_matrix(st, torch.tensor(kzz_c)[None], form=form,
                                       density=None if density is None else torch.tensor(density)[None])
    return m.matvec(torch.tensor(conc)[None])[0].numpy(), st


nz = 9
yv = rng.uniform(0.2, 1.0, (nz, 3)) * np.exp(-np.arange(nz) / 3.0)[:, None]
kc = rng.uniform(1.0, 5.0, nz)
x1f_u = np.linspace(0.0, 9.0, nz + 1)
t_mr, st = atm2d_tend(x1f_u, yv, kc, "mr_diffusion", yv.sum(1))
kf = 0.5 * (kc[1:] + kc[:-1])
t_cc = cpp(yv, kf, st.dx1v.numpy())
e = np.abs(t_mr - t_cc).max() / np.abs(t_cc).max()
report("f1", e < 1e-13, f"uniform grid, varying n: C++ vs atm2d mr_diffusion (density = species sum) {e:.1e} (tol 1e-13)")
t_c, _ = atm2d_tend(x1f_u, yv, kc, "c_diffusion")
e = np.abs(t_c - t_cc).max() / np.abs(t_cc).max()
report("f2", None, f"uniform grid, varying n: C++ vs atm2d c_diffusion differ by {e:.2f} of scale "
       "(the in-tree test passes only because its n is constant)")
x1f_s = np.concatenate([[0.0], np.cumsum(rng.uniform(0.5, 2.0, nz))])
t_mr, st = atm2d_tend(x1f_s, yv, kc, "mr_diffusion", yv.sum(1))
t_cc = cpp(yv, kf, st.dx1v.numpy())
e = np.abs(t_mr - t_cc).max() / np.abs(t_cc).max()
dxf = st.dx1f.numpy()
cons_atm = np.abs((dxf[:, None] * t_mr).sum(0)).max() / np.abs(dxf[:, None] * t_mr).max()
report("f3", None, f"stretched grid: C++ vs atm2d mr_diffusion differ by {e:.2f} of scale (cell widths differ); "
       f"atm2d keeps sum dx1f c to {cons_atm:.1e}")

# ---- g: Jacobian of the tendency (n = species sum is part of the state) ---------------------------
nz, ns = 7, 3
yj = rng.uniform(0.2, 1.0, (nz, ns))
hj = rng.uniform(0.5, 2.0, nz - 1)
Kj = rng.uniform(0.5, 2.0, nz - 1)
yt = torch.tensor(yj, requires_grad=True)
Jad = torch.autograd.functional.jacobian(
    lambda v: kt.diffusion_tendency(v, torch.tensor(Kj), torch.tensor(hj)), yt).reshape(nz * ns, nz * ns).numpy()
eps = 1e-6
Jfd = np.zeros((nz * ns, nz * ns))
for k in range(nz * ns):
    d = np.zeros(nz * ns)
    d[k] = eps
    Jfd[:, k] = (cpp(yj + d.reshape(nz, ns), Kj, hj) - cpp(yj - d.reshape(nz, ns), Kj, hj)).ravel() / (2 * eps)
A, B, C = [t.numpy() for t in kt.diffusion_coefficients(torch.tensor(yj), torch.tensor(Kj), torch.tensor(hj))]
T = np.diag(A) + np.diag(B[:-1], 1) + np.diag(C[1:], -1)
Jfrz = np.kron(T, np.eye(ns))
# analytic Jacobian, derived from F_s = -(K/h) nbar (X_{j+1,s} - X_{j,s})
n = yj.sum(1)
X = yj / n[:, None]
Jan = np.zeros((nz, ns, nz, ns))
wv = np.empty(nz)
wv[0], wv[-1] = hj[0], hj[-1]
wv[1:-1] = 0.5 * (hj[1:] + hj[:-1])
for f in range(nz - 1):          # face between f and f+1
    g = Kj[f] / hj[f]
    nb = 0.5 * (n[f] + n[f + 1])
    dF = np.zeros((ns, nz, ns))  # dF_s / dy_{l,r}
    for lev, sgn in ((f, -1.0), (f + 1, 1.0)):
        for r in range(ns):
            # d nbar / dy = 1/2 ; d X_{lev,s} / dy_{lev,r} = (delta_sr - X_s)/n_lev
            dF[:, lev, r] = -g * (0.5 * (X[f + 1] - X[f]) + nb * sgn * ((np.arange(ns) == r) - X[lev]) / n[lev])
    Jan[f] += -dF / wv[f]              # dy_f/dt = -(F_{f+1/2} - F_{f-1/2})/w_f
    Jan[f + 1] += dF / wv[f + 1]
Jan = Jan.reshape(nz * ns, nz * ns)
e1 = np.abs(Jad - Jfd).max() / np.abs(Jfd).max()
e2 = np.abs(Jan - Jfd).max() / np.abs(Jfd).max()
e3 = np.abs(Jfrz - Jfd).max() / np.abs(Jfd).max()
report("g1", e1 < 1e-8 and e2 < 1e-8,
       f"Jacobian: autograd vs FD {e1:.1e}, derived analytic (with dn/dy terms) vs FD {e2:.1e} (tol 1e-8)")
report("g2", None, f"frozen-n tridiagonal (A,B,C) x I differs from the true Jacobian by {e3:.2f} of its max "
       "(exact only where n is held fixed)")
Xu = rng.uniform(0.1, 1.0, ns)
yuj = n[:, None] * Xu / Xu.sum()                # uniform mixing ratio, varying n
A, B, C = [t.numpy() for t in kt.diffusion_coefficients(torch.tensor(yuj), torch.tensor(Kj), torch.tensor(hj))]
Tu = np.kron(np.diag(A) + np.diag(B[:-1], 1) + np.diag(C[1:], -1), np.eye(ns))
dv = np.zeros((nz, ns))
dv[3] = 1e-3 * yuj[3]                           # scale one level: X unchanged everywhere, n_3 changes
true = (cpp(yuj + dv, Kj, hj) - cpp(yuj, Kj, hj)).ravel()
frz = Tu @ dv.ravel()
report("g3", np.abs(true).max() < 1e-15 and np.abs(frz).max() > 1e-6,
       f"uniform X, one level scaled by 1e-3: true response {np.abs(true).max():.1e}, frozen-n Jacobian predicts "
       f"{np.abs(frz).max():.1e} (the dn/dy terms cancel it)")

# ---- h: boundary flux and velocity sources --------------------------------------------------------
x1f = np.array([0.0, 1.0e5, 2.5e5, 4.5e5, 7.0e5])      # cm
conc = rng.uniform(1e8, 1e9, (1, 4, 2))
st = kt.AtmState2D(x1f=torch.tensor(x1f), x2f=torch.tensor([0.0, 1.0]),
                   temperature=torch.full((1, 4), 150.0), pressure=torch.full((1, 4), 1e3),
                   concentration=torch.tensor(conc))
dz = np.diff(x1f)
Phi, v = 3.0e9, 0.7                                   # molecules cm^-2 s^-1, cm s^-1
lo = kt.IndexedBoundaryFluxSource(species=1, value=Phi, boundary="lower").linearize(st).tendency.numpy()
up = kt.IndexedBoundaryFluxSource(species=1, value=Phi, boundary="upper").linearize(st).tendency.numpy()
ok = (np.isclose(lo[0, 0, 1] * dz[0], Phi, rtol=1e-15) and np.isclose(up[0, -1, 1] * dz[-1], -Phi, rtol=1e-15)
      and np.count_nonzero(lo) == 1 and np.count_nonzero(up) == 1)
report("h1", ok, "flux source: dz_0 * tendency = +Phi at the bottom cell, dz_top * tendency = -Phi at the top cell "
       "(Phi = upward flux, positive into the column at the bottom, out at the top); rtol 1e-15")
lin_lo = kt.IndexedBoundaryVelocitySource(species=0, value=-v, boundary="lower").linearize(st)
lin_up = kt.IndexedBoundaryVelocitySource(species=0, value=v, boundary="upper").linearize(st)
ok = (np.isclose(lin_lo.tendency[0, 0, 0].item(), -v * conc[0, 0, 0] / dz[0], rtol=1e-15)
      and np.isclose(lin_up.tendency[0, -1, 0].item(), -v * conc[0, -1, 0] / dz[-1], rtol=1e-15)
      and np.isclose(lin_lo.jacobian[0, 0, 0, 0].item(), -v / dz[0], rtol=1e-15)
      and np.isclose(lin_up.jacobian[0, -1, 0, 0].item(), -v / dz[-1], rtol=1e-15))
report("h2", ok, "velocity source: upward velocity w gives flux w c; deposition needs w = -v_dep < 0 at the bottom, "
       "escape w > 0 at the top; tendency and Jacobian -v c/dz, -v/dz; rtol 1e-15")
# combined with the eddy matrix: column total changes only by the boundary fluxes
mat = kt.build_eddy_diffusion_matrix(st, torch.full((1, 4), 1e6), density=torch.tensor(conc.sum(-1)),
                                     form="mr_diffusion")
tt = mat.matvec(torch.tensor(conc)).numpy() + lo + up
col = (dz[None, :, None] * tt).sum(1)[0, 1]
report("h3", abs(col) / Phi < 1e-12,
       f"eddy matrix + flux in at bottom + flux out at top: d/dt sum dz c = {col/Phi:.1e} Phi (tol 1e-12)")

# ---- i: Cheng (Titan) binary diffusion coefficient -----------------------------------------------
try:
    from kintera.kinetics_base.titan.transport_diffusion import kinetics_base_titan_cheng_diffusion as cheng
except Exception as exc:  # pragma: no cover
    cheng = None
    report("i", None, f"Titan helper not importable: {exc!r}")
if cheng is not None:
    m = torch.tensor([2.016, 16.04, 28.0, 44.1])
    Tt = torch.tensor([[90.0, 150.0, 170.0, 180.0]])
    nn = torch.tensor([[1e20, 1e15, 1e11, 1e8]])
    st4 = kt.AtmState2D(x1f=torch.tensor(x1f), x2f=torch.tensor([0.0, 1.0]), temperature=Tt, pressure=Tt * 0 + 1.0,
                        concentration=torch.ones(1, 4, 4))
    D = cheng(st4, m, temperature=Tt, density=nn).numpy()
    mu = lambda mi: mi * 28.0 / (mi + 28.0)       # reduced mass with N2 (amu)
    oracle = 7.3e16 * Tt.numpy()[0, :, None] ** 0.75 / nn.numpy()[0, :, None] * \
        np.sqrt(mu(16.0) / mu(m.numpy()))[None, :]
    diag = np.diagonal(D[0], axis1=1, axis2=2)
    e = np.abs(diag / oracle - 1).max()
    off = np.abs(D[0] - np.einsum("li,ij->lij", diag, np.eye(4))).max()
    report("i1", e < 1e-14 and off == 0.0,
           f"Cheng D_i = 7.3e16 T^0.75/n sqrt(mu_CH4-N2/mu_i-N2) [cm^2/s, n in cm^-3]: max rel err {e:.1e}, "
           f"off-diagonal {off} (tol 1e-14)")
    report("i2", None, f"CH4 at 150 K, n = 1e15 cm^-3: D = {diag[1,1]:.3e} cm^2/s; "
           f"H2/CH4 ratio {diag[0,0]/diag[0,1]:.3f}")

# ---- j: CPU/CUDA, face fluxes against atm2d, Jacobian at fixed level totals, limits, K27 -------------------
rj = np.random.default_rng(80)
nz = 8
yv = rj.uniform(0.2, 1.0, (nz, 3)) * np.exp(-np.arange(nz) / 3.0)[:, None]
kc = rj.uniform(1.0, 5.0, nz)
kf = 0.5 * (kc[1:] + kc[:-1])
x1f_s = np.concatenate([[0.0], np.cumsum(1.3 ** np.arange(nz))])
t_mr, st = atm2d_tend(x1f_s, yv, kc, "mr_diffusion", yv.sum(1))
hs = st.dx1v.numpy()
t_cc = cpp(yv, kf, hs)
_, ws = fv_numpy(yv, kf, hs)
dxf = st.dx1f.numpy()
e = np.abs(dxf[:, None] * t_mr - ws[:, None] * t_cc).max() / np.abs(ws[:, None] * t_cc).max()
report("j1", e < 1e-13, f"stretched grid: dx1f * (atm2d mr_diffusion) = w * (C++), the same face fluxes: {e:.1e} "
       f"(tol 1e-13); w/dx1f = {', '.join(f'{r:.3f}' for r in ws / dxf)}")
yt = torch.tensor(yj)
v = rj.standard_normal(yj.shape) * yj
v0 = (v - v.mean(1, keepdims=True)).ravel()
e = np.abs((Jad - Jfrz) @ v0).max() / np.abs(Jfrz @ v0).max()
report("j2", e < 1e-12, f"Jacobian = frozen-n (A,B,C) x I on perturbations with zero level sums: {e:.1e} (tol 1e-12)")
if torch.cuda.is_available():
    e = np.abs(kt.diffusion_tendency(torch.tensor(y).cuda(), torch.tensor(K).cuda(), torch.tensor(h).cuda())
               .cpu().numpy() - got).max() / scale
    report("j3", e < 1e-13, f"CUDA vs CPU tendency on the grid of a: {e:.1e} (tol 1e-13)")
else:
    report("j3", None, "no GPU visible: CUDA vs CPU not run")
for label, args in (("one level", (y[:1], K[:0], h[:0])), ("batched (2, nz, ns)", (np.stack([y, y]), K, h))):
    try:
        r = kt.diffusion_tendency(*[torch.tensor(a) for a in args])
        report("j4", None, f"{label}: returns shape {tuple(r.shape)}")
    except Exception as exc:  # noqa: BLE001
        report("j4", None, f"{label}: raises {type(exc).__name__}")
y0 = y.copy()
y0[-1] = 0.0
report("j4", None, f"zero total at the top level: {int((~np.isfinite(cpp(y0, K, h))).sum())} of {y.size} entries "
       "non-finite (no guard; atm2d skips such faces)")
yc = np.concatenate([y, np.zeros((y.shape[0], 1))], 1)
yc[5, -1] = 0.2 * y[5].sum()                 # a condensate at one level, 20% of the gas total
tc = cpp(yc, K, h)
ratio = tc[:, 0] / got[:, 0]
report("j4", None, f"a species at one level with 20% of the level total moves the other species' tendencies by "
       f"x{ratio[4]:.2f}, x{ratio[5]:.2f}, x{ratio[6]:.2f} on levels 4-6 and gets |dy/dt| = "
       f"{np.abs(tc[:, -1]).max():.1e} itself (n_j counts every species passed in)")
nb = 4
x1b = np.linspace(0.0, 4.0e5, nb + 1)
cb = rj.uniform(1e8, 1e9, (1, nb, 2))
stb = kt.AtmState2D(x1f=torch.tensor(x1b), x2f=torch.tensor([0.0, 1.0]), temperature=torch.full((1, nb), 150.0),
                    pressure=torch.full((1, nb), 1e3), concentration=torch.tensor(cb))
Db = torch.zeros(1, nb, 2, 2)
Db[..., 0, 0] = 1e5
Db[..., 1, 1] = 3e5
mw = torch.tensor([28.0, 16.0])
tb = [kt.build_binary_diffusion_matrix(stb, Db, mw, include_gravity=False, species_diffusion_scale=s)
      .matvec(torch.tensor(cb)).numpy() for s in (None, torch.tensor([2.0, 1.0]))]
r0 = np.abs(tb[1][..., 0]).max() / np.abs(tb[0][..., 0]).max()
report("j5", abs(r0 - 2.0) < 1e-12, f"binary diffusion with species_diffusion_scale (2, 1): species-0 tendency "
       f"scales by {r0:.3f} (expect 2)", expected_fail="K27")
print(f"SUMMARY: {TAGS.count('PASS')} PASS, {TAGS.count('FAIL')} FAIL, {TAGS.count('EXPECTED-FAIL')} EXPECTED-FAIL, "
      f"{TAGS.count('INFO')} INFO")
