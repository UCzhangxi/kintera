# Chapter corrections: regenerated output ledger

Prior preserved reproduction: `073de157adb0a27b7af03f2242277c2200097f24`. Native source: `e357792d50639d68e9090b542edf038d2b029aa2` (Kintera 2.6.7); Torch 2.10.0+cu128; Python 3.11.13. This ledger records the new run, not reviewer approval. File references below are relative to `doc/tech-report`; the delivery report resolves them at the final full report SHA.

## Scope and quantitative changes

Ch4: 23 formerly failing partition figure cells now converge (25/25 total); the independent seven-start check passes at 1e-9 K, with maximum oracle error 3.4e-13 K. Only the two authorized ch4 figure/data baseline records were regenerated; all other baseline records and tolerances are unchanged. The 190 K cold-start residual changes by 3.33e-16. Reduced iteration-budget failures remain documented. D6/D12 and partition-cap descriptions now describe the pinned source and measured controls.

Ch5: kinetics default Pref changes from 101325 to 100000 Pa; the default/one-bar Kc ratio is now 1.000000 rather than 0.986923. The rank experiment also refreshes its x86-64 roundoff values from the same run. Historical arm64 evidence remains labelled historical. The water baseline and eight-ULP policy are unchanged.

Ch14: all six default saturation cells converge at max_iter=100. Warming changes from [22.352,21.810,20.554,13.713,9.087,3.756] to [28.163,27.660,26.127,18.686,11.822,4.714] K. An explicit max_iter=10 control gives the same warming at printed 0.001 K precision, although its first cell reports failure. This excludes the cap increase as the explanation at that precision; attribution to a particular latent-energy source change remains an unisolated hypothesis. Cp/Cv remains EXPECTED-FAIL (S14-1); updating its values does not resolve that scientific gap.

Shared glossary notes were regenerated from the registry after updating only Pref/reactions/cv_R/reference-state source references. Mechanical note changes outside chapters 4/5/14 (including the generated appendix H glossary) do not revise their other scientific claims or remove the appendix authorship exclusions. Package examples and chapter 12/13 resources remain outside this integration.

## Commands in this regeneration

| Command | Exit | Committed output |
|---|---:|---|
| `python /work/doc/tech-report/derivation-checks/check_ch4_uv.py` | 0 | `derivation-checks/check_ch4_uv.out` |
| `python /work/doc/tech-report/derivation-checks/check_ch4_tp.py` | 0 | `derivation-checks/check_ch4_tp.out` |
| `python /work/doc/tech-report/derivation-checks/check_ch5_equilibrium.py` | 0 | `derivation-checks/check_ch5_equilibrium.out` |
| `python /work/doc/tech-report/derivation-checks/check_ch14_coupling.py` | 0 | `derivation-checks/check_ch14_coupling.out` |
| `python /work/doc/tech-report/derivation-checks/check_ch14_coupling.py --max-iter 10` | 0 | `derivation-checks/check_ch14_coupling-maxiter10.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_host_rh.py` | 0 | `src/kintera_report/ch04/runs/uv_host_rh.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/partition_maxiter.py` | 0 | `src/kintera_report/ch04/runs/partition_maxiter.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/partition_tref.py 250 partition` | 0 | `src/kintera_report/ch04/runs/partition_tref-250-partition.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/partition_tref.py 250 kkt` | 0 | `src/kintera_report/ch04/runs/partition_tref-250-kkt.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_coldstart.py 10` | 0 | `src/kintera_report/ch04/runs/uv_coldstart-10.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_coldstart.py 20` | 0 | `src/kintera_report/ch04/runs/uv_coldstart-20.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_coldstart.py 30` | 0 | `src/kintera_report/ch04/runs/uv_coldstart-30.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_h2cp.py nh3_160 on` | 0 | `src/kintera_report/ch04/runs/uv_h2cp-nh3_160-on.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_h2cp.py nh3_160 off` | 0 | `src/kintera_report/ch04/runs/uv_h2cp-nh3_160-off.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_h2cp.py nh3_120 on` | 0 | `src/kintera_report/ch04/runs/uv_h2cp-nh3_120-on.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_h2cp.py nh3_120 off` | 0 | `src/kintera_report/ch04/runs/uv_h2cp-nh3_120-off.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_h2cp.py h2o_300 on` | 0 | `src/kintera_report/ch04/runs/uv_h2cp-h2o_300-on.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/uv_h2cp.py h2o_300 off` | 0 | `src/kintera_report/ch04/runs/uv_h2cp-h2o_300-off.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/fig_tp_sweep.py /work/doc/tech-report/src/kintera_report/ch04/data/tp_coldstart.json` | 0 | `src/kintera_report/ch04/runs/fig_tp_sweep.out` |
| `python -P /work/doc/tech-report/src/kintera_report/ch04/runs/fig_partition.py /work/doc/tech-report/src/kintera_report/ch04/data/uv_partition_tref.json` | 0 | `src/kintera_report/ch04/runs/fig_partition.out` |

## Exact quoted-line mappings

All literal chapter quotes matching these outputs are listed, including unchanged neighboring quotes for auditability. The six requested ch14 changes are n/o/p/k0/t/v.

