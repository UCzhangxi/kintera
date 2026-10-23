# Recorded derivation value changes

Old: report #100 at `fb86705d6726ab5398301c7accda064affb7b35e`; new: development CPU source build at `e357792d50639d68e9090b542edf038d2b029aa2`. Original audit evidence is preserved. Exact invocations: `python derivation-checks/<name>.py` for each diff below. These are measured outputs, not chapter-owner approvals.

```diff
diff --git a/doc/tech-report/derivation-checks/check_ch07_photolysis.out b/doc/tech-report/derivation-checks/check_ch07_photolysis.out
index c0d24a0..971667a 100644
--- a/doc/tech-report/derivation-checks/check_ch07_photolysis.out
+++ b/doc/tech-report/derivation-checks/check_ch07_photolysis.out
@@ -1,4 +1,4 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 [a1] max rel |J - trapezoid(sum_{b>=1} sigma_b F)| at T = 250, 180, 340 K: 1.110e-16 (tol 1e-13) PASS
 [a2] J / J(branch 0 included) = 0.4348: branch 0 does not count towards J INFO
 [b] rel |J(cgs, nm) - J(SI: area m2, flux per m2 per s per m of wavelength, wavelength m)|: 1.110e-16 (tol 1e-13) PASS
@@ -17,6 +17,6 @@ kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
 [h0] module grid 120-250 nm; 'O3 => O2 + O' table 200-330 nm INFO
 [h] rel |J(O3 => O2 + O) - trapezoid on its own grid| (code 4.8153e-03, oracle 4.2403e-03 s^-1): 1.356e-01 (tol 1e-12) EXPECTED-FAIL  (S7-2)
 [i1] max rel |actinic flux - F0| over the cells of the absorber-free column (4 pi J_mean = beam flux, no mu0 factor): 2.220e-16 (tol 1e-06) PASS
-[i0] tau of top cell at 150 nm = 1.800; actinic flux bottom->top / F0 = [1.     1.     1.     0.5137]; oracle [0.0273 0.0273 0.0273 0.5137] INFO
-[i2] max rel |actinic flux - Beer-Lambert from the top| (absorber in top cell): 3.560e+01 (tol 1e-06) EXPECTED-FAIL  (S7-3)
-[i3] max rel |optical depth - n sigma_total dz| for a KINETICS7 absorber, total 1e-18, channels 3e-19 + 2e-19 (code 0.5000, oracle 1.0000): 5.000e-01 (tol 1e-06) EXPECTED-FAIL  (S7-4)
+[i0] tau of top cell at 150 nm = 1.800; actinic flux bottom->top / F0 = [0.0273 0.0273 0.0273 0.5137]; oracle [0.0273 0.0273 0.0273 0.5137] INFO
+[i2] max rel |actinic flux - Beer-Lambert from the top| (absorber in top cell): 0.000e+00 (tol 1e-06) PASS  (S7-3)
+[i3] max rel |optical depth - n sigma_total dz| for a KINETICS7 absorber, total 1e-18, channels 3e-19 + 2e-19 (code 1.0000, oracle 1.0000): 4.581e-08 (tol 1e-06) PASS  (S7-4)
diff --git a/doc/tech-report/derivation-checks/check_ch10_dense.out b/doc/tech-report/derivation-checks/check_ch10_dense.out
index 0431d86..32fb9ab 100644
--- a/doc/tech-report/derivation-checks/check_ch10_dense.out
+++ b/doc/tech-report/derivation-checks/check_ch10_dense.out
@@ -1,25 +1,25 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
-(a) dsolve_lu, 300 random systems n=2..8: max normwise backward error 1.31e-16 (tol 64 eps = 1.4e-14); max forward error / cond 2.13e-16 vs numpy.linalg.solve (tol 1e-13) PASS
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
+(a) dsolve_lu, 300 random systems n=2..8: max normwise backward error 1.69e-16 (tol 64 eps = 1.4e-14); max forward error / cond 1.81e-16 vs numpy.linalg.solve (tol 1e-13) PASS
 (b1) dsolve_lu returns false on an exactly singular 2x2 (True) and true on a regular matrix scaled by 1e-300 (x err 2.8e-17) PASS
-(b2) rank-1 3x3 (numerically singular, round-off pivots): dsolve_lu returns True, max|x| = 3.5e+17; no fallback to psolve is triggered for this case INFO
-(c) ludcmp+lubksb, 300 random systems: max backward error 1.70e-16 (tol 1.4e-14); d * prod(diag U) = det(A) to 1e-10 in all cases: True PASS
+(b2) rank-1 3x3 (numerically singular, round-off pivots): dsolve_lu returns False, max|x| = 2.7e+00; no fallback to psolve is triggered for this case INFO
+(c) ludcmp+lubksb, 300 random systems: max backward error 1.55e-16 (tol 1.4e-14); d * prod(diag U) = det(A) to 1e-10 in all cases: True PASS
 (d) ludcmp scaled pivot ~1e-13: accepted at tol 0 (True), refused at tol 1e-12 (True); after scaling rows by 1e150, 1e-150, 1e100 the same verdicts (True, True) PASS
-(e) luminv vs numpy.linalg.inv rel 7.3e-16; leastsq (normal equations) vs numpy.linalg.lstsq 2.8e-16 (tol 1e-12) PASS
-(f) mmdot_t against a b^T: max error 9.70e-01 (tol 1e-14) EXPECTED-FAIL (S10-1, already in the report Limits)
-(g1) psolve n=4 full rank rel err 3.9e-13; rank-3 4x4 vs pinv (cut sigma/sigma_max 1e-6) 1.7e-14 (tol 1e-8) PASS
-(g2) psolve vs pinv, worst of 5 well-conditioned matrices per n: n=6 1.1e-13, n=8 3.1e-12, n=10 2.6e-02, n=12 9.9e-01, n=16 1.0e+00 (tol 1e-8) EXPECTED-FAIL (S10-2: 100 Jacobi rotations in total)
+(e) luminv vs numpy.linalg.inv rel 1.1e-15; leastsq (normal equations) vs numpy.linalg.lstsq 6.1e-16 (tol 1e-12) PASS
+(f) mmdot_t: REMOVED (absence verified in pinned core.h; no numerical PASS claimed)
+(g1) psolve n=4 full rank rel err 3.9e-13; rank-3 4x4 vs pinv (cut sigma/sigma_max 1e-6) 1.6e-14 (tol 1e-8) PASS
+(g2) psolve vs pinv, worst of 5 well-conditioned matrices per n: n=6 1.0e-13, n=8 3.1e-12, n=10 2.6e-02, n=12 9.9e-01, n=16 1.0e+00 (tol 1e-8) EXPECTED-FAIL (S10-2: 100 Jacobi rotations in total)
 (g3) psolve on A scaled by s (exact answer unchanged): s=1e-03 8.5e-08, s=1e-06 2.5e-01, s=1e-07 8.7e-01, s=1e-09 8.7e-01 (tol 1e-8) EXPECTED-FAIL (S10-3: absolute 1e-12 off-diagonal stop)
-(h1) leastsq_kkt (general), 60 random 6x4 problems with 5 inequalities (x = 0 feasible): status counts {0: 57, 2: 3}; converged cases: max rel diff to brute-force optimum 2.4e-15 (tol 1e-9) PASS
+(h1) leastsq_kkt (general), 60 random 6x4 problems with 5 inequalities (x = 0 feasible): status counts {0: 57, 2: 3}; converged cases: max rel diff to brute-force optimum 1.4e-15 (tol 1e-9) PASS
 (h1c) the 3 non-converged problems rerun with max_iter=1000: statuses [2, 2, 2], distance of the returned x to the optimum 0.22, 2.29, 0.02 (every convex problem with x = 0 feasible should converge) EXPECTED-FAIL (S10-4: active-set cycling)
-(h2) KKT residuals of those results: stationarity 2.0e-15, dual infeasibility 0.0e+00, complementarity 8.2e-15, primal infeasibility 8.9e-16 (tol 1e-9) PASS
+(h2) KKT residuals of those results: stationarity 2.0e-15, dual infeasibility -0.0e+00, complementarity 2.2e-14, primal infeasibility 2.4e-15 (tol 1e-9) PASS
 (h3) one equality + two inequalities: status 0, diff to brute force 2.2e-16 (tol 1e-10) PASS
-(h4) column scaling 1e-6..1e8 and row scaling 1e-7..1e5: status 0,0, rel diff 1.6e-16 (tol 1e-9) PASS
+(h4) column scaling 1e-6..1e8 and row scaling 1e-7..1e5: status 0,0, rel diff 1.9e-16 (tol 1e-9) PASS
 (h5) iteration cap: full run status 0 in 3 iterations; with max_iter=1 status 2 (2 expected when more than 1 iteration is needed) PASS
-(i1) leastsq_kkt_feasible_origin, 60 random square problems, 5 generic inequalities, d >= 0: status counts {0: 59, 2: 1}; converged cases: max rel diff to brute force 5.2e-14 (tol 1e-9) PASS
-(i1c) the 1 non-converged problems rerun with max_iter=1000: statuses [2] EXPECTED-FAIL (S10-5: active-set cycling, policy used by equilibrate_tp/uv)
+(i1) leastsq_kkt_feasible_origin, 60 random square problems, 5 generic inequalities, d >= 0: status counts {0: 60}; converged cases: max rel diff to brute force 5.3e-14 (tol 1e-9) PASS
+(i1c) the 0 non-converged problems rerun with max_iter=1000: statuses [] PASS
 (i2) x = 0 infeasible (d_0 = -1e-3): status 1 (1 expected) PASS
 (i3) single-coefficient active row: x_0 = 0.3 (bound 0.3 exactly) PASS
-(j) constrained_newton_step: bounds with slack keep the direct solve (status 0, iters 1, diff 1.1e-16); zero-slack bounds crossed -> KKT (status 0, diff to brute force 1.4e-17) (tol 1e-10) PASS
+(j) constrained_newton_step: bounds with slack keep the direct solve (status 0, iters 1, diff 1.1e-16); zero-slack bounds crossed -> KKT (status 0, diff to brute force 5.6e-17) (tol 1e-10) PASS
 Warning: leastsq_kkt maximum number of iterations reached (50).
 Warning: leastsq_kkt maximum number of iterations reached (50).
 Warning: leastsq_kkt maximum number of iterations reached (50).
@@ -27,6 +27,4 @@ Warning: leastsq_kkt maximum number of iterations reached (1000).
 Warning: leastsq_kkt maximum number of iterations reached (1000).
 Warning: leastsq_kkt maximum number of iterations reached (1000).
 Warning: leastsq_kkt maximum number of iterations reached (1).
-Warning: leastsq_kkt maximum number of iterations reached (50).
-Warning: leastsq_kkt maximum number of iterations reached (1000).
 Error: x = 0 violates constraint 0 (d = -0.001, max |d| = 1).
diff --git a/doc/tech-report/derivation-checks/check_ch10_interp.out b/doc/tech-report/derivation-checks/check_ch10_interp.out
index 45878d2..4eb5781 100644
--- a/doc/tech-report/derivation-checks/check_ch10_interp.out
+++ b/doc/tech-report/derivation-checks/check_ch10_interp.out
@@ -1,4 +1,4 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 (a) bilinear table, increasing x and decreasing y grids, 200 interior queries: max error 1.8e-15, 3.6e-15 (tol 1e-12) PASS
 (b) all 20 grid nodes, including the last node of each axis: max error 0.0e+00 (tol 1e-13) PASS
 (c) outside the grid: extrapolate=False gives the clamped-coordinate value (err 0.0e+00); extrapolate=True continues the end cells linearly, exact for a bilinear table (err 8.9e-15) (tol 1e-12) PASS
diff --git a/doc/tech-report/derivation-checks/check_ch14_coupling.out b/doc/tech-report/derivation-checks/check_ch14_coupling.out
index 318938e..ca3fdf2 100644
--- a/doc/tech-report/derivation-checks/check_ch14_coupling.out
+++ b/doc/tech-report/derivation-checks/check_ch14_coupling.out
@@ -1,12 +1,11 @@
-[Warning] equilibrate_uv did not converge after 10 iterations.
-[Warning] equilibrate_uv did not converge after 10 iterations.
 [Warning] equilibrate_uv did not converge after 1 iterations.
 [Warning] equilibrate_uv did not converge after 1 iterations.
 [Warning] equilibrate_uv did not converge after 1 iterations.
 [Warning] equilibrate_uv did not converge after 1 iterations.
 [Warning] equilibrate_uv did not converge after 1 iterations.
 [Warning] equilibrate_uv did not converge after 1 iterations.
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+[W1023 20:39:41.403769455 thermo_y.cpp:387] Warning: ThermoYImpl::forward: saturation adjustment failed in 6 cell(s); diag = -(100 * status + iterations) (function forward)
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 build: Linux x86_64, Python 3.11.13, torch 2.10.0+cu128
 (a) DY->V (snapy moist_mixture.cpp:149) against rho*(1-sum y), rho*y: max rel err 1.97e-16 (tol 1e-14) PASS
 (b) V->Y after DY->V returns the mass fractions: max rel err 3.62e-16 (tol 1e-14) PASS
@@ -18,17 +17,17 @@ build: Linux x86_64, Python 3.11.13, torch 2.10.0+cu128
 (h) IdealMoist W->I formula against kintera VT->U at the same state: max rel err 4.95e-16 (tol 1e-12) PASS
 (i) IdealMoist W->T = p/(rho Rd f_eps) against the state temperature: max rel err 3.33e-16 (tol 1e-13) PASS
 (j) the options object snapy reads after ThermoYImpl::create holds the T=0 offsets (uref - cref Tref): True PASS
-(k0) diag per cell at the default max_iter 10 (negative = failed, D4 filed): -2010 -2010 8 7 6 4 INFO
+(k0) diag per cell at the default max_iter 100 (negative = failed, D4 filed): 11 9 9 7 5 4 INFO
 (k) adjustment moved mass fractions by up to 1.00e+00 of the largest (state was supersaturated) PASS
 (l) total density rho_dry + sum y' rho equals rho (dry row untouched): max rel err 2.22e-16 (tol 1e-14) PASS
 (m) element moles H, He, N, O, S per cell conserved: max rel err 3.69e-16 (tol 1e-13) PASS
-(n) snapy's next VU->T at fixed ie (meshblock.cpp:825) = linear-model T: max rel err 4.44e-16 (tol 1e-12) PASS
-(o) latent warming T' - T per cell [K]: 22.352 21.810 20.554 13.713 9.087 3.756 INFO
-(p) max relative humidity per cell at (T', p') after the adjustment: 1.000000 1.000001 1.000000 1.000000 1.000000 1.000000 INFO
+(n) snapy's next VU->T at fixed ie (meshblock.cpp:825) = linear-model T: max rel err 2.22e-16 (tol 1e-12) PASS
+(o) latent warming T' - T per cell [K]: 28.163 27.660 26.127 18.686 11.822 4.714 INFO
+(p) max relative humidity per cell at (T', p') after the adjustment: 1.000000 1.000000 1.000000 1.000000 1.000000 1.000000 INFO
 (q) max_iter = 1: 6 failed cell(s) counted, count reset to 0 on the second read PASS
 (r) failed cells: written state still conserves total density: max rel err 2.22e-16 (tol 1e-14) PASS
 (s) gas concentrations from Y->X then TPX->V equal rho_i/mu_i [mol/m^3]: max rel err 4.44e-16 (tol 1e-12) PASS
-(t) cloud concentrations from TPX->V against rho_i/mu_i: max rel diff 4.44e-16 (filed as D16; the driver's tendencies start from these) INFO
+(t) cloud concentrations from TPX->V against rho_i/mu_i: max rel diff 6.66e-16 (filed as D16; the driver's tendencies start from these) INFO
 (u) sum_i M_i delta_i = 0 for a stoichiometric change (mass hand-back): max rel err 2.13e-16 (tol 1e-14) PASS
-(v) ratio of the volumetric heat capacity the drivers pass (TV->cp) to the C_V of the fixed-U Jacobian: 1.3845 1.3845 1.3846 1.3869 1.3908 1.3961 EXPECTED-FAIL (S14-1)
+(v) ratio of the volumetric heat capacity the drivers pass (TV->cp) to the C_V of the fixed-U Jacobian: 1.3853 1.3853 1.3854 1.3880 1.3921 1.3968 EXPECTED-FAIL (S14-1)
 (w) split-step local error / dt^2 against [B,A]/2: rel diff 6.32e-03 at dt=1e-2, 6.30e-04 at dt=1e-3 (first order in dt; tol 2e-2 at 1e-2) PASS
diff --git a/doc/tech-report/derivation-checks/check_ch3_adiabat.out b/doc/tech-report/derivation-checks/check_ch3_adiabat.out
index d6e5733..ca98a8c 100644
--- a/doc/tech-report/derivation-checks/check_ch3_adiabat.out
+++ b/doc/tech-report/derivation-checks/check_ch3_adiabat.out
@@ -1,13 +1,13 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
    ftol=1e-06: T1 = 260.063369404122 K, analytic 260.063369925054 K (cp/R = 3.5), p1 = 60653.065971 Pa
 4a dry adiabat T1 vs 300 exp(-0.5 R/cp), ftol=1e-06 (rel): measured 2.003e-09  tol 1e-08  PASS
    ftol=1e-12: T1 = 260.063369925054 K, analytic 260.063369925054 K (cp/R = 3.5), p1 = 60653.065971 Pa
 4a dry adiabat T1 vs 300 exp(-0.5 R/cp), ftol=1e-12 (rel): measured 0.000e+00  tol 1e-08  PASS
    state T=280 K, p=1e6 Pa, condensate mole fractions {'H2O(l)': 0.001509365302325915, 'NH3(s)': 0.0, 'NH4SH(s)': 0.0}
-   effective_cp = 31.3464857806, FD d(H/n)/dT = 31.3464858864, frozen cp = 29.169633 J/(mol K)
-4b effective_cp vs central FD of equilibrium molar enthalpy (rel): measured 3.375e-09  tol 1e-05  PASS
-   saturated step dlnp=-0.01: T 280.0 -> 279.24698789 K, s -21.1429530619 -> -21.1429525986 J/(mol K)
-4b |ds| over saturated extrapolate_dlnp step (J/(mol K)): measured 4.634e-07  tol 1e-05  PASS
-   S(600 K) = 404.3358553266 J/(K m^3); PXS->T returns 594.1625594241 K (start guess Tref = 300.0 K, max_iter = 10)
-4c PXS->T round trip |T - 600| (K): measured 5.837e+00  tol 1e-06  EXPECTED-FAIL (D8)
-SUMMARY: 4 PASS, 0 FAIL, 1 EXPECTED-FAIL
+   effective_cp = 32.2190406313, FD d(H/n)/dT = 32.2190407845, frozen cp = 29.163182 J/(mol K)
+4b effective_cp vs central FD of equilibrium molar enthalpy (rel): measured 4.756e-09  tol 1e-05  PASS
+   saturated step dlnp=-0.01: T 280.0 -> 279.26480447 K, s -21.2124497180 -> -21.2124497181 J/(mol K)
+4b |ds| over saturated extrapolate_dlnp step (J/(mol K)): measured 1.762e-10  tol 1e-05  PASS
+   S(600 K) = 404.3358553266 J/(K m^3); PXS->T returns 600.0000000000 K (start guess Tref = 300.0 K, max_iter = 100)
+4c PXS->T round trip |T - 600| (K): measured 2.728e-12  tol 1e-06  PASS
+SUMMARY: 5 PASS, 0 FAIL, 0 EXPECTED-FAIL
diff --git a/doc/tech-report/derivation-checks/check_ch3_adiabat_slope.out b/doc/tech-report/derivation-checks/check_ch3_adiabat_slope.out
index dba51d7..89969d5 100644
--- a/doc/tech-report/derivation-checks/check_ch3_adiabat_slope.out
+++ b/doc/tech-report/derivation-checks/check_ch3_adiabat_slope.out
@@ -1,8 +1,8 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
-   tests/jupiter.yaml, 280 K, 1e6 Pa, per mole of dry gas: dH/dT = 31.4370245170, T dS/dT = 31.3673271336 J/(mol K); per mole of mixture dh/dT = 31.3464858864
-(h1) closed parcel at fixed p, tests/jupiter.yaml: T dS/dT vs dH/dT (rel): measured 2.217e-03  tol 1e-05  EXPECTED-FAIL (K8)
-   effective_cp = 31.3464857806 J/(mol K)
-(h2) per mole: dh/dT along the equilibrium path vs effective_cp (rel): measured 3.375e-09  tol 1e-05  PASS
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
+   tests/jupiter.yaml, 280 K, 1e6 Pa, per mole of dry gas: dH/dT = 32.3120996315, T dS/dT = 32.3120996239 J/(mol K); per mole of mixture dh/dT = 32.2190407845
+(h1) closed parcel at fixed p, tests/jupiter.yaml: T dS/dT vs dH/dT (rel): measured 2.342e-10  tol 1e-05  PASS
+   effective_cp = 32.2190406313 J/(mol K)
+(h2) per mole: dh/dT along the equilibrium path vs effective_cp (rel): measured 4.756e-09  tol 1e-05  PASS
    corrected cards, 280 K, 1e6 Pa, per mole of dry gas: dH/dT = 32.3120996315, T dS/dT = 32.3120996239 J/(mol K); per mole of mixture dh/dT = 32.2190407845
 (h1) closed parcel at fixed p, corrected cards: T dS/dT vs dH/dT (rel): measured 2.342e-10  tol 1e-05  PASS
    T=170 K: x_NH4SH = 5.025e-03, effective_cp = 29.36303921, (1/n) dH/dT = 29.36303922, d(H/n)/dT = 29.36316862 J/(mol K)
@@ -12,6 +12,6 @@ kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
    T=240 K: x_NH4SH = 9.002e-04, effective_cp = 70.42215881, (1/n) dH/dT = 70.42216359, d(H/n)/dT = 70.16783442 J/(mol K)
    |effective_cp / d(H/n)/dT - 1| up to 3.625e-03 (n changes)
 (h4) effective_cp vs (1/n) dH/dT where NH4SH forms, worst rel: measured 6.787e-08  tol 1e-06  PASS
-   rain-out, d ln p = -0.2 from 300 K, 1e6 Pa: |T_N - T_512| = 7.5237e-02, 3.7305e-02, 1.8352e-02, 8.8786e-03 K for N = 4, 8, 16, 32; observed orders 1.012, 1.023, 1.048
-(h3) rain-out step is first order in d ln p: max |observed order - 1|: measured 4.751e-02  tol 0.15  PASS
-SUMMARY: 4 PASS, 0 FAIL, 1 EXPECTED-FAIL
+   rain-out, d ln p = -0.2 from 300 K, 1e6 Pa: |T_N - T_512| = 1.4982e-01, 7.4017e-02, 3.6346e-02, 1.7568e-02 K for N = 4, 8, 16, 32; observed orders 1.017, 1.026, 1.049
+(h3) rain-out step is first order in d ln p: max |observed order - 1|: measured 4.880e-02  tol 0.15  PASS
+SUMMARY: 5 PASS, 0 FAIL, 0 EXPECTED-FAIL
diff --git a/doc/tech-report/derivation-checks/check_ch3_condensate_entropy.out b/doc/tech-report/derivation-checks/check_ch3_condensate_entropy.out
index d8bbb13..87b9060 100644
--- a/doc/tech-report/derivation-checks/check_ch3_condensate_entropy.out
+++ b/doc/tech-report/derivation-checks/check_ch3_condensate_entropy.out
@@ -1,18 +1,18 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
-   H2O(l)    T= 250.0 K, p=7.620637e+01 Pa: sum nu (h - T s)/(R T) = -2.069e-10
-   H2O(l)    T= 280.0 K, p=9.921322e+02 Pa: sum nu (h - T s)/(R T) = -5.934e-10
-   H2O(l)    T= 300.0 K, p=3.539458e+03 Pa: sum nu (h - T s)/(R T) = -5.385e-10
-   NH3(s)    T= 150.0 K, p=1.712495e+01 Pa: sum nu (h - T s)/(R T) = -2.260e-09
-   NH3(s)    T= 180.0 K, p=1.165598e+03 Pa: sum nu (h - T s)/(R T) = +1.297e-09
-   NH3(s)    T= 220.0 K, p=2.938858e+04 Pa: sum nu (h - T s)/(R T) = +3.730e-10
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
+   H2O(l)    T= 250.0 K, p=7.620637e+01 Pa: sum nu (h - T s)/(R T) = +8.840e-10
+   H2O(l)    T= 280.0 K, p=9.921322e+02 Pa: sum nu (h - T s)/(R T) = -8.421e-10
+   H2O(l)    T= 300.0 K, p=3.539458e+03 Pa: sum nu (h - T s)/(R T) = +4.789e-10
+   NH3(s)    T= 150.0 K, p=1.712495e+01 Pa: sum nu (h - T s)/(R T) = +5.250e-10
+   NH3(s)    T= 180.0 K, p=1.165598e+03 Pa: sum nu (h - T s)/(R T) = -2.820e-13
+   NH3(s)    T= 220.0 K, p=2.938858e+04 Pa: sum nu (h - T s)/(R T) = -2.700e-11
    NH4SH(s)  T= 200.0 K, p=9.000085e+00 Pa: sum nu (h - T s)/(R T) = +3.350e-08
    NH4SH(s)  T= 240.0 K, p=8.216054e+02 Pa: sum nu (h - T s)/(R T) = -3.802e-09
 (e1) nucleation reactions at saturation: |sum_n nu_n (h_n - T s_n)|/(R T), worst: measured 3.350e-08  tol 1e-06  PASS
-   H2O(l,p): s/R = 0.000000, source H2O(l): s/R = -9.342692 (T=280.0 K, p=5.0e+05 Pa)
-   NH3(s,p): s/R = 0.000000, source NH3(s): s/R = -40.716115 (T=140.0 K, p=5.0e+04 Pa)
-(e2) coagulation copy entropy equals its source's, worst rel: measured 1.000e+00  tol 1e-09  EXPECTED-FAIL (D64)
+   H2O(l,p): s/R = -14.880469, source H2O(l): s/R = -14.880469 (T=280.0 K, p=5.0e+05 Pa)
+   NH3(s,p): s/R = -19.550801, source NH3(s): s/R = -19.550801 (T=140.0 K, p=5.0e+04 Pa)
+(e2) coagulation copy entropy equals its source's, worst rel: measured 3.497e-10  tol 1e-09  PASS
    H2O gas (constant cp): cp = [33.25784, 33.25784, 33.25784, 33.25784, 33.25784], T ds/dT = [33.25784, 33.25784, 33.25784, 33.25784, 33.25784] J/(mol K) at 250-900 K
 (e3) T (ds/dT)_p = cp for H2O gas, flag off, worst rel: measured 4.899e-11  tol 1e-06  PASS
-   H2O gas, use-nasa9-cp: true: cp = [33.435519, 33.595723, 34.265063, 36.323676, 39.997566], T ds/dT = [33.25784, 33.25784, 33.25784, 33.25784, 33.25784] J/(mol K) at 250-900 K
-(e3) T (ds/dT)_p = cp for H2O gas, use-nasa9-cp on, worst rel: measured 1.685e-01  tol 1e-06  EXPECTED-FAIL (K6)
-SUMMARY: 2 PASS, 0 FAIL, 2 EXPECTED-FAIL
+   H2O gas, use-nasa9-cp: true: cp = [33.435519, 33.595723, 34.265063, 36.323676, 39.997566], T ds/dT = [33.435519, 33.595723, 34.265063, 36.323676, 39.997566] J/(mol K) at 250-900 K
+(e3) T (ds/dT)_p = cp for H2O gas, use-nasa9-cp on, worst rel: measured 4.991e-11  tol 1e-06  PASS
+SUMMARY: 4 PASS, 0 FAIL, 0 EXPECTED-FAIL
diff --git a/doc/tech-report/derivation-checks/check_ch3_eos.out b/doc/tech-report/derivation-checks/check_ch3_eos.out
index 9c3dd4c..d1982e6 100644
--- a/doc/tech-report/derivation-checks/check_ch3_eos.out
+++ b/doc/tech-report/derivation-checks/check_ch3_eos.out
@@ -1,9 +1,9 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
    x = [1.0, 0.0, 0.0]: c = ['4.0090797638e+01', '1.0000000000e-20', '0.0000000000e+00'] mol/m^3
    x = [0.5, 0.4, 0.1]: c = ['2.2272665355e+01', '1.7818132284e+01', '4.4545330709e+00'] mol/m^3
 (c1) sum_gas c R T = p, gas-only and cloudy states with x_0 > 0 (rel): measured 0.000e+00  tol 1e-13  PASS
 (c1) c_m = x_m p / (R T x_g), cloudy state with x_0 = 0.5 (rel): measured 0.000e+00  tol 1e-13  PASS
-   x = [0.0, 0.9, 0.1]: c = [1e-20, 40.09079763849165, inf] mol/m^3 (x_0 = 0)
+   x = [0.0, 0.9, 0.1]: c = [1e-20, 40.09079763849165, 4.4545330709435165] mol/m^3 (x_0 = 0)
 (c2) x_0 = 0: sum_gas c R T = p (rel): measured 0.000e+00  tol 1e-13  PASS
-(c2) x_0 = 0: c_m = x_m p / (R T x_g) (rel; non-finite at the pin): measured inf  tol 1e-13  EXPECTED-FAIL (D16)
-SUMMARY: 3 PASS, 0 FAIL, 1 EXPECTED-FAIL
+(c2) x_0 = 0: c_m = x_m p / (R T x_g) (rel; non-finite at the pin): measured 0.000e+00  tol 1e-13  PASS
+SUMMARY: 4 PASS, 0 FAIL, 0 EXPECTED-FAIL
diff --git a/doc/tech-report/derivation-checks/check_ch3_pxs.out b/doc/tech-report/derivation-checks/check_ch3_pxs.out
index eef2b4a..12fc540 100644
--- a/doc/tech-report/derivation-checks/check_ch3_pxs.out
+++ b/doc/tech-report/derivation-checks/check_ch3_pxs.out
@@ -1,11 +1,11 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 (f1) dS/dT|_(p,x) vs (C_p - S)/T, dry state, 250-600 K (rel): measured 3.097e-10  tol 1e-07  PASS
    at 600 K: S = 404.335855, C_p = 583.333333 J/(K m^3); pin map derivative 0.6931471806, S/C_p = 0.6931471806
 (f2) derivative of the pin's fixed-point map at the root vs S/C_p (abs): measured 8.112e-11  tol 1e-07  PASS
    correct Newton from Tref: 403.972077084, 501.235209722, 568.954669227, 596.240464978, 599.938986432, 599.999983690 K ...
-(f3) correct Newton step, 10 iterations from Tref, |T - 600| (K): measured 0.000e+00  tol 1e-09  PASS
-   kintera PXS->T: 594.1625594241 K
-(f4) kintera PXS->T from the same S, |T - 600| (K): measured 5.837e+00  tol 1e-06  EXPECTED-FAIL (D8)
+(f3) correct Newton step, 100 iterations from Tref, |T - 600| (K): measured 0.000e+00  tol 1e-09  PASS
+   kintera PXS->T: 600.0000000000 K
+(f4) kintera PXS->T from the same S, |T - 600| (K): measured 2.728e-12  tol 1e-06  PASS
    saturated state 299 K, 1e6 Pa, x_H2O 0.02: x_g = 0.983281, S = -8479.79, C_p = 12188.27, C_eff = 15700.77 J/(K m^3)
    T dS/dT: central difference 24683.374353, (C_eff - S) - S T dln n_g/dT = 24683.374354, C_eff - S = 24180.56
 (f5) saturated T dS/dT vs (C_eff - S) - S T d ln n_g/dT (rel): measured 2.732e-11  tol 1e-06  PASS
@@ -13,8 +13,8 @@ kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
 (f6) frozen-slope step: root factor 1 - T (dS/dT)/(C_p - S) vs iteration (abs): measured 1.658e-06  tol 1e-03  PASS
    pin step: predicted 1 - T (dS/dT)/C_p = -1.025175 (S/C_p = -0.695734), error ratios -1.025161, -1.025190
 (f7) pin step: root factor 1 - T (dS/dT)/C_p vs iteration (abs): measured 1.429e-05  tol 1e-03  PASS
-   kintera PXS->T from Tref, max_iter 1..8: T - T* = -28.1, +13.8, -23.0, +20.1, -30.0, +21.3, -29.4, +21.1 K
-(f8) kintera PXS->T in the saturated parcel after 8 passes, |T - T*| (K): measured 2.114e+01  tol 1e-06  EXPECTED-FAIL (D8)
+   kintera PXS->T from Tref, max_iter 1..8: T - T* = -16.3, -8.0, +1.2, +0.0, -0.0, +0.0, +0.0, +0.0 K
+(f8) kintera PXS->T in the saturated parcel after 8 passes, |T - T*| (K): measured 5.684e-14  tol 1e-06  PASS
    dry gas, s0_R 0: first step 403.972 K, S(300) = 0.0, C_p - S = 1166.7; s0_R 10: first step 474.784 K, S(300) = 3333.3, C_p - S = -2166.7 J/(K m^3)
 (f9) the root does not depend on s0_R: both runs end at 600 K, max |T - 600| (K): measured 1.137e-13  tol 1e-09  PASS
 (f9) the iterates do: first steps differ (K), must EXCEED tol: measured 7.081e+01  tol 1e+00  PASS
@@ -28,10 +28,10 @@ kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
    default constants, 1e+02 Pa, 205 K: x_g = 0.983356, C_p - S = -0.814 J/(K m^3), ratio -0.388684, phi' = +1.388684, error ratios +1.388695, +1.388700
 (f11) default constants, 1e6-1e2 Pa: phi' vs iteration (rel): measured 2.369e-03  tol 1e-02  PASS
 (f11) converges iff 0 < ratio < 2, alternates iff ratio > 1: rows against it (count): measured 0.000e+00  tol 0e+00  PASS
-   1e+03 Pa, T* = 225 K: roots of S_vol(T) = S_vol(T*): 225.00, 347.12 K; local maximum of S_vol at 237.11 K; PXS->T from Tref = 225.00 K (relative entropy residual -1.2e-16)
+   1e+03 Pa, T* = 225 K: roots of S_vol(T) = S_vol(T*): 225.00, 347.12 K; local maximum of S_vol at 237.11 K; PXS->T from Tref = 347.12 K (relative entropy residual 5.9e-16)
    INFO 1e+03 Pa: condensate fraction 1.1e-04 at 237.06 K and 0.0e+00 at 237.16 K
-   1e+02 Pa, T* = 205 K: roots of S_vol(T) = S_vol(T*): 199.18, 205.00, 240.48 K; local maximum of S_vol at 217.80 K; PXS->T from Tref = nan K (relative entropy residual nan)
+   1e+02 Pa, T* = 205 K: roots of S_vol(T) = S_vol(T*): 199.18, 205.00, 240.48 K; local maximum of S_vol at 217.80 K; PXS->T from Tref = 240.48 K (relative entropy residual 1.7e-16)
    INFO 1e+02 Pa: condensate fraction 1.3e-04 at 217.75 K and 0.0e+00 at 217.85 K; local minimum of S_vol at 202.26 K
 (f12) S_vol(T) = S_vol(T*) has 2 roots at 1e3 Pa and 3 at 1e2 Pa, one above the local maximum (count): measured 0.000e+00  tol 0e+00  PASS
-(f12) kintera PXS->T from Tref returns T*, max |T - T*| over both states (K): measured nan  tol 1e-06  EXPECTED-FAIL (K16)
-SUMMARY: 13 PASS, 0 FAIL, 3 EXPECTED-FAIL
+(f12) kintera PXS->T from Tref returns T*, max |T - T*| over both states (K): measured 1.221e+02  tol 1e-06  EXPECTED-FAIL (K16)
+SUMMARY: 15 PASS, 0 FAIL, 1 EXPECTED-FAIL
diff --git a/doc/tech-report/derivation-checks/check_ch3_reference.out b/doc/tech-report/derivation-checks/check_ch3_reference.out
index c45f6ac..810b54a 100644
--- a/doc/tech-report/derivation-checks/check_ch3_reference.out
+++ b/doc/tech-report/derivation-checks/check_ch3_reference.out
@@ -1,23 +1,23 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 (a1) h/R = (u0 - cv Tref) + cv T (+ T for a gas), H2O, H2O(l), NH3(s) at 200-400 K (rel): measured 0.000e+00  tol 1e-13  PASS
 (a2) pure H2O gas s/R = (cv+1) ln(T/Tref) - ln(p/Pref) (abs): measured 1.776e-15  tol 1e-12  PASS
-   T=250.0 K: l = h_v - h_c = 33299.412300 J/mol, L = u_v - u_c = 31220.797300 J/mol, l - L = 2078.615000 (R T = 2078.615000)
-   T=300.0 K: l = h_v - h_c = 31012.935800 J/mol, L = u_v - u_c = 28518.597800 J/mol, l - L = 2494.338000 (R T = 2494.338000)
-   T=350.0 K: l = h_v - h_c = 28726.459300 J/mol, L = u_v - u_c = 25816.398300 J/mol, l - L = 2910.061000 (R T = 2910.061000)
-(a3) l - L = R T for H2O -> H2O(l) (rel to l): measured 4.749e-17  tol 1e-12  PASS
+   T=250.0 K: l = h_v - h_c = 46063.421669 J/mol, L = u_v - u_c = 43984.806669 J/mol, l - L = 2078.615000 (R T = 2078.615000)
+   T=300.0 K: l = h_v - h_c = 43990.623049 J/mol, L = u_v - u_c = 41496.285049 J/mol, l - L = 2494.338000 (R T = 2494.338000)
+   T=350.0 K: l = h_v - h_c = 41917.824430 J/mol, L = u_v - u_c = 39007.763430 J/mol, l - L = 2910.061000 (R T = 2910.061000)
+(a3) l - L = R T for H2O -> H2O(l) (rel to l): measured 1.410e-16  tol 1e-12  PASS
    use-nasa9-cp, Tref = 300.0 K: u(300 K)/R = 1000.000000 (u* + c* (300 - Tref) = 1000.000000), u(Tref)/R = 1000.000000
    use-nasa9-cp, Tref = 250.0 K: u(300 K)/R = 1150.000000 (u* + c* (300 - Tref) = 1150.000000), u(Tref)/R = 998.513027
 (a4) u(300 K)/R = u* + c* (300 K - Tref) under use-nasa9-cp, Tref 300 and 250 K (abs): measured 0.000e+00  tol 1e-09  PASS
-   tests/jupiter.yaml: H2O(l) l_card/l_svp = 0.712354, 0.708706, 0.704990, 0.701202, 0.697342
-   tests/jupiter.yaml: NH3(s) l_card/l_svp = 1.763756, 1.754351, 1.744875, 1.735328, 1.725707
-(g1) tests/jupiter.yaml: |l_card/l_svp - 1| on the forming branch, worst: measured 7.638e-01  tol 1e-06  EXPECTED-FAIL (K8)
-   tests/jupiter.yaml: H2O(l) T ds_c/dT / c_p,c = 0.384691, 0.403940, 0.421905, 0.438711, 0.454466
-   tests/jupiter.yaml: NH3(s) T ds_c/dT / c_p,c = 3.025308, 2.868323, 2.729806, 2.606681, 2.496515
-(g3) tests/jupiter.yaml: solved condensate entropy has T ds_c/dT = c_p,c, worst rel: measured 2.025e+00  tol 1e-06  EXPECTED-FAIL (K8)
+   tests/jupiter.yaml: H2O(l) l_card/l_svp = 1.000000, 1.000000, 1.000000, 1.000000, 1.000000
+   tests/jupiter.yaml: NH3(s) l_card/l_svp = 1.000000, 1.000000, 1.000000, 1.000000, 1.000000
+(g1) tests/jupiter.yaml: |l_card/l_svp - 1| on the forming branch, worst: measured 5.237e-11  tol 1e-06  PASS
+   tests/jupiter.yaml: H2O(l) T ds_c/dT / c_p,c = 1.000000, 1.000000, 1.000000, 1.000000, 1.000000
+   tests/jupiter.yaml: NH3(s) T ds_c/dT / c_p,c = 1.000000, 1.000000, 1.000000, 1.000000, 1.000000
+(g3) tests/jupiter.yaml: solved condensate entropy has T ds_c/dT = c_p,c, worst rel: measured 2.196e-09  tol 1e-06  PASS
    corrected cards: H2O(l) l_card/l_svp = 1.000000, 1.000000, 1.000000, 1.000000, 1.000000
    corrected cards: NH3(s) l_card/l_svp = 1.000000, 1.000000, 1.000000, 1.000000, 1.000000
 (g2) corrected cards: |l_card/l_svp - 1| on the forming branch, worst: measured 5.237e-11  tol 1e-06  PASS
    corrected cards: H2O(l) T ds_c/dT / c_p,c = 1.000000, 1.000000, 1.000000, 1.000000, 1.000000
    corrected cards: NH3(s) T ds_c/dT / c_p,c = 1.000000, 1.000000, 1.000000, 1.000000, 1.000000
 (g3) corrected cards: solved condensate entropy has T ds_c/dT = c_p,c, worst rel: measured 2.196e-09  tol 1e-06  PASS
-SUMMARY: 6 PASS, 0 FAIL, 2 EXPECTED-FAIL
+SUMMARY: 8 PASS, 0 FAIL, 0 EXPECTED-FAIL
diff --git a/doc/tech-report/derivation-checks/check_ch3_thermo_y.out b/doc/tech-report/derivation-checks/check_ch3_thermo_y.out
index 3f4f563..4609ec2 100644
--- a/doc/tech-report/derivation-checks/check_ch3_thermo_y.out
+++ b/doc/tech-report/derivation-checks/check_ch3_thermo_y.out
@@ -1,12 +1,12 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 (d1) Y->X vs the mole-fraction formula with the dry species implicit (rel): measured 2.179e-19  tol 1e-14  PASS
 (d2) VT->U then VU->T, constant cv, |T - T0| (K): measured 0.000e+00  tol 1e-10  PASS
-   use-h2-cp off: after ThermoY.forward T = 304.958496 K, cloud = 1.462651e-01 mol/m^3, ln p_v - ln K(T) = +9.178e-07
-(d4) UV saturation adjustment lands on the curve, use-h2-cp off: |ln p_v - ln K(T)|: measured 9.178e-07  tol 1e-05  PASS
-(d3) VT->U then VU->T, use-h2-cp normal, |T - T0| (K): measured 3.666e-12  tol 1e-10  PASS
-   use-h2-cp normal: after ThermoY.forward T = 305.044993 K, cloud = 1.462651e-01 mol/m^3, ln p_v - ln K(T) = -4.612e-03
-(d4) UV saturation adjustment lands on the curve, use-h2-cp normal: |ln p_v - ln K(T)|: measured 4.612e-03  tol 1e-05  EXPECTED-FAIL (D12)
+   use-h2-cp off: after ThermoY.forward T = 304.958509 K, cloud = 1.462655e-01 mol/m^3, ln p_v - ln K(T) = -5.329e-15
+(d4) UV saturation adjustment lands on the curve, use-h2-cp off: |ln p_v - ln K(T)|: measured 5.329e-15  tol 1e-05  PASS
+(d3) VT->U then VU->T, use-h2-cp normal, |T - T0| (K): measured 3.638e-12  tol 1e-10  PASS
+   use-h2-cp normal: after ThermoY.forward T = 304.978232 K, cloud = 1.443095e-01 mol/m^3, ln p_v - ln K(T) = -3.553e-15
+(d4) UV saturation adjustment lands on the curve, use-h2-cp normal: |ln p_v - ln K(T)|: measured 3.553e-15  tol 1e-05  PASS
 (d3) VT->U then VU->T, use-h2-cp equilibrium, |T - T0| (K): measured 5.684e-14  tol 1e-10  PASS
-   use-h2-cp equilibrium: after ThermoY.forward T = 305.044345 K, cloud = 1.462651e-01 mol/m^3, ln p_v - ln K(T) = -4.577e-03
-(d4) UV saturation adjustment lands on the curve, use-h2-cp equilibrium: |ln p_v - ln K(T)|: measured 4.577e-03  tol 1e-05  EXPECTED-FAIL (D12)
-SUMMARY: 5 PASS, 0 FAIL, 2 EXPECTED-FAIL
+   use-h2-cp equilibrium: after ThermoY.forward T = 304.978086 K, cloud = 1.443240e-01 mol/m^3, ln p_v - ln K(T) = -3.553e-15
+(d4) UV saturation adjustment lands on the curve, use-h2-cp equilibrium: |ln p_v - ln K(T)|: measured 3.553e-15  tol 1e-05  PASS
+SUMMARY: 7 PASS, 0 FAIL, 0 EXPECTED-FAIL
diff --git a/doc/tech-report/derivation-checks/check_ch4_tp.out b/doc/tech-report/derivation-checks/check_ch4_tp.out
index e0e1357..492cf0f 100644
--- a/doc/tech-report/derivation-checks/check_ch4_tp.out
+++ b/doc/tech-report/derivation-checks/check_ch4_tp.out
@@ -1,4 +1,4 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 == a. complementarity (|res|<=1e-6 if condensate present, res<0 if absent); elements 1e-14
 == b. TP gain[H2O,H2O] vs central FD of ln(x_H2O/x_g) along H2O->H2O(l), tol 1e-7 rel
 T=300 K  diag=1
@@ -15,7 +15,7 @@ T=250 K  diag=9
   a element O/dry rel change=0.0e+00  tol 1e-14 PASS
   a element N/dry rel change=2.2e-16  tol 1e-14 PASS
   a element S/dry rel change=2.2e-16  tol 1e-14 PASS
-  b gain=-1.3369663184e+03 FD=-1.3369663186e+03 rel=1.1e-10 tol 1e-7 PASS; without -sum(nu)/x_g: -1.337986e+03 (rel 7.6e-04)
+  b gain=-1.3369663184e+03 FD=-1.3369663180e+03 rel=3.3e-10 tol 1e-7 PASS; without -sum(nu)/x_g: -1.337986e+03 (rel 7.6e-04)
 T=200 K  diag=18
   a H2O->H2O(l)        cloud=2.010e-02 res=-1.119e-09  tol |res|<=1e-6  PASS
   a NH3->NH3(s)        cloud=0.000e+00 res=-7.536e+00  tol res<0        PASS
@@ -24,26 +24,14 @@ T=200 K  diag=18
   a element N/dry rel change=3.3e-16  tol 1e-14 PASS
   a element S/dry rel change=3.3e-16  tol 1e-14 PASS
   b gain=-6.3797848693e+05 FD=-6.3797848656e+05 rel=5.8e-10 tol 1e-7 PASS; without -sum(nu)/x_g: -6.379795e+05 (rel 1.6e-06)
-T=160 K  diag=29
-  a H2O->H2O(l)        cloud=2.010e-02 res=-6.953e-08  tol |res|<=1e-6  PASS
+T=160 K  diag=32
+  a H2O->H2O(l)        cloud=2.010e-02 res=-4.108e-11  tol |res|<=1e-6  PASS
   a NH3->NH3(s)        cloud=0.000e+00 res=-9.696e+00  tol res<0        PASS
-  a NH3+H2S->NH4SH(s)  cloud=5.025e-03 res=-3.914e-11  tol |res|<=1e-6  PASS
-  a element O/dry rel change=2.2e-16  tol 1e-14 PASS
-  a element N/dry rel change=3.3e-16  tol 1e-14 PASS
+  a NH3+H2S->NH4SH(s)  cloud=5.025e-03 res=-1.331e-07  tol |res|<=1e-6  PASS
+  a element O/dry rel change=3.3e-16  tol 1e-14 PASS
+  a element N/dry rel change=0.0e+00  tol 1e-14 PASS
   a element S/dry rel change=3.3e-16  tol 1e-14 PASS
-  b gain=-1.4525632007e+09 FD=-1.4525632006e+09 rel=4.2e-11 tol 1e-7 PASS; without -sum(nu)/x_g: -1.452563e+09 (rel 7.5e-10)
-== c. default max-iter on cold-start cells 130..250 K (known defect D4)
-  max-iter=10 (default): non-converged 12/13; diag=[-2010, -2010, -2010, -2010, -2010, -2010, -2010, -2010, -2010, -2010, -2010, -2010, 9]  tol 0  EXPECTED-FAIL
-  max-iter=100: non-converged 0/13; iterations=[46, 41, 37, 29, 29, 23, 21, 18, 16, 14, 12, 11, 9]  tol 0  PASS
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
-equilibrate_tp did not converge after 10 iterations.
+  b gain=-1.4525630998e+09 FD=-1.4525630997e+09 rel=4.2e-11 tol 1e-7 PASS; without -sum(nu)/x_g: -1.452563e+09 (rel 7.5e-10)
+== c. default max-iter on cold-start cells 130..250 K (D4 regression)
+  max-iter=100 (default): non-converged 0/13; diag=[46, 41, 33, 32, 26, 23, 21, 18, 16, 14, 12, 11, 9]  tol 0  PASS
+  max-iter=100: non-converged 0/13; iterations=[46, 41, 33, 32, 26, 23, 21, 18, 16, 14, 12, 11, 9]  tol 0  PASS
diff --git a/doc/tech-report/derivation-checks/check_ch4_uv.out b/doc/tech-report/derivation-checks/check_ch4_uv.out
index 5cf01b7..d10dbfb 100644
--- a/doc/tech-report/derivation-checks/check_ch4_uv.out
+++ b/doc/tech-report/derivation-checks/check_ch4_uv.out
@@ -1,10 +1,7 @@
-[Warning] equilibrate_uv partition did not converge.
-[Warning] equilibrate_uv partition did not converge.
-[Warning] equilibrate_uv partition did not converge.
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 == a. uv-solver kkt: |T - T_oracle| <= 1e-06 K, U rel 1e-10, water rel 1e-14
   T0=280 yv=0.02: diag=6 T=281.9157078006 oracle=281.9157077988 dT=1.8e-09 PASS; dU=3.3e-16 PASS; dWater=0.0e+00 PASS
-  T0=250 yv=0.01: diag=7 T=251.6354488725 oracle=251.6354488589 dT=1.4e-08 PASS; dU=2.2e-16 PASS; dWater=0.0e+00 PASS
+  T0=250 yv=0.01: diag=7 T=251.6354488589 oracle=251.6354488589 dT=4.0e-12 PASS; dU=1.1e-16 PASS; dWater=2.2e-16 PASS
   T0=320 yv=0.05: diag=1 T=320.0000000000 oracle=320.0000000000 dT=0.0e+00 PASS; dU=0.0e+00 PASS; dWater=2.2e-16 PASS
 == b. uv-solver partition: |T - T_oracle| <= 1e-09 K, U rel 1e-10, water rel 1e-14
   T0=280 yv=0.02: diag=4 T=281.9157077988 oracle=281.9157077988 dT=5.7e-14 PASS; dU=1.6e-15 PASS; dWater=2.2e-16 PASS
@@ -12,18 +9,18 @@ kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
   T0=320 yv=0.05: diag=1 T=320.0000000000 oracle=320.0000000000 dT=0.0e+00 PASS; dU=0.0e+00 PASS; dWater=2.2e-16 PASS
 == b. KKT vs partition final T, tol 1e-6 K
   T0=280: |T_kkt - T_partition|=1.8e-09 PASS
-  T0=250: |T_kkt - T_partition|=1.4e-08 PASS
+  T0=250: |T_kkt - T_partition|=4.0e-12 PASS
   T0=320: |T_kkt - T_partition|=0.0e+00 PASS
-== c. partition near Tref, yv=0.05 (known defect D6): converged (diag>=0) and |dT|<=1e-9 K
-  T0=296: diag=5 U=-3.7623e+04 T=300.09050331 oracle=300.09050331 dT=5.7e-14
-  T0=298: diag=5 U=-1.8812e+04 T=301.68306618 oracle=301.68306618 dT=0.0e+00
-  T0=299: diag=-1 U=-9.4058e+03 T=299.00000000 oracle=302.47113637 dT=3.5e+00
-  T0=300: diag=-1 U=0.0000e+00 T=300.00000000 oracle=303.25368140 dT=3.3e+00
-  T0=301: diag=-1 U=9.4058e+03 T=301.00000000 oracle=304.03066775 dT=3.0e+00
-  T0=302: diag=5 U=1.8812e+04 T=304.80206565 oracle=304.80206565 dT=0.0e+00
-  T0=304: diag=5 U=3.7623e+04 T=306.32799568 oracle=306.32799568 dT=0.0e+00
-  failing T0: [299.0, 300.0, 301.0] (3/7)  EXPECTED-FAIL
+== c. partition near Tref, yv=0.05 (D6 regression): converged (diag>=0) and |dT|<=1e-9 K
+  T0=296: diag=4 U=-3.7623e+04 T=300.09050331 oracle=300.09050331 dT=3.4e-13
+  T0=298: diag=4 U=-1.8812e+04 T=301.68306618 oracle=301.68306618 dT=2.3e-13
+  T0=299: diag=4 U=-9.4058e+03 T=302.47113637 oracle=302.47113637 dT=1.1e-13
+  T0=300: diag=4 U=0.0000e+00 T=303.25368140 oracle=303.25368140 dT=5.7e-14
+  T0=301: diag=4 U=9.4058e+03 T=304.03066775 oracle=304.03066775 dT=1.1e-13
+  T0=302: diag=4 U=1.8812e+04 T=304.80206565 oracle=304.80206565 dT=5.7e-14
+  T0=304: diag=4 U=3.7623e+04 T=306.32799568 oracle=306.32799568 dT=5.7e-14
+  failing T0: [] (0/7)  PASS
 == d. oracle U(T) on 150..400 K: dU/dT > 0; analytic dU/dT vs central FD, tol 1e-7 rel
-  case T0=280 yv=0.02 (T_sat=295.650 K): min dU/dT=9.6664e+03 J/K/m3 PASS; max rel(analytic/FD-1)=3.5e-11 tol 1e-7 PASS
-  case T0=250 yv=0.01 (T_sat=284.124 K): min dU/dT=9.7532e+03 J/K/m3 PASS; max rel(analytic/FD-1)=3.0e-11 tol 1e-7 PASS
-  case T0=320 yv=0.05 (T_sat=312.706 K): min dU/dT=9.4058e+03 J/K/m3 PASS; max rel(analytic/FD-1)=4.6e-11 tol 1e-7 PASS
+  case T0=280 yv=0.02 (T_sat=295.650 K): min dU/dT=9.6664e+03 J/K/m3 PASS; max rel(analytic/FD-1)=3.6e-11 tol 1e-7 PASS
+  case T0=250 yv=0.01 (T_sat=284.124 K): min dU/dT=9.7532e+03 J/K/m3 PASS; max rel(analytic/FD-1)=3.4e-11 tol 1e-7 PASS
+  case T0=320 yv=0.05 (T_sat=312.706 K): min dU/dT=9.4058e+03 J/K/m3 PASS; max rel(analytic/FD-1)=4.7e-11 tol 1e-7 PASS
diff --git a/doc/tech-report/derivation-checks/check_ch6_evaporation.out b/doc/tech-report/derivation-checks/check_ch6_evaporation.out
index 3a9b82b..839c9e4 100644
--- a/doc/tech-report/derivation-checks/check_ch6_evaporation.out
+++ b/doc/tech-report/derivation-checks/check_ch6_evaporation.out
@@ -1,4 +1,4 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 (a) T = 80.0 K, K = 3.157972e+00 mol/m^3, kappa = 7.392000e+01 1/s, c_p = 0.7
 (a1) c_v = 0.5K: |rate - kappa c_p (K - c_v)|/ref: measured 1.739e-16  tol 1e-10  PASS
 (a2) c_v = K: |rate| / (kappa c_p K): measured 1.406e-16  tol 1e-12  PASS
diff --git a/doc/tech-report/derivation-checks/check_ch6_jacobian.out b/doc/tech-report/derivation-checks/check_ch6_jacobian.out
index b733f1f..4585568 100644
--- a/doc/tech-report/derivation-checks/check_ch6_jacobian.out
+++ b/doc/tech-report/derivation-checks/check_ch6_jacobian.out
@@ -1,4 +1,4 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
   dr/dc_A: jacobian -2.8232709637e+06  FD(fixed U) -2.8232709635e+06  rel err 7.11e-11  | FD(fixed T) 2.8232709635e+06  (feedback share 2.00e+00)
   dr/dc_B: jacobian -7.2934499896e+06  FD(fixed U) -7.2934499898e+06  rel err 3.53e-11  | FD(fixed T) 1.8821806425e+06  (feedback share 1.26e+00)
   dr/dc_C: jacobian 1.4116354819e+07  FD(fixed U) 1.4116354817e+07  rel err 1.04e-10  | FD(fixed T) 0.0000000000e+00  (feedback share 1.00e+00)
@@ -7,7 +7,7 @@ T-feedback Jacobian vs fixed-U FD, worst rel err: measured 1.041e-10  tol 1e-08
   forward dr/dc_O2: jacobian 2.4648392548e+01  FD(fixed U) 2.4648392548e+01  rel err 2.56e-11
   forward dr/dc_O3: jacobian 9.6071688371e-01  FD(fixed U) 9.6071688405e-01  rel err 3.54e-10
 reversible O + O2 <=> O3, forward column T-feedback Jacobian vs fixed-U FD, worst rel err: measured 3.536e-10  tol 1e-08  PASS
-  reverse dr/dc_O: jacobian 7.2053766278e+03  FD(fixed U) -4.2431786765e-06  rel err 1.70e+09
-  reverse dr/dc_O2: jacobian 7.2053766278e+03  FD(fixed U) -4.2431787219e-06  rel err 1.70e+09
-  reverse dr/dc_O3: jacobian 4.8035844222e+02  FD(fixed U) 8.1989914491e-08  rel err 5.86e+09
-reversible O + O2 <=> O3, reverse column T-feedback Jacobian vs fixed-U FD, worst rel err: measured 5.859e+09  tol 1e-08  EXPECTED-FAIL  (D65: reverse rc_ddT is a copy of dk_f/dT)
+  reverse dr/dc_O: jacobian -4.2431786841e-06  FD(fixed U) -4.2431786765e-06  rel err 1.80e-09
+  reverse dr/dc_O2: jacobian -4.2431786841e-06  FD(fixed U) -4.2431787219e-06  rel err 8.91e-09
+  reverse dr/dc_O3: jacobian 8.1989914601e-08  FD(fixed U) 8.1989914491e-08  rel err 1.35e-09
+reversible O + O2 <=> O3, reverse column T-feedback Jacobian vs fixed-U FD, worst rel err: measured 8.915e-09  tol 1e-08  PASS  (D65 regression)
diff --git a/doc/tech-report/derivation-checks/check_ch6_rates.out b/doc/tech-report/derivation-checks/check_ch6_rates.out
index 1a542ff..62f18d9 100644
--- a/doc/tech-report/derivation-checks/check_ch6_rates.out
+++ b/doc/tech-report/derivation-checks/check_ch6_rates.out
@@ -1,4 +1,4 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
 [a1] max rel |rate - k prod c^order|: 0.000e+00 (tol 1e-13) PASS
      forward_orders == react_stoich: True; order of H in '2 H => H2' = 2
 [a2] max |atom matrix @ stoich| (exact): 0.000e+00 (tol 0e+00) PASS
@@ -10,16 +10,16 @@ kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
 [c1] max rel |k - k0 M/(1 + k0 M/kinf)|, Pr = 1e-6..1e6: 4.441e-16 (tol 1e-12) PASS
 [c2] low-P limit |k/(k0 M) - 1| at Pr=1e-6: 1.000e-06 (tol 2e-06) PASS
 [c3] high-P limit |k/kinf - 1| at Pr=1e6: 1.000e-06 (tol 2e-06) PASS
-[d1] T=300 max |r_f - r_r|/r_f per reaction: 1.138e-16 (tol 1e-10) PASS
+[d1] T=300 max |r_f - r_r|/r_f per reaction: 2.802e-14 (tol 1e-10) PASS
 [d1] T=300 max |stoich @ rate| / max r_f: 1.138e-16 (tol 1e-10) PASS
 [d1] T=300 R1 K_c code (k_f/k_r) = 2.805844e+10 vs ours 2.805844e+10; rel: 1.110e-16 (tol 1e-10) PASS
-[d1] T=300 R2 K_c code (k_f/k_r) = 4.048789e+68 vs ours 4.048789e+68; rel: 0.000e+00 (tol 1e-10) PASS
+[d1] T=300 R2 K_c code (k_f/k_r) = 4.048789e+68 vs ours 4.048789e+68; rel: 2.842e-14 (tol 1e-10) PASS
 [d1] T=1500 max |r_f - r_r|/r_f per reaction: 1.053e-14 (tol 1e-10) PASS
 [d1] T=1500 max |stoich @ rate| / max r_f: 3.504e-15 (tol 1e-10) PASS
 [d1] T=1500 R1 K_c code (k_f/k_r) = 9.740225e-05 vs ours 9.740225e-05; rel: 3.553e-15 (tol 1e-10) PASS
 [d1] T=1500 R2 K_c code (k_f/k_r) = 7.788137e+13 vs ours 7.788137e+13; rel: 1.066e-14 (tol 1e-10) PASS
 [d2] forward column rc_ddT vs FD dk_f/dT, rel: 2.416e-10 (tol 1e-06) PASS
-     reverse R1: code rc_ddT = -8.190111e+01, FD dk_r/dT = 4.823080e-08, analytic d(k_f/K_c)/dT = 4.823080e-08
-     predicted code - true = dk_f/dT - d(k_f/K_c)/dT = -8.190111e+01; observed -8.190111e+01
-[d2] reverse column rc_ddT vs FD dk_r/dT, rel: 1.698e+09 (tol 1e-06) EXPECTED-FAIL  (reverse column is a copy of dk_f/dT: no 1/K_c, no van 't Hoff term)
-[d2] observed defect vs predicted (dk_f/dT - dk_r/dT), rel: 2.416e-10 (tol 1e-05) PASS
+     reverse R1: code rc_ddT = 4.823080e-08, FD dk_r/dT = 4.823080e-08, analytic d(k_f/K_c)/dT = 4.823080e-08
+     predicted code - true = dk_f/dT - d(k_f/K_c)/dT = -8.190111e+01; observed -1.072998e-15
+[d2] reverse column rc_ddT vs FD dk_r/dT, rel: 2.225e-08 (tol 1e-06) PASS  (reverse column is a copy of dk_f/dT: no 1/K_c, no van 't Hoff term)
+[d2] observed defect vs predicted (dk_f/dT - dk_r/dT), rel: 1.000e+00 (tol 1e-05) FAIL
diff --git a/doc/tech-report/derivation-checks/check_ch9_budget_below1.out b/doc/tech-report/derivation-checks/check_ch9_budget_below1.out
index 54892e8..e812828 100644
--- a/doc/tech-report/derivation-checks/check_ch9_budget_below1.out
+++ b/doc/tech-report/derivation-checks/check_ch9_budget_below1.out
@@ -1,12 +1,12 @@
-kintera 2.6.5 from $KINTERA_WT/_pyinstall/kintera/__init__.py
-   (y1) hog total 0.5, excess 0.21: corrected rule total_after = 0.300000, code total_after = 0.405000, pinned-code formula 0.51 - 0.21 * 0.5 = 0.405000
+kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py
+   (y1) hog total 0.5, excess 0.21: corrected rule total_after = 0.300000, code total_after = 0.300000, pinned-code formula 0.51 - 0.21 * 0.5 = 0.405000
 (y1) corrected rule meets the budget: |total_after / 0.3 - 1|: measured 0.000e+00  tol 1e-13  PASS
 (y1) corrected rule: no hog negative (min c): measured 0.000e+00  tol 0e+00  PASS
-(y1) code equals the pinned-code formula eq-ch09-conservation-code: |total_after - 0.405| / 0.405: measured 0.000e+00  tol 1e-13  PASS
-(y1) code meets the budget: |total_after / 0.3 - 1| (K9, UCzhangxi/kintera#54): measured 3.500e-01  tol 1e-13  EXPECTED-FAIL
-   (y2) unit scale s = 1e-03: total_after / (s budget) corrected 1.000000, code 1.699650
+(y1) code equals the pinned-code formula eq-ch09-conservation-code: |total_after - 0.405| / 0.405: measured 2.593e-01  tol 1e-13  FAIL
+(y1) code meets the budget: |total_after / 0.3 - 1| (K9, UCzhangxi/kintera#54): measured 0.000e+00  tol 1e-13  PASS
+   (y2) unit scale s = 1e-03: total_after / (s budget) corrected 1.000000, code 1.000000
    (y2) unit scale s = 1e+03: total_after / (s budget) corrected 1.000000, code 1.000000
    (y2) unit scale s = 1e+06: total_after / (s budget) corrected 1.000000, code 1.000000
 (y2) corrected rule is unit-independent: max rel |trim(s c) - s trim(c)|: measured 5.421e-17  tol 1e-13  PASS
-(y2) code is unit-independent: max rel |code(s c) - s code(c)| (K9, UCzhangxi/kintera#54): measured 1.050e-01  tol 1e-13  EXPECTED-FAIL
-ALL PASS, 2 EXPECTED-FAIL
+(y2) code is unit-independent: max rel |code(s c) - s code(c)| (K9, UCzhangxi/kintera#54): measured 5.421e-17  tol 1e-13  PASS
+1 FAIL

```