| Chapter location | Output location | Regenerated quoted line |
|---|---|---|
| `book/chapters/14-coupling/_thermo.qmd:124` | `derivation-checks/check_ch14_coupling.out:9` | `(a) DY->V (snapy moist_mixture.cpp:149) against rho*(1-sum y), rho*y: max rel err 1.97e-16 (tol 1e-14) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:125` | `derivation-checks/check_ch14_coupling.out:10` | `(b) V->Y after DY->V returns the mass fractions: max rel err 3.62e-16 (tol 1e-14) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:126` | `derivation-checks/check_ch14_coupling.out:11` | `(c) VT->U [J/m^3] against sum c_i R (u0_i - cv_i Tref + cv_i T), c = rho_i/mu_i: max rel err 2.33e-16 (tol 1e-12) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:127` | `derivation-checks/check_ch14_coupling.out:12` | `(d) VU->T(VT->U(T)) round trip (moist_mixture.cpp:150): max rel err 2.22e-16 (tol 1e-10) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:128` | `derivation-checks/check_ch14_coupling.out:13` | `(e) VT->P against R T sum_gas rho_i/mu_i (moist_mixture.cpp:151): max rel err 4.44e-16 (tol 1e-14) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:129` | `derivation-checks/check_ch14_coupling.out:14` | `(f) PV->T (moist_mixture.cpp:290) inverts VT->P: max rel err 4.44e-16 (tol 1e-14) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:130` | `derivation-checks/check_ch14_coupling.out:15` | `(g) Y->X (run_hydro.cpp:179) against x_i = (y_i/mu_i)/sum_j(y_j/mu_j), dry included: max rel err 3.47e-18 (tol 1e-15) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:131` | `derivation-checks/check_ch14_coupling.out:16` | `(h) IdealMoist W->I formula against kintera VT->U at the same state: max rel err 4.95e-16 (tol 1e-12) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:132` | `derivation-checks/check_ch14_coupling.out:17` | `(i) IdealMoist W->T = p/(rho Rd f_eps) against the state temperature: max rel err 3.33e-16 (tol 1e-13) PASS` |
| `book/chapters/14-coupling/_thermo.qmd:133` | `derivation-checks/check_ch14_coupling.out:18` | `(j) the options object snapy reads after ThermoYImpl::create holds the T=0 offsets (uref - cref Tref): True PASS` |
| `book/chapters/14-coupling/_saturation.qmd:112` | `derivation-checks/check_ch14_coupling.out:19` | `(k0) diag per cell at the default max_iter 100 (negative = failed): 11 9 9 7 5 4 INFO` |
| `book/chapters/14-coupling/_saturation.qmd:106` | `derivation-checks/check_ch14_coupling.out:20` | `(k) adjustment moved mass fractions by up to 1.00e+00 of the largest (state was supersaturated) PASS` |
| `book/chapters/14-coupling/_saturation.qmd:107` | `derivation-checks/check_ch14_coupling.out:21` | `(l) total density rho_dry + sum y' rho equals rho (dry row untouched): max rel err 2.22e-16 (tol 1e-14) PASS` |
| `book/chapters/14-coupling/_saturation.qmd:108` | `derivation-checks/check_ch14_coupling.out:22` | `(m) element moles H, He, N, O, S per cell conserved: max rel err 3.69e-16 (tol 1e-13) PASS` |
| `book/chapters/14-coupling/_saturation.qmd:109` | `derivation-checks/check_ch14_coupling.out:23` | `(n) snapy's next VU->T at fixed ie (meshblock.cpp:825) = linear-model T: max rel err 2.22e-16 (tol 1e-12) PASS` |
| `book/chapters/14-coupling/_saturation.qmd:110` | `derivation-checks/check_ch14_coupling.out:24` | `(o) latent warming T' - T per cell [K]: 28.163 27.660 26.127 18.686 11.822 4.714 INFO` |
| `book/chapters/14-coupling/_saturation.qmd:111` | `derivation-checks/check_ch14_coupling.out:25` | `(p) max relative humidity per cell at (T', p') after the adjustment: 1.000000 1.000000 1.000000 1.000000 1.000000 1.000000 INFO` |
| `book/chapters/14-coupling/_saturation.qmd:113` | `derivation-checks/check_ch14_coupling.out:26` | `(q) max_iter = 1: 6 failed cell(s) counted, count reset to 0 on the second read PASS` |
| `book/chapters/14-coupling/_saturation.qmd:114` | `derivation-checks/check_ch14_coupling.out:27` | `(r) failed cells: written state still conserves total density: max rel err 2.22e-16 (tol 1e-14) PASS` |
| `book/chapters/14-coupling/_kinetics.qmd:80` | `derivation-checks/check_ch14_coupling.out:28` | `(s) gas concentrations from Y->X then TPX->V equal rho_i/mu_i [mol/m^3]: max rel err 4.44e-16 (tol 1e-12) PASS` |
| `book/chapters/14-coupling/_kinetics.qmd:81` | `derivation-checks/check_ch14_coupling.out:29` | `(t) cloud concentrations from TPX->V against rho_i/mu_i: max rel diff 6.66e-16 (filed as D16; the driver's tendencies start from these) INFO` |
| `book/chapters/14-coupling/_kinetics.qmd:82` | `derivation-checks/check_ch14_coupling.out:30` | `(u) sum_i M_i delta_i = 0 for a stoichiometric change (mass hand-back): max rel err 2.13e-16 (tol 1e-14) PASS` |
| `book/chapters/14-coupling/_kinetics.qmd:139` | `derivation-checks/check_ch14_coupling.out:31` | `(v) ratio of the volumetric heat capacity the drivers pass (TV->cp) to the C_V of the fixed-U Jacobian: 1.3853 1.3853 1.3854 1.3880 1.3921 1.3968 EXPECTED-FAIL (S14-1)` |
| `book/chapters/14-coupling/_kinetics.qmd:118` | `derivation-checks/check_ch14_coupling.out:32` | `(w) split-step local error / dt^2 against [B,A]/2: rel diff 6.32e-03 at dt=1e-2, 6.30e-04 at dt=1e-3 (first order in dt; tol 2e-2 at 1e-2) PASS` |

## Narrative quantity mappings

| Chapter file and line (under book/chapters) | Committed output source |
|---|---|
| `04-phase-equilibrium/_equilibrate-uv.qmd:200` (1.8\times10^{-9}) | `derivation-checks/check_ch4_uv.out` lines 3 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:276` (4.7\times10^{-11}) | `derivation-checks/check_ch4_uv.out` lines 26 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:357` (all cells converge for outer budgets) | `src/kintera_report/ch04/runs/partition_maxiter.out` lines 1, 2, 3, 4 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:443` (every partition cell converges) | `src/kintera_report/ch04/runs/fig_partition.out` lines 1, 2 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:446` (round to zero) | `src/kintera_report/ch04/runs/partition_tref-250-partition.out` lines 2, 3 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:447` (largest oracle temperature difference) | `derivation-checks/check_ch4_uv.out` lines 15, 3 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:408` (7.2\times10^{-8}) | `src/kintera_report/ch04/runs/uv_host_rh.out` lines 8, 10 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:457` (2.220\times10^{-16}) | `src/kintera_report/ch04/runs/uv_h2cp-nh3_160-on.out` lines 1 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:457` (3.730\times10^{-14}) | `src/kintera_report/ch04/runs/uv_h2cp-nh3_120-on.out` lines 1 |
| `04-phase-equilibrium/_equilibrate-uv.qmd:458` (-6.994\times10^{-15}) | `src/kintera_report/ch04/runs/uv_h2cp-h2o_300-on.out` lines 1 |

## Complete numerical output line index

This index also maps rounded narrative quantities and all control experiments to exact committed output lines. Labels in each output identify the corresponding equation/case.

### `derivation-checks/check_ch4_uv.out`

| Line | Output |
|---:|---|
| 1 | `kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py` |
| 2 | `== a. uv-solver kkt: &#124;T - T_oracle&#124; <= 1e-06 K, U rel 1e-10, water rel 1e-14` |
| 3 | `  T0=280 yv=0.02: diag=6 T=281.9157078006 oracle=281.9157077988 dT=1.8e-09 PASS; dU=3.3e-16 PASS; dWater=0.0e+00 PASS` |
| 4 | `  T0=250 yv=0.01: diag=7 T=251.6354488589 oracle=251.6354488589 dT=4.0e-12 PASS; dU=1.1e-16 PASS; dWater=2.2e-16 PASS` |
| 5 | `  T0=320 yv=0.05: diag=1 T=320.0000000000 oracle=320.0000000000 dT=0.0e+00 PASS; dU=0.0e+00 PASS; dWater=2.2e-16 PASS` |
| 6 | `== b. uv-solver partition: &#124;T - T_oracle&#124; <= 1e-09 K, U rel 1e-10, water rel 1e-14` |
| 7 | `  T0=280 yv=0.02: diag=4 T=281.9157077988 oracle=281.9157077988 dT=5.7e-14 PASS; dU=1.6e-15 PASS; dWater=2.2e-16 PASS` |
| 8 | `  T0=250 yv=0.01: diag=4 T=251.6354488589 oracle=251.6354488589 dT=2.8e-14 PASS; dU=0.0e+00 PASS; dWater=0.0e+00 PASS` |
| 9 | `  T0=320 yv=0.05: diag=1 T=320.0000000000 oracle=320.0000000000 dT=0.0e+00 PASS; dU=0.0e+00 PASS; dWater=2.2e-16 PASS` |
| 10 | `== b. KKT vs partition final T, tol 1e-6 K` |
| 11 | `  T0=280: &#124;T_kkt - T_partition&#124;=1.8e-09 PASS` |
| 12 | `  T0=250: &#124;T_kkt - T_partition&#124;=4.0e-12 PASS` |
| 13 | `  T0=320: &#124;T_kkt - T_partition&#124;=0.0e+00 PASS` |
| 14 | `== c. partition near Tref, yv=0.05 (D6 regression): converged (diag>=0) and &#124;dT&#124;<=1e-9 K` |
| 15 | `  T0=296: diag=4 U=-3.7623e+04 T=300.09050331 oracle=300.09050331 dT=3.4e-13` |
| 16 | `  T0=298: diag=4 U=-1.8812e+04 T=301.68306618 oracle=301.68306618 dT=2.3e-13` |
| 17 | `  T0=299: diag=4 U=-9.4058e+03 T=302.47113637 oracle=302.47113637 dT=1.1e-13` |
| 18 | `  T0=300: diag=4 U=0.0000e+00 T=303.25368140 oracle=303.25368140 dT=5.7e-14` |
| 19 | `  T0=301: diag=4 U=9.4058e+03 T=304.03066775 oracle=304.03066775 dT=1.1e-13` |
| 20 | `  T0=302: diag=4 U=1.8812e+04 T=304.80206565 oracle=304.80206565 dT=5.7e-14` |
| 21 | `  T0=304: diag=4 U=3.7623e+04 T=306.32799568 oracle=306.32799568 dT=5.7e-14` |
| 22 | `  failing T0: [] (0/7)  PASS` |
| 23 | `== d. oracle U(T) on 150..400 K: dU/dT > 0; analytic dU/dT vs central FD, tol 1e-7 rel` |
| 24 | `  case T0=280 yv=0.02 (T_sat=295.650 K): min dU/dT=9.6664e+03 J/K/m3 PASS; max rel(analytic/FD-1)=3.6e-11 tol 1e-7 PASS` |
| 25 | `  case T0=250 yv=0.01 (T_sat=284.124 K): min dU/dT=9.7532e+03 J/K/m3 PASS; max rel(analytic/FD-1)=3.4e-11 tol 1e-7 PASS` |
| 26 | `  case T0=320 yv=0.05 (T_sat=312.706 K): min dU/dT=9.4058e+03 J/K/m3 PASS; max rel(analytic/FD-1)=4.7e-11 tol 1e-7 PASS` |

### `derivation-checks/check_ch4_tp.out`

| Line | Output |
|---:|---|
| 1 | `kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py` |
| 2 | `== a. complementarity (&#124;res&#124;<=1e-6 if condensate present, res<0 if absent); elements 1e-14` |
| 3 | `== b. TP gain[H2O,H2O] vs central FD of ln(x_H2O/x_g) along H2O->H2O(l), tol 1e-7 rel` |
| 4 | `T=300 K  diag=1` |
| 5 | `  a H2O->H2O(l)        cloud=0.000e+00 res=-5.708e-01  tol res<0        PASS` |
| 6 | `  a NH3->NH3(s)        cloud=0.000e+00 res=-7.087e+00  tol res<0        PASS` |
| 7 | `  a NH3+H2S->NH4SH(s)  cloud=0.000e+00 res=-8.635e+00  tol res<0        PASS` |
| 8 | `  a element O/dry rel change=0.0e+00  tol 1e-14 PASS` |
| 9 | `  a element N/dry rel change=0.0e+00  tol 1e-14 PASS` |
| 10 | `  a element S/dry rel change=0.0e+00  tol 1e-14 PASS` |
| 11 | `T=250 K  diag=9` |
| 12 | `  a H2O->H2O(l)        cloud=1.925e-02 res=-1.616e-08  tol &#124;res&#124;<=1e-6  PASS` |
| 13 | `  a NH3->NH3(s)        cloud=0.000e+00 res=-5.476e+00  tol res<0        PASS` |
| 14 | `  a NH3+H2S->NH4SH(s)  cloud=0.000e+00 res=-1.374e+00  tol res<0        PASS` |
| 15 | `  a element O/dry rel change=0.0e+00  tol 1e-14 PASS` |
| 16 | `  a element N/dry rel change=2.2e-16  tol 1e-14 PASS` |
| 17 | `  a element S/dry rel change=2.2e-16  tol 1e-14 PASS` |
| 18 | `  b gain=-1.3369663184e+03 FD=-1.3369663180e+03 rel=3.3e-10 tol 1e-7 PASS; without -sum(nu)/x_g: -1.337986e+03 (rel 7.6e-04)` |
| 19 | `T=200 K  diag=18` |
| 20 | `  a H2O->H2O(l)        cloud=2.010e-02 res=-1.119e-09  tol &#124;res&#124;<=1e-6  PASS` |
| 21 | `  a NH3->NH3(s)        cloud=0.000e+00 res=-7.536e+00  tol res<0        PASS` |
| 22 | `  a NH3+H2S->NH4SH(s)  cloud=4.981e-03 res=-3.126e-08  tol &#124;res&#124;<=1e-6  PASS` |
| 23 | `  a element O/dry rel change=5.6e-16  tol 1e-14 PASS` |
| 24 | `  a element N/dry rel change=3.3e-16  tol 1e-14 PASS` |
| 25 | `  a element S/dry rel change=3.3e-16  tol 1e-14 PASS` |
| 26 | `  b gain=-6.3797848693e+05 FD=-6.3797848656e+05 rel=5.8e-10 tol 1e-7 PASS; without -sum(nu)/x_g: -6.379795e+05 (rel 1.6e-06)` |
| 27 | `T=160 K  diag=32` |
| 28 | `  a H2O->H2O(l)        cloud=2.010e-02 res=-4.108e-11  tol &#124;res&#124;<=1e-6  PASS` |
| 29 | `  a NH3->NH3(s)        cloud=0.000e+00 res=-9.696e+00  tol res<0        PASS` |
| 30 | `  a NH3+H2S->NH4SH(s)  cloud=5.025e-03 res=-1.331e-07  tol &#124;res&#124;<=1e-6  PASS` |
| 31 | `  a element O/dry rel change=3.3e-16  tol 1e-14 PASS` |
| 32 | `  a element N/dry rel change=0.0e+00  tol 1e-14 PASS` |
| 33 | `  a element S/dry rel change=3.3e-16  tol 1e-14 PASS` |
| 34 | `  b gain=-1.4525630998e+09 FD=-1.4525630997e+09 rel=4.2e-11 tol 1e-7 PASS; without -sum(nu)/x_g: -1.452563e+09 (rel 7.5e-10)` |
| 35 | `== c. default max-iter on cold-start cells 130..250 K (D4 regression)` |
| 36 | `  max-iter=100 (default): non-converged 0/13; diag=[46, 41, 33, 32, 26, 23, 21, 18, 16, 14, 12, 11, 9]  tol 0  PASS` |
| 37 | `  max-iter=100: non-converged 0/13; iterations=[46, 41, 33, 32, 26, 23, 21, 18, 16, 14, 12, 11, 9]  tol 0  PASS` |

### `derivation-checks/check_ch5_equilibrium.out`

| Line | Output |
|---:|---|
| 1 | `kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py` |
| 2 | `== a. two-phase vapour-liquid, T=300 K, p=1e5 Pa, n0=(1, .05, .05)` |
| 3 | `  n_v=3.66933196081383e-02 analytic=3.66933196082227e-02 rel=2.3e-12 tol 1e-10 PASS` |
| 4 | `  status=0 (0 = converged) PASS; iterations=4; reported error=2.2e-12 <= ftol=1e-08 PASS` |
| 5 | `  water conservation rel=0.0e+00 tol 1e-14 PASS` |
| 6 | `== b. Newton Jacobian at the converged state vs central FD along the reaction direction` |
| 7 | `  J=2.628831174589e+01 FD=2.628831174035e+01 rel=2.1e-10 tol 1e-8 PASS  (returned gain 2.628837e+01 is from the last Newton iterate)` |
| 8 | `== c. 2 H2 + O2 <=> 2 H2O, Nasa9LogK, T=3500 K, p=p0=1e5 Pa` |
| 9 | `  lnK=3.3267652907 status=0 n=['3.282195e-01', '6.410976e-02', '4.717805e-01']` |
| 10 | `  &#124;residual&#124;=8.0e-12 tol 1e-10 PASS` |
| 11 | `  H rel=0.0e+00 tol 1e-14 PASS; O rel=2.2e-16 tol 1e-14 PASS` |
| 12 | `  table parse: Delta g/RT table=-3.326765290687 library=-3.326765290687 rel=0.0e+00 tol 1e-12 PASS` |
| 13 | `  van 't Hoff: FD dlnK/dT=-4.9501006409e-03 Delta h/(R T^2)=-4.9501006385e-03 rel=4.7e-10 tol 1e-6 PASS` |
| 14 | `== d. returned gain vs the Jacobian formula (kintera's gain, not a copy)` |
| 15 | `  three-phase system, max-iter 1 (gain formed at the input): max rel &#124;gain - J(n0)&#124;=0.0e+00 tol 1e-14 PASS  (status 3; J singular, P > C: line f)` |
| 16 | `  water card, status 0 after 4 steps: gain=2.6288369104611e+01 J(iterate 3, status 2)=2.6288369104611e+01 rel=0.0e+00 tol 1e-14 PASS; J(returned)=2.6288311745887e+01 rel 2.2e-06` |
| 17 | `  water card, start (1, .01, .001), status 4: gain=8.9919971225634e+01 J(returned)=8.9919971225634e+01 rel=0.0e+00 tol 1e-14 PASS` |
| 18 | `== e. numpy copy of the iteration, plain LU direction, no least-squares fallback, vs kintera` |
| 19 | `  start (1.0, 0.05, 0.05): kintera status 0 steps 4 error 2.217e-12; copy status 0 steps 4 error 2.217e-12; max &#124;n_kintera - n_copy&#124;=0.0e+00 mol (rel 0.0e+00, tol 1e-14; per amount 0.0e+00, tol 1e-5) PASS` |
| 20 | `    smallest slack n - floor along the path=3.44e-02 mol (> 0: the fallback test d <= 0 never holds) PASS` |
| 21 | `  start (1.0, 0.01, 0.001): kintera status 4 steps 19 error 2.253e+00; copy status 4 steps 19 error 2.253e+00; max &#124;n_kintera - n_copy&#124;=0.0e+00 mol (rel 0.0e+00, tol 1e-14; per amount 0.0e+00, tol 1e-5) PASS` |
| 22 | `    smallest slack n - floor along the path=3.03e-15 mol (> 0: the fallback test d <= 0 never holds) PASS` |
| 23 | `    returned liquid=3.027e-15 mol; last halving loop: 40 scales rejected by the floor test, 0 by no decrease of max&#124;r&#124; (INFO)` |
| 24 | `== f. phase rule P <= C: three-phase system of line d (N=6, C=2, P=3, R=4), J singular` |
| 25 | `  rank S=4 (reactions independent), N - P = 3` |
| 26 | `  start state: sigma_min(J)=1.2e-16 sigma_max=2.214e+01 cond=1.8e+17 rank=3 tol 1e-12 PASS` |
| 27 | `  200 random states (seed 0, amounts 0.01..1 mol): max sigma_min(J)=4.9e-15 tol 1e-12 PASS` |
| 28 | `  kintera on it: max-iter 1: status 3 after 0 steps; max-iter default: status 4 after 1 steps (INFO: status 3 or 4 is decided by rounding)` |
| 29 | `== g. kinetics reference pressure: K_c of O + O2 <=> O3 at 1500 K (dn = -1)` |
| 30 | `  Pref=100000 Pa: K_c=9.7402248543e-05 vs 1-bar NASA-9 9.7402248543e-05 rel=1.1e-16 tol 1e-12 PASS` |
| 31 | `  default Pref=100000 Pa: K_c/K_c(1 bar)=1.000000, i.e. 0.0000e+00; expected (1e5/Pref)^(-dn)=1.000000, rel=0.0e+00 tol 1e-12 PASS` |
| 32 | `Warning: leastsq_kkt maximum number of iterations reached (1).` |
| 33 | `Warning: leastsq_kkt maximum number of iterations reached (1).` |

### `derivation-checks/check_ch14_coupling.out`

| Line | Output |
|---:|---|
| 1 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 2 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 3 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 4 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 5 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 6 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 7 | `kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py` |
| 8 | `build: Linux x86_64, Python 3.11.13, torch 2.10.0+cu128` |
| 9 | `(a) DY->V (snapy moist_mixture.cpp:149) against rho*(1-sum y), rho*y: max rel err 1.97e-16 (tol 1e-14) PASS` |
| 10 | `(b) V->Y after DY->V returns the mass fractions: max rel err 3.62e-16 (tol 1e-14) PASS` |
| 11 | `(c) VT->U [J/m^3] against sum c_i R (u0_i - cv_i Tref + cv_i T), c = rho_i/mu_i: max rel err 2.33e-16 (tol 1e-12) PASS` |
| 12 | `(d) VU->T(VT->U(T)) round trip (moist_mixture.cpp:150): max rel err 2.22e-16 (tol 1e-10) PASS` |
| 13 | `(e) VT->P against R T sum_gas rho_i/mu_i (moist_mixture.cpp:151): max rel err 4.44e-16 (tol 1e-14) PASS` |
| 14 | `(f) PV->T (moist_mixture.cpp:290) inverts VT->P: max rel err 4.44e-16 (tol 1e-14) PASS` |
| 15 | `(g) Y->X (run_hydro.cpp:179) against x_i = (y_i/mu_i)/sum_j(y_j/mu_j), dry included: max rel err 3.47e-18 (tol 1e-15) PASS` |
| 16 | `(h) IdealMoist W->I formula against kintera VT->U at the same state: max rel err 4.95e-16 (tol 1e-12) PASS` |
| 17 | `(i) IdealMoist W->T = p/(rho Rd f_eps) against the state temperature: max rel err 3.33e-16 (tol 1e-13) PASS` |
| 18 | `(j) the options object snapy reads after ThermoYImpl::create holds the T=0 offsets (uref - cref Tref): True PASS` |
| 19 | `(k0) diag per cell at the default max_iter 100 (negative = failed): 11 9 9 7 5 4 INFO` |
| 20 | `(k) adjustment moved mass fractions by up to 1.00e+00 of the largest (state was supersaturated) PASS` |
| 21 | `(l) total density rho_dry + sum y' rho equals rho (dry row untouched): max rel err 2.22e-16 (tol 1e-14) PASS` |
| 22 | `(m) element moles H, He, N, O, S per cell conserved: max rel err 3.69e-16 (tol 1e-13) PASS` |
| 23 | `(n) snapy's next VU->T at fixed ie (meshblock.cpp:825) = linear-model T: max rel err 2.22e-16 (tol 1e-12) PASS` |
| 24 | `(o) latent warming T' - T per cell [K]: 28.163 27.660 26.127 18.686 11.822 4.714 INFO` |
| 25 | `(p) max relative humidity per cell at (T', p') after the adjustment: 1.000000 1.000000 1.000000 1.000000 1.000000 1.000000 INFO` |
| 26 | `(q) max_iter = 1: 6 failed cell(s) counted, count reset to 0 on the second read PASS` |
| 27 | `(r) failed cells: written state still conserves total density: max rel err 2.22e-16 (tol 1e-14) PASS` |
| 28 | `(s) gas concentrations from Y->X then TPX->V equal rho_i/mu_i [mol/m^3]: max rel err 4.44e-16 (tol 1e-12) PASS` |
| 29 | `(t) cloud concentrations from TPX->V against rho_i/mu_i: max rel diff 6.66e-16 (filed as D16; the driver's tendencies start from these) INFO` |
| 30 | `(u) sum_i M_i delta_i = 0 for a stoichiometric change (mass hand-back): max rel err 2.13e-16 (tol 1e-14) PASS` |
| 31 | `(v) ratio of the volumetric heat capacity the drivers pass (TV->cp) to the C_V of the fixed-U Jacobian: 1.3853 1.3853 1.3854 1.3880 1.3921 1.3968 EXPECTED-FAIL (S14-1)` |
| 32 | `(w) split-step local error / dt^2 against [B,A]/2: rel diff 6.32e-03 at dt=1e-2, 6.30e-04 at dt=1e-3 (first order in dt; tol 2e-2 at 1e-2) PASS` |

### `derivation-checks/check_ch14_coupling-maxiter10.out`

| Line | Output |
|---:|---|
| 1 | `[Warning] equilibrate_uv did not converge after 10 iterations.` |
| 2 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 3 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 4 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 5 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 6 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 7 | `[Warning] equilibrate_uv did not converge after 1 iterations.` |
| 8 | `kintera 2.6.7 from $KINTERA_WT/../../../../../../usr/local/lib/python3.11/site-packages/kintera/__init__.py` |
| 9 | `build: Linux x86_64, Python 3.11.13, torch 2.10.0+cu128` |
| 10 | `(a) DY->V (snapy moist_mixture.cpp:149) against rho*(1-sum y), rho*y: max rel err 1.97e-16 (tol 1e-14) PASS` |
| 11 | `(b) V->Y after DY->V returns the mass fractions: max rel err 3.62e-16 (tol 1e-14) PASS` |
| 12 | `(c) VT->U [J/m^3] against sum c_i R (u0_i - cv_i Tref + cv_i T), c = rho_i/mu_i: max rel err 2.33e-16 (tol 1e-12) PASS` |
| 13 | `(d) VU->T(VT->U(T)) round trip (moist_mixture.cpp:150): max rel err 2.22e-16 (tol 1e-10) PASS` |
| 14 | `(e) VT->P against R T sum_gas rho_i/mu_i (moist_mixture.cpp:151): max rel err 4.44e-16 (tol 1e-14) PASS` |
| 15 | `(f) PV->T (moist_mixture.cpp:290) inverts VT->P: max rel err 4.44e-16 (tol 1e-14) PASS` |
| 16 | `(g) Y->X (run_hydro.cpp:179) against x_i = (y_i/mu_i)/sum_j(y_j/mu_j), dry included: max rel err 3.47e-18 (tol 1e-15) PASS` |
| 17 | `(h) IdealMoist W->I formula against kintera VT->U at the same state: max rel err 4.95e-16 (tol 1e-12) PASS` |
| 18 | `(i) IdealMoist W->T = p/(rho Rd f_eps) against the state temperature: max rel err 3.33e-16 (tol 1e-13) PASS` |
| 19 | `(j) the options object snapy reads after ThermoYImpl::create holds the T=0 offsets (uref - cref Tref): True PASS` |
| 20 | `(k0) diag per cell at the explicit max_iter 10 (negative = failed): -2010 9 9 7 5 4 INFO` |
| 21 | `(k) adjustment moved mass fractions by up to 1.00e+00 of the largest (state was supersaturated) PASS` |
| 22 | `(l) total density rho_dry + sum y' rho equals rho (dry row untouched): max rel err 2.22e-16 (tol 1e-14) PASS` |
| 23 | `(m) element moles H, He, N, O, S per cell conserved: max rel err 3.69e-16 (tol 1e-13) PASS` |
| 24 | `(n) snapy's next VU->T at fixed ie (meshblock.cpp:825) = linear-model T: max rel err 2.22e-16 (tol 1e-12) PASS` |
| 25 | `(o) latent warming T' - T per cell [K]: 28.163 27.660 26.127 18.686 11.822 4.714 INFO` |
| 26 | `(p) max relative humidity per cell at (T', p') after the adjustment: 1.000000 1.000000 1.000000 1.000000 1.000000 1.000000 INFO` |
| 27 | `(q) max_iter = 1: 6 failed cell(s) counted, count reset to 0 on the second read PASS` |
| 28 | `(r) failed cells: written state still conserves total density: max rel err 2.22e-16 (tol 1e-14) PASS` |
| 29 | `(s) gas concentrations from Y->X then TPX->V equal rho_i/mu_i [mol/m^3]: max rel err 4.44e-16 (tol 1e-12) PASS` |
| 30 | `(t) cloud concentrations from TPX->V against rho_i/mu_i: max rel diff 6.66e-16 (filed as D16; the driver's tendencies start from these) INFO` |
| 31 | `(u) sum_i M_i delta_i = 0 for a stoichiometric change (mass hand-back): max rel err 2.13e-16 (tol 1e-14) PASS` |
| 32 | `(v) ratio of the volumetric heat capacity the drivers pass (TV->cp) to the C_V of the fixed-U Jacobian: 1.3853 1.3853 1.3854 1.3880 1.3921 1.3968 EXPECTED-FAIL (S14-1)` |
| 33 | `(w) split-step local error / dt^2 against [B,A]/2: rel diff 6.32e-03 at dt=1e-2, 6.30e-04 at dt=1e-3 (first order in dt; tol 2e-2 at 1e-2) PASS` |

### `src/kintera_report/ch04/runs/fig_partition.out`

| Line | Output |
|---:|---|
| 1 | `partition ln RH range -2.2093438190040858e-14 2.4868995751603197e-14 diag [5.0]` |
| 2 | `kkt ln RH range 4.529709940470536e-14 9.178442945672832e-07 diag [3.0, 4.0]` |

### `src/kintera_report/ch04/runs/fig_tp_sweep.out`

| Line | Output |
|---:|---|
| 1 | `max-iter 10: diag [-2010.0, -2010.0, -2010.0, -2010.0, -2010.0, -2010.0, -2010.0, -2010.0, -2010.0, -2010.0, 10.0, 8.0, 7.0]` |
| 2 | `  max ln RH [18.0, 13.9, 10.9, 8.91, 6.06, 4.04, 2.23, 0.603, -2.52e-06, -1.32e-07, -5.55e-10, -2.11e-12, -1.21e-11]` |
| 3 | `max-iter 60: diag [44.0, 39.0, 34.0, 27.0, 23.0, 20.0, 18.0, 15.0, 13.0, 11.0, 10.0, 8.0, 7.0]` |
| 4 | `  max ln RH [-3.79e-11, -2.86e-12, -5.4e-12, -2.43e-07, -9.36e-10, -1.01e-07, -1.69e-07, -1.34e-07, -2.79e-09, -1.32e-07, -5.55e-10, -2.11e-12, -1.21e-11]` |
| 5 | `equilibrate_tp did not converge after 10 iterations.` |
| 6 | `equilibrate_tp did not converge after 10 iterations.` |
| 7 | `equilibrate_tp did not converge after 10 iterations.` |
| 8 | `equilibrate_tp did not converge after 10 iterations.` |
| 9 | `equilibrate_tp did not converge after 10 iterations.` |
| 10 | `equilibrate_tp did not converge after 10 iterations.` |
| 11 | `equilibrate_tp did not converge after 10 iterations.` |
| 12 | `equilibrate_tp did not converge after 10 iterations.` |
| 13 | `equilibrate_tp did not converge after 10 iterations.` |
| 14 | `equilibrate_tp did not converge after 10 iterations.` |

### `src/kintera_report/ch04/runs/partition_maxiter.out`

| Line | Output |
|---:|---|
| 1 | `max-iter 3: failed 0 of 15, largest pass count 4, converged cells with condensate 11, their max &#124;ln RH&#124; 2.0e-13` |
| 2 | `max-iter 5: failed 0 of 15, largest pass count 4, converged cells with condensate 11, their max &#124;ln RH&#124; 2.0e-13` |
| 3 | `max-iter 10: failed 0 of 15, largest pass count 4, converged cells with condensate 11, their max &#124;ln RH&#124; 2.0e-13` |
| 4 | `max-iter 50: failed 0 of 15, largest pass count 4, converged cells with condensate 11, their max &#124;ln RH&#124; 2.0e-13` |

### `src/kintera_report/ch04/runs/partition_tref-250-kkt.out`

| Line | Output |
|---:|---|
| 1 | `Tref 250.0 solver kkt T0 [249.0, 249.5, 250.0, 250.5, 251.0]` |
| 2 | ` diag [5.0, 5.0, 5.0, 5.0, 5.0]` |
| 3 | ` ln RH after [-0.0, -0.0, -0.0, -0.0, -0.0]` |
| 4 | ` T after [290.6281, 290.8191, 291.0087, 291.197, 291.384]` |

### `src/kintera_report/ch04/runs/partition_tref-250-partition.out`

| Line | Output |
|---:|---|
| 1 | `Tref 250.0 solver partition T0 [249.0, 249.5, 250.0, 250.5, 251.0]` |
| 2 | ` diag [7.0, 7.0, 7.0, 7.0, 7.0]` |
| 3 | ` ln RH after [0.0, 0.0, 0.0, 0.0, -0.0]` |
| 4 | ` T after [290.6281, 290.8191, 291.0087, 291.197, 291.384]` |

### `src/kintera_report/ch04/runs/uv_coldstart-10.out`

| Line | Output |
|---:|---|
| 1 | `[Warning] equilibrate_uv did not converge after 10 iterations.` |
| 2 | `[Warning] equilibrate_uv did not converge after 10 iterations.` |
| 3 | `max-iter 10 diag [-2010.0, -2010.0, 9.0, 8.0, 6.0]` |
| 4 | ` max ln RH at the host temperature [-0.00418, -6.37e-09, -5.38e-13, -1.36e-09, -2.69e-08]` |

### `src/kintera_report/ch04/runs/uv_coldstart-20.out`

| Line | Output |
|---:|---|
| 1 | `max-iter 20 diag [14.0, 12.0, 9.0, 8.0, 6.0]` |
| 2 | ` max ln RH at the host temperature [4.3e-08, -6.37e-09, -5.38e-13, -1.36e-09, -2.69e-08]` |

### `src/kintera_report/ch04/runs/uv_coldstart-30.out`

| Line | Output |
|---:|---|
| 1 | `max-iter 30 diag [14.0, 12.0, 9.0, 8.0, 6.0]` |
| 2 | ` max ln RH at the host temperature [4.3e-08, -6.37e-09, -5.38e-13, -1.36e-09, -2.69e-08]` |

### `src/kintera_report/ch04/runs/uv_h2cp-h2o_300-off.out`

| Line | Output |
|---:|---|
| 1 | `h2o_300 use-h2-cp=off diag [5.0] T_after 303.7781 ln RH at that T -5.107e-15` |

### `src/kintera_report/ch04/runs/uv_h2cp-h2o_300-on.out`

| Line | Output |
|---:|---|
| 1 | `h2o_300 use-h2-cp=on diag [5.0] T_after 303.8059 ln RH at that T -6.994e-15` |

### `src/kintera_report/ch04/runs/uv_h2cp-nh3_120-off.out`

| Line | Output |
|---:|---|
| 1 | `nh3_120 use-h2-cp=off diag [3.0] T_after 121.8902 ln RH at that T +2.309e-14` |

### `src/kintera_report/ch04/runs/uv_h2cp-nh3_120-on.out`

| Line | Output |
|---:|---|
| 1 | `nh3_120 use-h2-cp=on diag [4.0] T_after 122.1113 ln RH at that T +3.730e-14` |

### `src/kintera_report/ch04/runs/uv_h2cp-nh3_160-off.out`

| Line | Output |
|---:|---|
| 1 | `nh3_160 use-h2-cp=off diag [4.0] T_after 160.2381 ln RH at that T +0.000e+00` |

### `src/kintera_report/ch04/runs/uv_h2cp-nh3_160-on.out`

| Line | Output |
|---:|---|
| 1 | `nh3_160 use-h2-cp=on diag [4.0] T_after 160.2647 ln RH at that T +2.220e-16` |

### `src/kintera_report/ch04/runs/uv_host_rh.out`

| Line | Output |
|---:|---|
| 1 | `[Warning] equilibrate_uv did not converge after 2 iterations.` |
| 2 | `[Warning] equilibrate_uv did not converge after 2 iterations.` |
| 3 | `[Warning] equilibrate_uv did not converge after 2 iterations.` |
| 4 | `[Warning] equilibrate_uv did not converge after 2 iterations.` |
| 5 | `[Warning] equilibrate_uv did not converge after 2 iterations.` |
| 6 | `(a) one vapour, kkt: cells 25, diag [3.0, 4.0], max ln RH +9.2e-07, max &#124;ln RH&#124; with condensate 9.2e-07, check passes` |
| 7 | `(a) one vapour, auto: cells 25, diag [5.0], max ln RH +2.5e-14, max &#124;ln RH&#124; with condensate 2.5e-14, check passes` |
| 8 | `(b) jupiter.yaml cold start, kkt, max-iter 30: cells 5, diag [6.0, 8.0, 9.0, 12.0, 14.0], max ln RH +4.3e-08, max &#124;ln RH&#124; with condensate 7.2e-08, check passes` |
| 9 | `(c) jupiter.yaml cold start, kkt, max-iter 2: cells 5, diag [-2002.0], max ln RH +1.4e+01, max &#124;ln RH&#124; with condensate 1.4e+01, check FAILS` |
| 10 | `(d) one vapour, use-h2-cp, Tref 0: cells 1, diag [3.0], max ln RH -1.8e-07, max &#124;ln RH&#124; with condensate 1.8e-07, check passes` |

## Plot regression and preserved obligations

Regenerating the partition figure reduced its y range to order 1e-6. The old Tref annotation at data y=0.45 made Agg PNG rendering fail (FT_Render_Glyph/raster overflow). The reproduction and implementation ownership were recorded on issue 101 before repair. The new regression renders the real figure and checks the annotation stays in the axes. It failed before the fix and passed afterward. The fix uses axes coordinates for annotation height; it does not change plotted values.

Strict guard coverage, 1000-step assertions, actual-source mutation evidence, six appendix exclusions and all original audit artifacts remain intact. Historical provenance and owner-routed failures are not waived. The chapter 4/5/13 owner must recheck chapters 4/5; the two designated reviewers must recheck chapter 14; no approval is claimed. The designated package-fix contact owns the separate examples issue/fix batch under the lead’s routing. the chapter 12 continuation has not been integrated here; chapter 13 GPU continuation remains with chapter 4/5/13 owner.

## Every changed ch4 data leaf (provenance excluded)

| JSON pointer | Old | New | New minus old |
|---|---:|---:|---:|
| `tp_coldstart/max_iter_60/max_ln_rh/6` | -1.6883253010885364e-07 | -1.6883252977578668e-07 | 3.3306696032710617e-16 |
| `uv_partition_tref/partition/diag/0` | 7.0 | 5.0 | -2.0 |
| `uv_partition_tref/partition/diag/1` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/2` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/3` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/4` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/5` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/6` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/7` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/8` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/9` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/10` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/11` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/12` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/13` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/14` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/15` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/16` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/17` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/18` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/19` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/20` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/22` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/23` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/diag/24` | -1.0 | 5.0 | 6.0 |
| `uv_partition_tref/partition/ln_rh/0` | -1.1102230246251565e-16 | 2.4424906541753144e-14 | 2.453592884421566e-14 |
| `uv_partition_tref/partition/ln_rh/1` | 0.5088372403147803 | 2.4868995751603197e-14 | -0.5088372403147554 |
| `uv_partition_tref/partition/ln_rh/2` | 0.49384279982520024 | 4.6629367034256464e-15 | -0.4938427998251956 |
| `uv_partition_tref/partition/ln_rh/3` | 0.4788770569048892 | 1.4210854715201903e-14 | -0.478877056904875 |
| `uv_partition_tref/partition/ln_rh/4` | 0.4639399363770907 | 1.6875389974302237e-14 | -0.4639399363770738 |
| `uv_partition_tref/partition/ln_rh/5` | 0.44903136332205035 | 1.5099033134902015e-14 | -0.44903136332203525 |
| `uv_partition_tref/partition/ln_rh/6` | 0.4341512630759389 | 1.4210854715201903e-14 | -0.43415126307592466 |
| `uv_partition_tref/partition/ln_rh/7` | 0.4192995612297541 | -5.5511151231257985e-15 | -0.41929956122975964 |
| `uv_partition_tref/partition/ln_rh/8` | 0.404476183628259 | 2.2204460492503128e-16 | -0.40447618362825877 |
| `uv_partition_tref/partition/ln_rh/9` | 0.3896810563689008 | -2.2093438190040858e-14 | -0.3896810563689229 |
| `uv_partition_tref/partition/ln_rh/10` | 0.37491410580073986 | 1.0214051826551388e-14 | -0.37491410580072965 |
| `uv_partition_tref/partition/ln_rh/11` | 0.3601752585233986 | 5.107025913275707e-15 | -0.3601752585233935 |
| `uv_partition_tref/partition/ln_rh/12` | 0.3454644413859987 | -4.884981308350701e-15 | -0.3454644413860036 |
| `uv_partition_tref/partition/ln_rh/13` | 0.33078158148611536 | 1.332267629550179e-14 | -0.33078158148610204 |
| `uv_partition_tref/partition/ln_rh/14` | 0.31612660616872396 | -9.880984919163942e-15 | -0.31612660616873384 |
| `uv_partition_tref/partition/ln_rh/15` | 0.3014994430251677 | 9.76996261670133e-15 | -0.3014994430251579 |
| `uv_partition_tref/partition/ln_rh/16` | 0.28690001989211805 | -2.220446049250313e-16 | -0.2869000198921183 |
| `uv_partition_tref/partition/ln_rh/17` | 0.2723282648505458 | -1.1102230246251565e-16 | -0.2723282648505459 |
| `uv_partition_tref/partition/ln_rh/18` | 0.25778410622469694 | 3.330669073875464e-15 | -0.2577841062246936 |
| `uv_partition_tref/partition/ln_rh/19` | 0.24326747258107345 | -1.521005543736476e-14 | -0.24326747258108866 |
| `uv_partition_tref/partition/ln_rh/20` | 0.22877829272741682 | -4.440892098500636e-15 | -0.22877829272742126 |
| `uv_partition_tref/partition/ln_rh/22` | 0.1998820108211397 | 1.5321077739827044e-14 | -0.1998820108211244 |
| `uv_partition_tref/partition/ln_rh/23` | 0.18547476758114528 | -1.3544720900427001e-14 | -0.18547476758115883 |
| `uv_partition_tref/partition/ln_rh/24` | 0.17109469575439207 | 9.76996261670133e-15 | -0.1710946957543823 |
| `uv_partition_tref/partition/T_after/0` | 304.4072980585243 | 304.40729805852396 | -3.410605131648481e-13 |
| `uv_partition_tref/partition/T_after/1` | 297.25 | 304.453921288398 | 7.203921288398021 |
| `uv_partition_tref/partition/T_after/2` | 297.5 | 304.5004175550696 | 7.000417555069589 |
| `uv_partition_tref/partition/T_after/3` | 297.75 | 304.54678737461325 | 6.7967873746132454 |
| `uv_partition_tref/partition/T_after/4` | 298.0 | 304.5930312604387 | 6.593031260438693 |
| `uv_partition_tref/partition/T_after/5` | 298.25 | 304.63914972330474 | 6.38914972330474 |
| `uv_partition_tref/partition/T_after/6` | 298.5 | 304.6851432713345 | 6.185143271334482 |
| `uv_partition_tref/partition/T_after/7` | 298.75 | 304.7310124100314 | 5.981012410031383 |
| `uv_partition_tref/partition/T_after/8` | 299.0 | 304.776757642293 | 5.776757642292978 |
| `uv_partition_tref/partition/T_after/9` | 299.25 | 304.822379468428 | 5.572379468427982 |
| `uv_partition_tref/partition/T_after/10` | 299.5 | 304.8678783861684 | 5.3678783861684 |
| `uv_partition_tref/partition/T_after/11` | 299.75 | 304.9132548906882 | 5.163254890688222 |
| `uv_partition_tref/partition/T_after/12` | 300.0 | 304.9585094746145 | 4.958509474614516 |
| `uv_partition_tref/partition/T_after/13` | 300.25 | 305.00364262804345 | 4.753642628043451 |
| `uv_partition_tref/partition/T_after/14` | 300.5 | 305.04865483855673 | 4.548654838556729 |
| `uv_partition_tref/partition/T_after/15` | 300.75 | 305.0935465912324 | 4.343546591232382 |
| `uv_partition_tref/partition/T_after/16` | 301.0 | 305.13831836866353 | 4.138318368663533 |
| `uv_partition_tref/partition/T_after/17` | 301.25 | 305.18297065096925 | 3.932970650969253 |
| `uv_partition_tref/partition/T_after/18` | 301.5 | 305.2275039158108 | 3.7275039158108143 |
| `uv_partition_tref/partition/T_after/19` | 301.75 | 305.2719186384058 | 3.5219186384057934 |
| `uv_partition_tref/partition/T_after/20` | 302.0 | 305.3162152915407 | 3.3162152915406864 |
| `uv_partition_tref/partition/T_after/22` | 302.5 | 305.40445626851573 | 2.9044562685157302 |
| `uv_partition_tref/partition/T_after/23` | 302.75 | 305.4484015259078 | 2.698401525907798 |
| `uv_partition_tref/partition/T_after/24` | 303.0 | 305.49223058097016 | 2.4922305809701584 |

## Six reviewed chapter 14 quote corrections

| ID | Previous chapter quote | New quote from committed output | Output line |
|---|---|---|---:|
| n | `(n) snapy's next VU->T at fixed ie (meshblock.cpp:825) = linear-model T: max rel err 4.44e-16 (tol 1e-12) PASS` | `(n) snapy's next VU->T at fixed ie (meshblock.cpp:825) = linear-model T: max rel err 2.22e-16 (tol 1e-12) PASS` | 23 |
| o | `(o) latent warming T' - T per cell [K]: 22.352 21.810 20.554 13.713 9.087 3.756 INFO` | `(o) latent warming T' - T per cell [K]: 28.163 27.660 26.127 18.686 11.822 4.714 INFO` | 24 |
| p | `(p) max relative humidity per cell at (T', p') after the adjustment: 1.000000 1.000001 1.000000 1.000000 1.000000 1.000000 INFO` | `(p) max relative humidity per cell at (T', p') after the adjustment: 1.000000 1.000000 1.000000 1.000000 1.000000 1.000000 INFO` | 25 |
| k0 | `(k0) diag per cell at the default max_iter 10 (negative = failed, D4 filed): -2010 -2010 8 7 6 4 INFO` | `(k0) diag per cell at the default max_iter 100 (negative = failed): 11 9 9 7 5 4 INFO` | 19 |
| t | `(t) cloud concentrations from TPX->V against rho_i/mu_i: max rel diff 4.44e-16 (filed as D16; the driver's tendencies start from these) INFO` | `(t) cloud concentrations from TPX->V against rho_i/mu_i: max rel diff 6.66e-16 (filed as D16; the driver's tendencies start from these) INFO` | 29 |
| v | `(v) ratio of the volumetric heat capacity the drivers pass (TV->cp) to the C_V of the fixed-U Jacobian: 1.3845 1.3845 1.3846 1.3869 1.3908 1.3961 EXPECTED-FAIL (S14-1)` | `(v) ratio of the volumetric heat capacity the drivers pass (TV->cp) to the C_V of the fixed-U Jacobian: 1.3853 1.3853 1.3854 1.3880 1.3921 1.3968 EXPECTED-FAIL (S14-1)` | 31 |

## Wording ratchet regression

The complete intermediate audit at `77d033ea34ed5ef76a677c35dc8bf072d4f22fb5` exposed a new chapter 4 history count: “the default is now 100” in `_conditions.qmd`. The reproduction and explicit ownership were recorded on issue 101 before correction (comment 6381112721). Removing “now” leaves the value 100 and all scientific assertions unchanged. The existing `python tools/ratchet_gate.py counts -v` changes chapter 4 history from 1 to 0; other historical provenance/ratchet findings remain red. A new complete fresh-clone run is required at the corrected head; the intermediate run is preserved separately.
