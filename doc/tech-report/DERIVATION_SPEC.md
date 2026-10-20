# Derivation spec for the kintera tech report

Code pin: kintera 0d9f67f (v2.6.5). Report text judged: tech-report c5791ee9 (`doc/tech-report/book/chapters/`).
Audience of this spec: the authors (human or bot) who write the Derivation layers of chapters 2-6 and 9.
Audience of the report: a first-year PhD student who knows undergraduate thermodynamics and linear algebra.

## How to use an entry

Every entry has six parts.

1. **Question**: what the derivation answers, in plain words. Open the section with it.
2. **Start**: definitions and assumptions, each one a code fact (file:line at 0d9f67f) or textbook physics.
   State them before the first equation; do not introduce assumptions later.
3. **End**: the formula the code evaluates, with file:line. The derivation must arrive at this formula, in the
   code's variables and sign conventions. Where the derivation and the code differ, say so and point to the
   defect entry; never bend the derivation to match a defect.
4. **Steps**: the intermediate results a reader must see. Show each one as a displayed equation with one
   sentence of reasoning. A step may be merged with its neighbour only if the merge is a single substitution.
5. **Check**: a short numeric test against the built package that confirms the end result. The scripts live
   in `derivation-checks/` next to this file; run one from a scratch directory
   (`export KINTERA_WT=<build tree>; cd $(mktemp -d); python <this dir>/derivation-checks/<script>.py`) and
   quote its `.out` line in the section's Tests layer with the tolerance.
   A derivation without a passing check is not done.
6. **Home and status**: the section file that should hold the derivation and what c5791ee9 already has:
   PRESENT (all steps a reader needs are written; at most a remark is missing), PARTIAL (named steps are
   missing), MISSING (no derivation).

**Fix batch.** Entries tagged `[FIX: ...]` describe code that changes in the open fix batch (D64, K6, D8,
D4, D6, K4, D12, D16, K9; see issue [#54](https://github.com/UCzhangxi/kintera/issues/54) of UCzhangxi/kintera).
Write those derivations for the corrected code: derive the physically correct result, cite the fixed lines
once the batch lands, and keep the 0d9f67f behaviour only as a Limits note. Rerun the entry's check after the
batch lands; some checks are expected to flip from EXPECTED-FAIL to PASS.

## Conventions every chapter must share

- `stoich[i][r]` is positive for products and negative for reactants (`src/thermo/thermo_y.cpp:109-121`);
  the equilibrium solvers work with `nu = -stoich` (reactants positive), e.g. `src/thermo/equilibrate_tp.h:189`.
  An extent vector `xi` changes amounts by `stoich @ xi`. State this once, in the overview chapter.
- Gas constant `R = 8.31446` J/(mol K) (`src/constants.h:6`). Numeric oracles must use the same value; a
  CODATA value moves temperatures by about 1e-5 K.
- Species energies are linear in T with a constant offset: after `reset`, `u_n(T) = R (u0_n' + cv_n T)` with
  `u0_n' = u0_n - cv_n Tref` (`src/thermo/thermo_y.cpp:63-67`, `src/thermo/eval_uhs.cpp:288`), unless NASA-9
  or the H2 heat-capacity option replaces them (`src/thermo/eval_uhs.cpp:289-299`).
- Gases: `h = u + R T` (with the compressibility factor `z`, `h = u + z R T`); condensates: `h = u`, no
  pressure dependence (`src/thermo/eval_uhs.cpp:477-486`).
- Concentrations are mol/m^3; mole fractions `x` include condensates; `x_g` is the sum over gases only.

## Summary table

| ID | Derivation | Home (section file) | Status | Fix batch | Check script |
|---|---|---|---|---|---|
| O-1 | State variables and what each solver holds fixed | new overview chapter | MISSING | - | (cites C4-d, C3-h, C6-g checks) |
| O-2 | One saturation function and one energy model shared by all modules | new overview chapter | MISSING | - | check_ch3_species_functions, check_ch6_evaporation |
| C2-a | NASA-9 cp integrated to h and s | 02/_nasa9 | PRESENT | (feeds K6) | check_ch5_equilibrium (3c), check_ch2_nasa9 |
| C2-b | Ideal saturation curve from Clausius-Clapeyron, and its T-derivative | 02/_svp | PARTIAL | - | check_ch2_svp |
| C2-c | Hand-written backward pass of ln K(T) | 02/_svp-autograd | PRESENT | - | check_ch2_svp_autograd |
| C3-a | Reference state: energy and entropy offsets, latent heat | 03/_reference-state | PARTIAL | D12 | check_ch3_card_latent |
| C3-b | Species and mixture cv, cp, u, h, s | 03/_species-functions | PRESENT | - | check_ch3_species_functions |
| C3-c | Equation of state with condensates (TPX->V) | 03/_eos | PRESENT | D16 | check_ch3_species_functions |
| C3-d | ThermoY conversions and the VU->T Newton step | 03/_thermo-y | PRESENT | D12 | check_ch3_species_functions (1b) + proposed round trip |
| C3-e | Condensate entropy from zero reaction Gibbs energy | 03/_species-functions | PRESENT | D64, K6 | check_ch3_gibbs |
| C3-f | PXS->T: slope of entropy per volume | 03/_thermo-x | PRESENT | D8 | check_ch3_adiabat |
| C3-g | Condensate card consistent with its saturation curve | 03/_reference-state | MISSING | (K6 related) | check_ch3_card_latent |
| C3-h | Moist adiabat: effective heat capacity, reversible and rain-out steps | 03/_adiabat | PARTIAL | (K5 note) | check_ch3_adiabat |
| C3-i | Relative humidity per reaction | 03/_relative-humidity | PRESENT | - | check_ch3_species_functions |
| C3-j | Dry limit of the adiabat: Poisson's law | 03/_adiabat | MISSING | - | check_ch3_adiabat |
| C4-a | Saturation conditions as a constrained Gibbs minimum | 04/_conditions | PARTIAL | - | check_ch4_tp |
| C4-b | K in pressure and concentration units; d ln K'/dT | 04/_equilibrate-uv | PARTIAL | - | check_ch2_svp, check_ch4_tp |
| C4-c | TP Newton system with the gas-sum term | 04/_equilibrate-tp | PRESENT | D4 | check_ch4_tp |
| C4-d | UV Newton system with latent-heat coupling; T at fixed U | 04/_equilibrate-uv | PRESENT | D12 | check_ch4_uv |
| C4-e | Partition method: one scalar equation in T | 04/_equilibrate-uv | PARTIAL | D6, K4 | check_ch4_uv |
| C4-f | Active-set least squares with non-negative amounts | 04/_active-set | PARTIAL | - | check_ch4_tp (indirect) |
| C5-a | ln K from Gibbs energies | 05/_log-k | PRESENT | - | check_ch5_equilibrium |
| C5-b | Activity conditions; element conservation by construction | 05/_conditions | PRESENT | - | check_ch5_equilibrium |
| C5-c | Newton in reaction extents: Jacobian, bounds, line search, diagnostics | 05/_newton, 05/_diagnostics | PRESENT | - | check_ch5_equilibrium |
| C6-a | Mass action and species tendency | 06/_mass-action | PRESENT | - | check_ch6_rates |
| C6-b | Arrhenius law and the unit factor | 06/_arrhenius | PARTIAL | - | check_ch6_rates |
| C6-c | Fall-off from the Lindemann mechanism; pressure switch | 06/_falloff | PARTIAL | - | check_ch6_rates |
| C6-d | Reverse rates from K_c (detailed balance) and their T-derivative | 06/_mass-action | MISSING | - | check_ch6_rates |
| C6-e | Evaporation rate and its fixed point at saturation | 06/_evaporation | PARTIAL | - | check_ch6_evaporation |
| C6-f | Kessler form in mole fractions | 06/_kessler | PRESENT | - | existing test (see entry) |
| C6-g | Jacobian with temperature feedback at fixed internal energy | 06/_jacobian | PARTIAL | rerun after batch | check_ch6_jacobian |
| C6-h | Linearly implicit step and the two-stage Rosenbrock variant | 06/_implicit | PARTIAL | - | check_ch6_implicit |
| C9-a | Eddy diffusion in concentration and mixing-ratio forms | 09/_transport | PRESENT | - | check_ch9_atm2d |
| C9-b | Molecular diffusion and the diffusive-equilibrium profile | 09/_molecular | PARTIAL | - | check_ch9_atm2d |
| C9-c | Source linearisation and stoichiometric mapping | 09/_sources | PRESENT | - | check_ch9_sources |
| C9-d | Implicit assembly and Rosenbrock-2 order | 09/_assembly, 09/_rosenbrock | PARTIAL | - | check_ch9_atm2d, check_ch9_ros2_stability, check_ch9_ros2_error |
| C9-e | Newton iteration and the steady-state limit | 09/_newton | PRESENT | - | check_ch9_newton |
| C9-f | Atomic-budget projection | 09/_conservation | PRESENT | K9 | check_ch9_atm2d, check_ch9_budget_exact, check_ch9_budget_below1 |

Counts: 38 entries; PRESENT 19, PARTIAL 14, MISSING 5. Fix-batch tagged: 9 entries (C3-a, C3-c, C3-d, C3-e,
C3-f, C4-c, C4-d, C4-e, C9-f) plus C6-g, whose check must be rerun because it calls the energy function the batch
edits.

## Check scripts and results at 0d9f67f

All scripts are in `derivation-checks/`, print the package version first, and run from a scratch directory (they write
nothing there). Each line of the `.out` files ends in PASS, FAIL, EXPECTED-FAIL (a documented defect,
expected to pass after the fix batch) or INFO.

| Script | Entries | PASS | FAIL | EXPECTED-FAIL | Notes |
|---|---|---|---|---|---|
| check_ch2_svp.py | C2-b, C4-b | 15 | 0 | 0 | prints beta R T3 per branch; lines 8-15 read kintera at T3 -+ 1e-6 K and 3e-6 K |
| check_ch2_nasa9.py | C2-a | 3 | 0 | 0 | b1, b2 against CODATA; prints the jumps at Tmid (5 of 293 entries > 1 K in h/R) |
| check_ch2_svp_autograd.py | C2-c | 8 | 0 | 0 | through kintera.Evaporation and forward_with_rate_constants |
| check_ch3_species_functions.py | C3-b, C3-c, C3-d, C3-i | 8 | 0 | 0 | 1 INFO: default cap leaves 6 of 9 cold cells unconverged (D4) |
| check_ch3_card_latent.py | C3-a, C3-g | 3 | 0 | 0 | 8 INFO: test-card latent heat ratios |
| check_ch3_gibbs.py | C3-e | 1 | 0 | 0 | four states, RH 0.024 to 2.6 |
| check_ch3_adiabat.py | C3-f, C3-h, C3-j | 4 | 0 | 1 | D8 |
| check_ch4_tp.py | C4-a, C4-c | all | 0 | 1 | D4 |
| check_ch4_uv.py | C4-d, C4-e | all | 0 | 1 | D6 |
| check_ch5_equilibrium.py | C2-a, C5-a, C5-b, C5-c | all | 0 | 0 | |
| check_ch6_rates.py | C6-a..C6-d | all | 0 | 1 | reverse-rate T-derivative (C6-d) |
| check_ch6_evaporation.py | C6-e, O-2 | 4 | 0 | 0 | |
| check_ch6_jacobian.py | C6-g | 1 | 0 | 0 | rerun after the batch |
| check_ch6_implicit.py | C6-h | all | 0 | 0 | |
| check_ch9_sources.py | C9-c | 8 | 0 | 0 | FD Jacobians at 1e-7 |
| check_ch9_newton.py | C9-e | 6 | 0 | 0 | residual ratio, damping, large-dt limit |
| check_ch9_ros2_stability.py | C9-d | 7 | 0 | 0 | R(z), L-stability, both roots |
| check_ch9_ros2_error.py | C9-d | 8 | 0 | 0 | embedded error estimate |
| check_ch9_budget_exact.py | C9-f | 9 | 0 | 0 | exactness condition, element order |
| check_ch9_budget_below1.py | C9-f | 4 | 0 | 2 | K9 |
| check_ch9_atm2d.py | C9-a, C9-b, C9-d, C9-f | all | 0 | 0 | 1 INFO: clamped hog total |

Not yet covered by a script: C3-d round trip, C4-f direct KKT test. The overview entries O-1 and O-2 cite lines of
the scripts above.

---

## Proposed overview chapter: "The parcel model in one place"

Why it is needed: chapters 3-6 each derive one solver, but no chapter says which quantities a solver holds
fixed, which functions the solvers share, and why sharing them makes the library self-consistent. A reader
meets the same saturation curve in four places and the same species energies in three, with no statement
that they must be (and are) the same objects. A short chapter (4-6 pages) between the overview and chapter 2,
or as the opening section of chapter 3, closes that gap. It holds two entries.

### O-1 State variables and what each solver holds fixed

- **Question.** A parcel is a list of amounts of gases and condensates plus two thermodynamic variables.
  Which two does each solver hold fixed, and which conservation law does each step obey?
- **Start.** ThermoX works in (T, p, mole fractions), ThermoY in (density, mass fractions, internal energy)
  (`src/thermo/thermo.hpp`, classes `ThermoXImpl`, `ThermoYImpl`); extents change amounts by `stoich @ xi`
  (`src/thermo/equilibrate_tp.h:248-252`); every reaction column conserves elements.
- **End.** A table with one row per entry point: `ThermoX.forward` holds T, p and elements; `ThermoY.forward`
  holds U, V and elements (`src/thermo/equilibrate_uv.h:558-586`); `extrapolate_dlnp` holds molar entropy
  along a pressure step, or the rain-out entropy budget (`src/thermo/extrapolate_ad.cpp:87`, `:121-136`); the
  kinetics Jacobian holds U, V when temperature evolves (`src/kinetics/kinetics.cpp:372-376`); EquilibriumTP
  holds T, p, elements (`src/equilibrium/phase_equilibrate_tp.h:113-119`).
- **Steps.** (1) Counting: species amounts plus two state variables, minus one condition per active
  reaction, leave the free variables. (2) Elements are conserved by any step `stoich @ xi` because each
  column is balanced (`E @ stoich = 0`). (3) Which thermodynamic potential each solver minimises or which
  conserved quantity it holds: G at fixed T, p (C4-a); U at fixed V is held, so T is an output (C4-d); S
  along the adiabat (C3-h). (4) Consequence for coupling: a dynamical core that conserves U and V must call
  the UV path, not the TP path.
- **Check.** Collect, do not duplicate: the element and energy conservation lines of `check_ch4_uv.out`
  and `check_ch4_tp.out`, and the entropy line of `check_ch3_adiabat.out`.
- **Home and status.** New overview chapter. MISSING.

### O-2 One saturation function and one energy model shared by all modules

- **Question.** Why does the equilibrium found by the phase solver coincide with the fixed point of the
  evaporation kinetics, and why does the latent heat released in a kinetic step equal the one the UV solver
  uses?
- **Start.** One saturation function `LogSVPFunc` (`src/thermo/log_svp.cpp`) is called by the phase solvers
  (`src/thermo/equilibrate_tp.h:114`, `src/thermo/equilibrate_uv.h:388`), by the condensate entropy
  (`src/thermo/eval_uhs.cpp:424-425`), by the adiabat (`src/thermo/extrapolate_ad.cpp:25-27`) and by
  evaporation (`src/kinetics/evaporation.cpp:260-261`). One energy function `eval_intEng_R`
  (`src/thermo/eval_uhs.cpp:266-301`) feeds ThermoY and the kinetics temperature feedback
  (`src/kinetics/kinetics.cpp:373`).
- **End.** Two statements with their code lines: (a) the evaporation deficit is `K - c_v = K (1 - RH)` for a
  single-vapour reaction (`src/kinetics/evaporation.cpp:267-278`, `src/thermo/relative_humidity.cpp:25-33`),
  so the kinetic rate vanishes exactly where the phase solver puts the parcel (RH = 1); (b) the latent
  energy of reaction r, `L_r = -sum_i stoich[i][r] u_i`, enters both the UV weight
  (`src/thermo/equilibrate_uv.h:453-455`) and the kinetic Jacobian (`src/kinetics/kinetics.cpp:373-375`).
- **Steps.** (1) Write RH and the evaporation deficit in the same variables. (2) Show that RH = 1 is the
  phase-equilibrium condition of C4-a. (3) Show that both the UV solver and the kinetics differentiate
  `U = sum c_i u_i(T)` at fixed U, giving `dT = -sum u_i dc_i / C_V` (C4-d step 1, C6-g step 3). (4) State
  what breaks if the energy model of one module differs from the other's (this is the D12 defect: the UV
  kernel receives constant offsets while ThermoY may use the H2 heat capacity).
- **Check.** `check_ch3_species_functions.out` (RH = 1 at a cloudy equilibrium) together with
  `check_ch6_evaporation.out` (rate zero at c_v = K).
- **Home and status.** New overview chapter. MISSING.

---

## Chapter 2: species data

### C2-a NASA-9 cp integrated to enthalpy and entropy

- **Question.** Given seven heat-capacity coefficients and two constants, how are h and s obtained, and why
  does the code evaluate h/R while the polynomial tables are usually written as h/(RT)?
- **Start.** `cp/R = a0 T^-2 + a1 T^-1 + a2 + a3 T + a4 T^2 + a5 T^3 + a6 T^4`
  (`src/thermo/eval_uhs.cpp:24-29`, `src/thermo/nasa9.hpp:11-18`); `b1, b2` stored at indices 7, 8
  (`src/thermo/nasa9.hpp:53-54`); two ranges joined at Tmid (`src/thermo/nasa9.hpp:39-43`).
- **End.** `h/R = -a0/T + a1 ln T + a2 T + a3 T^2/2 + a4 T^3/3 + a5 T^4/4 + a6 T^5/5 + b1`
  (`src/thermo/eval_uhs.cpp:30-35`); `s/R = -a0/(2T^2) - a1/T + a2 ln T + a3 T + a4 T^2/2 + a5 T^3/3 +
  a6 T^4/4 + b2`, `g/RT = h/RT - s/R` (`src/thermo/nasa9.hpp:56-62`).
- **Steps.** (1) `h = int cp dT` term by term; the T^-1 term gives ln T and the T^-2 term gives -1/T.
  (2) `s = int cp dT / T`; now the constant gives ln T, the T^-1 term -1/T, the T^-2 term -1/(2T^2).
  (3) b1, b2 are the integration constants fixed by tabulated h and s at a reference temperature.
  (4) Continuity at Tmid is a property of the data, not enforced by the code. (5) `g/RT = h/RT - s/R`.
- **Check.** Only `nasa9_gibbs_rt` is bound in Python, so h and s are tested together through the
  van 't Hoff identity `d(-Delta g/RT)/dT = Delta h/(R T^2)`, with h from the step-1 integral of the
  coefficients in the package's `data/nasa9.dat` (whose parse reproduces the library's g/RT exactly):
  `check_ch5_equilibrium.py` line 3c, relative error 4.7e-10 (tol 1e-6), PASS.
- **Home and status.** `02-species-data/_nasa9.qmd:45-62`. PRESENT. Add one remark that the code evaluates
  h/R (`src/thermo/eval_uhs.cpp:30-35`), and an executable check of the s line (the section says it has none).

### C2-b Ideal saturation curve from Clausius-Clapeyron, and its T-derivative

- **Question.** What do the parameters beta and gamma of the "ideal" saturation formula mean physically, and
  what is `d ln p_sat / dT`?
- **Start.** Textbook Clausius-Clapeyron for an ideal vapour over a condensate of negligible volume,
  `d ln p / dT = l / (R T^2)`, with a latent heat linear in T, `l(T) = l(0) - dcp T` (constant difference of
  heat capacities). Parameters T3, P3, beta, gamma (and betas, gammas for the solid branch) are read per
  reaction (`src/thermo/nucleation.cpp:43-107`, `src/thermo/svp_eval.h:16-19`).
- **End.** `ln p_sat = beta (1 - 1/t) - gamma ln t + ln P3`, `t = T/T3` (`src/vapors/vapor_functions.h:12-15`,
  `src/thermo/svp_eval.h:36-40`); `d ln p_sat/dT = (beta/t^2 - gamma/t)/T3` (`src/vapors/vapor_functions.h:17-20`,
  `src/thermo/svp_eval.h:51-55`). Antoine form and derivative: `src/vapors/vapor_functions.h:22-30`.
- **Steps.** (1) Integrate Clausius-Clapeyron from (T3, P3) with the linear l(T). (2) Collect terms:
  `beta = l(0) / (R T3)` and `gamma = dcp / R`. (3) State the reading of beta explicitly: `beta R T3` is the
  enthalpy latent heat extrapolated to T = 0, and `l(T) = R (beta T3 - gamma T)`; C3-g needs this.
  (4) Differentiate in t and divide by T3. (5) Two branches (liquid above T3, solid below) make ln p_sat
  continuous at T3 but give a kink in its slope.
- **Check.** `check_ch2_svp.py`: kintera's ln p_sat against an independent copy, 1.8e-15 (tol 1e-12);
  analytic derivative against a central difference, at most 7.3e-11 (tol 1e-7); `R T^2 d ln p/dT =
  R (beta T3 - gamma T)` on both branches, 4.4e-16 (tol 1e-12); all PASS. It also prints `beta R T3`:
  56.4 kJ/mol (H2O liquid branch), 52.2 (ice), 32.6 (NH3 liquid), 33.5 (NH3 solid).
- **Home and status.** `02-species-data/_svp.qmd:44-78`. PARTIAL: steps 2-3 (the identification of beta
  with l(0) and of gamma with the heat-capacity difference) are missing.

### C2-c Hand-written backward pass of ln K(T)

- **Question.** What does the backward pass of the saturation function return, and why are second
  derivatives through it not available?
- **Start.** `LogSVPFunc::forward` saves T and the formula parameters; `LogSVPFunc::backward` multiplies the
  incoming gradient by a hand-written derivative (`src/thermo/log_svp.cpp`).
- **End.** `dL/dT = g_bar * d ln K/dT` with the derivative from `eval_logsvp_ddT` (`src/thermo/svp_eval.h:48-60`).
- **Steps.** (1) Chain rule per reaction column. (2) T is expanded to one column per reaction so each
  gradient lands on its own entry. (3) The derivative is computed outside autograd, so the backward pass is
  itself a constant for a second differentiation.
- **Check.** `check_ch2_svp_autograd.py` reaches `LogSVPFunc::apply` through its one caller, `kintera.Evaporation`:
  the first derivative against the closed form (1.3e-15) and `gradcheck` (step 1); the per-column gradient,
  `rc_ddT` of `forward_with_rate_constants` per reaction ([32.978, 0.000] at 78 K) and the summed gradient for an
  unexpanded temperature (step 2); the second derivative without the d2 ln K/dT2 term, and `gradgradcheck` false (step 3).
  8 PASS.
- **Home and status.** `02-species-data/_svp-autograd.qmd:35-46`. PRESENT.

(Molar mass and unit conversion, `02-species-data/_molar-mass.qmd` and `_units.qmd`, are bookkeeping, not
derivations; they are PRESENT and not listed as entries.)

---

## Chapter 3: thermodynamics

### C3-a Reference state: energy and entropy offsets, and the latent heat

- **Question.** The input card gives u0 and s0 at (Tref, Pref). How do these become constants at T = 0
  (energy) and at T = 1 K, p = 1 Pa (entropy), and what latent heat does the card imply?
- **Start.** Defaults cv_R 5/2, u0_R 0, s0_R 0 (`src/species.cpp:172-182`); the reset shifts
  `u0 -= cv Tref` and `s0 -= (cv+1) ln max(Tref,1) - ln max(Pref,1)` for gases, and sets condensate s0 to 0
  (`src/thermo/thermo_y.cpp:63-82`; ThermoX does the same in its reset).
- **End.** `u/R = u0' + cv T` (`src/thermo/eval_uhs.cpp:288`); `s_gas/R = s0' + (cv+1) ln T - ln p - ln(x_n/x_g)`
  (`src/thermo/eval_uhs.cpp:416-419`); energy latent heat of reaction r, `L_r = -sum_n stoich[n][r] u_n`,
  with the sign check in `ThermoOptionsImpl::from_yaml` (`src/thermo/thermo_options.cpp`).
- **Steps.** (1) Integrate constant cv from Tref to T and collect the constant. (2) Same for the gas
  entropy, with p in Pa. (3) Energy latent heat `L(T) = L(Tref) - (T - Tref) sum_n stoich[n][r] cv_n`
  (Kirchhoff's law at constant volume). (4) Enthalpy latent heat per mole of vapour
  `l = L + R T (moles of gas removed)`, the quantity that appears in Clausius-Clapeyron (C2-b, C3-g).
  (5) Why the condensate s0 is discarded: the condensate entropy is solved from equilibrium (C3-e).
- **Check.** `check_ch3_card_latent.py`: latent heat from kintera's own `TV->H` (one mole moved from vapour
  to condensate) against the card algebra of step 4, at most 5.5e-13 (tol 1e-10), PASS for H2O and NH3.
- **Home and status.** `03-thermodynamics/_reference-state.qmd:43-86`. PARTIAL: step 4 is missing; the fact
  that NASA-9 and H2 energies are referenced to a fixed 300 K (`src/thermo/eval_uhs.cpp:289-299`) is only in Limits.
- **[FIX: D12]** ThermoY passes the shifted constant `u0`, `cv` to the UV kernel even when the H2 heat
  capacity is on (`src/thermo/thermo_y.cpp:347-356`). Derive the offsets for one energy model shared by
  ThermoY and its kernel.

### C3-b Species and mixture cv, cp, u, h, s

- **Question.** Why is `cp = cv + R` for gases only, `h = u + R T` for gases and `h = u` for condensates,
  why condensates carry no pressure term, and why `C_p = dH/dT` at fixed concentrations?
- **Start.** cv (`src/thermo/eval_uhs.cpp:153-188`); cp adds 1 for vapours only (`:208-211`); u (`:285-301`);
  h (`:477-486`); gas entropy with the mixing term and the floor 1e-300 on x/x_g (`:416-419`).
- **End.** `C_p = R sum_n c_n cp_n`, `H = R sum_n c_n h_n`, `S = R sum_n c_n s_n` (`ThermoXImpl` methods
  `_cp_vol`, `_enthalpy_vol`, `_entropy_vol`, `src/thermo/thermo.hpp`); U and C_V likewise in ThermoY.
- **Steps.** (1) Ideal gas: u(T) only, `h = u + R T`, `cp = cv + R`. (2) Incompressible condensate of zero
  volume: `h = u`, `cp = cv`. (3) `dH/dT` at fixed c equals C_p. (4) `C_p - C_V = R sum_gas c_n`. (5) Gas
  entropy from `ds = cp dT/T - R dp_n/p_n` with `p_n = (x_n/x_g) p`, giving the mixing term `-R ln(x_n/x_g)`
  computed over gases only.
- **Check.** `check_ch3_species_functions.py`: FD of `TV->H` against `TV->cp`, 2.7e-11 (tol 1e-8);
  `C_p - C_V` (ThermoY `VT->cv`) against `R sum_gas c`, 3.4e-16 (tol 1e-12); PASS.
- **Home and status.** `03-thermodynamics/_species-functions.qmd:46-118`. PRESENT.

### C3-c Equation of state with condensates (TPX->V)

- **Question.** Why do only gas concentrations enter the pressure, and how do condensate concentrations
  follow from mole fractions?
- **Start.** `p = R T sum_gas z_n c_n` (`ThermoYImpl::_temp_to_pres`, `src/thermo/thermo_y.cpp`); gas
  concentrations from mole fractions with a Newton loop when `z != 1` (`src/thermo/thermo_x.cpp:320-368`).
- **End.** `c_n = x_n p / (R T x_g)` for gases; condensates at 0d9f67f: `c_m = c_0 x_m / x_0`
  (`src/thermo/thermo_x.cpp:365-367`).
- **Steps.** (1) Dalton's law over gases. (2) Total concentration `c_tot = p / (R T x_g)` (condensates occupy
  no volume). (3) `c_m = x_m c_tot` for every species. (4) Newton for the non-ideal factor z(c).
- **Check.** `check_ch3_species_functions.py`, cloud present: `R T sum_gas c = p` exactly (0) and
  `c_m/c_n = x_m/x_n` to 2.2e-16 (tol 1e-13), PASS. This state has nonzero x_0, so it does not exercise D16.
- **Home and status.** `03-thermodynamics/_eos.qmd:39-94`. PRESENT.
- **[FIX: D16]** Write the end result as `c_m = x_m p / (R T x_g)`; the pin divides by the first species'
  mole fraction, which fails when that is zero.

### C3-d ThermoY conversions and the VU->T Newton step

- **Question.** How are mass fractions turned into mole fractions with the dry species implicit, and why is
  the starting guess of the energy inversion exact for constant cv?
- **Start.** `rho_0 = rho (1 - sum y)`, `rho_n = rho y_n` (`_yfrac_to_ivol`, `src/thermo/thermo_y.cpp`);
  per-mass offsets `u0 = uref_R R / mu` (`src/thermo/thermo_y.cpp:101`).
- **End.** `x_n = (y_n mu_0/mu_n) / (1 + sum_k y_k (mu_0/mu_k - 1))` (`_yfrac_to_xfrac`); Newton
  `T <- T + (U - sum c u)/(sum c cv)` from the start `T = (U - sum rho_n u0_n)/sum rho_n cv_n`
  (`_intEng_to_temp`, `src/thermo/thermo_y.cpp`).
- **Steps.** (1) Partial densities. (2) Mole-fraction algebra with the dry term pulled out. (3) U is linear
  in T when cv is constant, so the start is the root. (4) The Newton slope is `dU/dT = C_V`.
- **Check.** The cv used in step 4 is tested in `check_ch3_species_functions.py` line 1b (3.4e-16, PASS).
  Proposed and not yet run: a `VT->U` then `VU->T` round trip, with and without the H2 heat-capacity
  option (after D12 both must return T to 1e-10).
- **Home and status.** `03-thermodynamics/_thermo-y.qmd:42-98`. PRESENT.
- **[FIX: D12]** After the batch, state that the UV kernel receives the same T-dependent energy as ThermoY.

### C3-e Condensate entropy from zero reaction Gibbs energy

- **Question.** Why is the condensate entropy not input data, how does it follow from saturation, and what
  is the mixture entropy?
- **Start.** Gas entropy split into a part without the pressure and mixing terms (`src/thermo/eval_uhs.cpp:433-434`);
  `ln K` from `LogSVPFunc` (`:424-425`); reaction enthalpy `h @ stoich` (`:429`).
- **End.** At 0d9f67f: `b_r = sum_n stoich[n][r] h_n/(R T) - sum_gas stoich[n][r] s~_n/R - ln K_r`
  (`src/thermo/eval_uhs.cpp:438-439`), condensate entropies `= pinv(S_c^T) b` (`:443-455`).
- **Steps.** (1) At saturation the reaction Gibbs energy is zero: `sum_n stoich[n][r] (h_n - T s_n) = 0`.
  (2) For the gases, the pressure terms sum to `ln K_r` exactly on the saturation curve (p in Pa).
  (3) Move the condensate terms to one side: one linear equation per reaction. (4) When each condensate is
  the product of exactly one reaction, each equation gives one condensate entropy directly. (5) Consequence:
  `s_c = s_v - l/T` on the curve, so the entropy of condensation equals latent heat over temperature.
  (6) Mixture `S = sum_n c_n s_n` including the gas mixing terms.
- **Check.** `check_ch3_gibbs.py`: at fixed T, p, move a small amount from H2O vapour to H2O(l) and
  difference `G = H - T S` (`TV->H`, `TPV->S`); step 1-3 predict `dG/dxi = -R T ln RH` at any state, sub- or
  supersaturated. Four states with RH from 0.024 to 2.6: worst |diff|/(R T) 3.9e-8 (tol 1e-6), PASS.
- **Home and status.** `03-thermodynamics/_species-functions.qmd:120-166`. PRESENT; the executable check
  the section admits is missing (`:164-166`) must be added.
- **[FIX: D64, K6]** The pin solves all condensates at once with a pseudo-inverse, which gives zero entropy
  to a condensate without its own reaction and a least-squares value when equations outnumber condensates
  (D64); its enthalpy may come from NASA-9 or the H2 heat capacity while the vapour entropy keeps constant
  cp (K6). Write step 4 for the corrected code: each condensate from its own reaction, with h and s from the
  same heat-capacity model.

### C3-f PXS->T: slope of entropy per volume

- **Question.** What is `dS/dT` at fixed p and x when S is per volume, and when does the temperature update
  converge?
- **Start.** S per volume; at fixed p, x every concentration scales as 1/T (C3-c).
- **End.** At 0d9f67f: `T <- T (1 + (S_given - S)/C_p)` followed by a phase equilibration
  (`src/thermo/thermo_x.cpp:296-297`).
- **Steps.** (1) `dS/dT|_{p,x} = (C_p - S)/T` (the 1/T scaling of c adds `-S/T`). (2) The pin's update is a
  fixed-point map with derivative `s/cp` at the root (molar entropy over molar heat capacity), which depends
  on the arbitrary entropy offset. (3) The correct Newton update is `T <- T + T (S_given - S)/(C_p - S)`, or
  equivalently inversion of the molar entropy as the adiabat does (C3-h).
- **Check.** `check_ch3_adiabat.py` line 4c: S computed at 600 K, then `PXS->T` from the 300 K start returns
  594.16 K after the 10 allowed passes (|dT| = 5.8 K, tol 1e-6): EXPECTED-FAIL at the pin, PASS after D8.
- **Home and status.** `03-thermodynamics/_thermo-x.qmd:68-107`. PRESENT.
- **[FIX: D8]** Write the end result for the corrected slope `(C_p - S)/T`.

### C3-g Condensate card consistent with its saturation curve

- **Question.** A condensate carries its own u0 and cv, and its reaction carries a saturation formula. Both
  imply a latent heat. What must the card satisfy so that the two agree at every temperature, and what goes
  wrong otherwise?
- **Start.** Energies `u_n(T) = R (u0_n' + cv_n T)`, gas `h = u + R T`, condensate `h = u`
  (`src/thermo/eval_uhs.cpp:288`, `:477-486`); ideal saturation formula and its derivative
  (`src/vapors/vapor_functions.h:12-20`); C2-b step 3.
- **End.** No code line evaluates this; the result is a constraint on input cards. For a reaction
  `vapour -> condensate` with the ideal formula: `u0_v' - u0_c' = beta T3` and `cv_c = cv_v + 1 + gamma`
  (energies referenced to T = 0, i.e. after the reset of C3-a).
- **Steps.** (1) From the species functions, `l_card(T) = h_v - h_c = R [(u0_v' - u0_c') + (cv_v + 1 - cv_c) T]`,
  linear in T. (2) From C2-b, `l_svp(T) = R (beta T3 - gamma T)`. (3) Equate the constant and the linear
  coefficient. (4) If the card satisfies them, the condensate entropy of C3-e has `ds_c/dT = cv_c/T` and is
  the entropy of a constant-cv substance; if not, the solved s_c carries a spurious T-dependence and the
  energy released by condensation differs from the latent heat in the saturation curve, so the moist
  adiabat and the UV temperature are biased. (5) The NASA-9 version of the same requirement is K6.
- **Check.** `check_ch3_card_latent.py`: a card built from step 3 gives `l_card/l_svp - 1` at most 8.5e-14
  over 150-400 K (tol 1e-10), PASS. For information, the cards in `tests/jupiter.yaml` give l_card/l_svp =
  0.63-0.70 for H2O(l) and 2.3-2.6 for NH3(s) at 200-300 K; step 3 would require u_c(0) - u_v(0) =
  -6786.7 K and cv_c = 8.49 for H2O on the liquid branch (card: -5380, 9.0). Note also that the H2O(l)
  reaction switches to the ice branch of `h2o_ideal` at and below T3, so one liquid card cannot match
  both branches. Authors should present this as a property of the test card, not of the method.
- **Home and status.** New subsection "Latent heat" at the end of `03-thermodynamics/_reference-state.qmd`,
  with a pointer from `02-species-data/_svp.qmd`. MISSING.

### C3-h Moist adiabat: effective heat capacity, reversible and rain-out steps

- **Question.** Along a saturated adiabat, how does the latent heat of every active reaction enter the
  temperature step, what is conserved in the reversible and in the rain-out branch, and why is rain-out
  first order in the pressure step?
- **Start.** Frozen cp (`src/thermo/extrapolate_ad.cpp:21`); `d ln K/dT` (`:27`); row scaling and the
  least-squares solve of `G dxi/dT = d ln K/dT` with G the gain returned by the TP solver (`:45-54`);
  reaction enthalpies (`:61-62`).
- **End.** `cp_eff = sum x cp + sum_r (h @ stoich)_r dxi_r/dT` (`src/thermo/extrapolate_ad.cpp:61-69`);
  reversible target `s_target = s_0 + ds_dlnp dlnp` (`:87`); rain-out target
  `(x_dry_new/x_dry0) s_0 - sum s_cond c_cloud / n_gas + ds_dlnp dlnp` (`:121-136`); update
  `T <- T (1 + (s_target - s)/cp_eff)` (`:170`), stop at `10 ftol` (`:164`).
- **Steps.** (1) On the saturated path at fixed p, the active conditions give `G dxi/dT = d ln K/dT`.
  (2) The molar enthalpy along that path changes by `cp_eff dT`, and because `dh = T ds` at fixed p for an
  equilibrium change, `ds/dT = cp_eff/T`; derive this, do not state it. (3) The update is Newton on s(T)
  with that slope, written in relative form. (4) Reversible branch: molar entropy is conserved; this equals
  conservation of total entropy only when the step does not change the total number of moles. (5) Rain-out:
  removed condensate carries its own entropy, `d(n_g s_g) = -sum s_m dn_m`; evaluating it at the end point
  only is a rectangle rule, hence first order in dlnp.
- **Check.** `check_ch3_adiabat.py` line 4b, saturated state at 280 K, 10 bar: `effective_cp` 31.3465
  J/(mol K) against a central difference of the equilibrium molar enthalpy, 3.4e-9 (tol 1e-5); molar
  entropy change over a reversible step dlnp = -0.01, 4.6e-7 J/(mol K) (tol 1e-5); PASS. (Calling
  `effective_cp` directly with an empty gain raises an error; the dry path goes through `extrapolate_dlnp`.)
- **Home and status.** `03-thermodynamics/_adiabat.qmd:47-142`. PARTIAL: step 2 is stated, not derived
  (`:90-91`); no executable check.
- (K5, not in the fix batch: the rain-out branch is first order; keep the derivation of its order.)

### C3-i Relative humidity per reaction

- **Question.** How is relative humidity defined when a reaction has several gaseous reactants?
- **Start/End.** `RH_r = prod_n c_n^{a_nr} / exp(ln K_r - sum_n a_nr ln(R T))` with `a_nr` the reactant
  coefficients over gases (`src/thermo/relative_humidity.cpp:25-33`).
- **Steps.** (1) `p_n = c_n R T`. (2) Ratio of the reactant pressure product to K. (3) Log form.
- **Check.** `check_ch3_species_functions.py`: RH against a hand value for H2O, NH3, NH4SH, at most 2.2e-16
  (tol 1e-12); |RH - 1| at present condensates after equilibration with max-iter 100, 2.0e-7 (tol 1e-6);
  PASS. With the default cap of 10, 6 of 9 cold cells are returned unconverged (D4; INFO line).
- **Home and status.** `03-thermodynamics/_relative-humidity.qmd:38-58`. PRESENT.

### C3-j Dry limit of the adiabat: Poisson's law

- **Question.** What does the adiabat routine reduce to when nothing condenses, and how does that connect
  to the potential temperature a reader knows?
- **Start.** With no active reaction the gain is empty and `cp_eff` is the frozen `sum x cp`
  (`src/thermo/extrapolate_ad.cpp:20-23`); the molar entropy of an ideal-gas mixture of fixed composition is
  `s = cp ln T - R ln p + const` (C3-b).
- **End.** The same update as C3-h (`src/thermo/extrapolate_ad.cpp:170`), whose converged result is
  `T_1 = T_0 exp((R/cp) dlnp)`, i.e. `T (p0/p)^(R/cp)` is unchanged. kintera has no separate
  potential-temperature function at the pin; state this.
- **Steps.** (1) Set ds = 0 at fixed composition. (2) Integrate to Poisson's law. (3) Show that the Newton
  update with `cp_eff = cp` converges to it. (4) Remark that with condensation the conserved quantity is
  the molar entropy of C3-h, not a single potential temperature.
- **Check.** `check_ch3_adiabat.py` line 4a: dry parcel, dlnp = -0.5, against `300 exp(-0.5 R/cp)`:
  2.0e-9 at ftol 1e-6 and 0 at ftol 1e-12 (tol 1e-8), PASS.
- **Home and status.** `03-thermodynamics/_adiabat.qmd` (opening). MISSING: no chapter mentions potential
  temperature or the dry limit.

---

## Chapter 4: phase equilibrium

### C4-a Saturation conditions as a constrained Gibbs minimum

- **Question.** When is a parcel with several vapours and pure condensates in equilibrium, and why does
  each condensate either sit exactly on its saturation curve or be absent?
- **Start.** Every nucleation reaction has gaseous reactants and one condensed product
  (`src/thermo/thermo_y.cpp:123-137`); condensates have unit activity and never enter the quotient
  (`src/thermo/equilibrate_tp.h:146`, `:160-162`); gas quotient
  `Lambda_r = sum_gas nu_ir ln(x_i/x_g)` (`:135-136`, `:158`).
- **End.** The activation test `Lambda < lnK~ - eps and condensate present, or Lambda > lnK~ + eps`
  (`src/thermo/equilibrate_tp.h:185-186`, `src/thermo/equilibrate_uv.h:451-452`), i.e. for each reaction:
  `c_m >= 0`, `lnK~_r - Lambda_r >= 0`, and their product is zero, with
  `lnK~_r = ln K_r(T) - (sum_gas nu_ir) ln p` (`src/thermo/equilibrate_tp.h:111-117`).
- **Steps.** (1) Write G of the parcel at fixed T, p with ideal-gas chemical potentials
  `mu_i = mu_i0 + R T ln(x_i/x_g) + R T ln p` and constant condensate potentials. (2) Differentiate along an
  extent: `dG/dxi_r = R T (Lambda_r - lnK~_r)` with `ln K_r = -Delta_r G0/(R T)`. (3) Minimise G with
  `n_m >= 0`; the optimality (KKT) conditions are the three conditions above, the multiplier being the
  saturation deficit. (4) Read the three cases: saturated with condensate, subsaturated without,
  supersaturated never. (5) Single vapour: partial pressure equals p_sat; NH4SH: `p_NH3 p_H2S = K(T)`
  (`src/vapors/vapor_functions.h:81-83`).
- **Check.** `check_ch4_tp.py` line 1a, 160-300 K: worst residual at present condensates 7.0e-8 (tol 1e-6),
  every absent condensate subsaturated, element ratios changed by at most 5.6e-16 (tol 1e-14); PASS.
- **Home and status.** `04-phase-equilibrium/_conditions.qmd:43-73`. PARTIAL: steps 1-3 are missing; the
  chapter never mentions chemical potential or Gibbs energy.

### C4-b K in pressure and concentration units; d ln K'/dT

- **Question.** How does a saturation curve in Pa become the right-hand side in mole fractions (TP) and in
  concentrations (UV), and what does the temperature derivative of the concentration form mean?
- **Start.** `eval_logsvp`, `eval_logsvp_ddT` (`src/thermo/svp_eval.h:34-60`); TP right side
  (`src/thermo/equilibrate_tp.h:111-117`).
- **End.** `ln K'_r = ln K_r - (sum_gas nu_ir) ln(R T)`, `d ln K'_r/dT = d ln K_r/dT - (sum_gas nu_ir)/T`
  (`src/thermo/equilibrate_uv.h:384-393`); partition form `c_v = K^(1/nu)/(R T)`,
  `dc_v/dT = c_v (d ln K/dT / nu - 1/T)` (`src/thermo/equilibrate_uv.h:59-63`, `:107-113`).
- **Steps.** (1) `p_i = (x_i/x_g) p = c_i R T`. (2) Move the p or RT factors into the constant. (3) With
  Clausius-Clapeyron `d ln K/dT = Delta h/(R T^2)`, the concentration form gives
  `d ln K'/dT = (Delta h - (sum nu) R T)/(R T^2) = Delta u/(R T^2)`: the latent energy, not enthalpy,
  which is why it appears in the UV weight (C4-d).
- **Check.** `check_ch2_svp.py` (derivatives) and `check_ch4_tp.py` (the pressure form reproduces
  `ln(x_v p/x_g) = ln p_sat`).
- **Home and status.** `04-phase-equilibrium/_equilibrate-uv.qmd:50-55`. PARTIAL: step 3 is missing.

### C4-c TP Newton system with the gas-sum term

- **Question.** How does the fixed-T, p solver turn the active conditions into a linear system for the
  extents, and why does the weight carry the term `-(sum nu)/x_g`?
- **Start.** Residual `F_r = lnK~_r - Lambda_r(x)` (`src/thermo/equilibrate_tp.h:158`, `:199`); step
  `dx = stoich @ xi`; renormalisation after the step (`:321`).
- **End.** `W_ri = nu_ir/x_i - (sum_gas nu_kr)/x_g` for gases, 0 for condensates
  (`src/thermo/equilibrate_tp.h:187-197`); `G = W @ S_active` (`:224`); the constrained least-squares step
  of C4-f (`:259-263`); per-reaction clip and halving (`:277-316`); absent gas weight
  `sign(nu) exp(-log_r)` (`:164-172`, `:190-193`).
- **Steps.** (1) `d ln(x_i/x_g)/dx_l = delta_il/x_i - 1/x_g` for gases. (2) Sum with nu: the second term is
  the non-dilute correction, negligible only when gas removal is small. (3) Chain rule along extents gives
  G; Newton `G xi = b`. (4) Renormalising all x by a common factor leaves `x_i/x_g`, hence Lambda,
  unchanged. (5) Absent gas: linearise at a small boundary level so the weight stays finite.
- **Check.** `check_ch4_tp.py` line 1b: returned gain against a finite difference of Lambda along the
  extents, at most 5.8e-10 (tol 1e-7), PASS; dropping the `-(sum nu)/x_g` term gives 7.6e-4 at the warmest
  state and 7.5e-10 at the coldest, which shows where the non-dilute term matters. Line 1c (D4): with the
  default cap 12 of 13 cold-start cells fail (EXPECTED-FAIL); with 100 all converge in 9-46 passes (PASS).
- **Home and status.** `04-phase-equilibrium/_equilibrate-tp.qmd:39-65`. PRESENT; add step 4 in one line.
- **[FIX: D4]** The default iteration cap (`src/thermo/thermo.hpp:80`) is too small for cold starts; the
  derivation is unchanged, the Tests layer must use the fixed default.

### C4-d UV Newton system with latent-heat coupling; temperature at fixed U

- **Question.** At fixed internal energy and volume, condensation releases latent heat and raises T, which
  moves the saturation curve. How does the Newton system include this, and how is T recovered?
- **Start.** `u_i(T)`, `cv_i(T)` (`src/thermo/equilibrate_uv.h:360-369`); `U = sum u_i c_i` fixed;
  `C_V = sum cv_i c_i` (`:396-399`); residual `F_r = ln K'_r - sum_gas nu_ir ln c_i` (`:422`, `:463`).
- **End.** `W_ri = (d ln K'_r/dT) u_i / C_V + [gas] nu_ir / c_i` (`src/thermo/equilibrate_uv.h:453-461`);
  after the extent step, `T <- T + (U0 - sum u_i c_i)/(sum cv_i c_i)` until `|dT| <= max(1e-4, 8 eps T)`,
  at most 100 passes (`:558-586`).
- **Steps.** (1) `0 = dU = sum u_i dc_i + C_V dT`, so `dT = -(1/C_V) sum u_i dc_i`. (2) `dF_r =
  (d ln K'_r/dT) dT - sum nu_ir dc_i/c_i = -sum_i W_ri dc_i`. (3) With `dc = S xi`, the coupling column is
  `-(d ln K'_r/dT) L_k / C_V` with `L_k = -sum_i S_ik u_i` the latent energy of reaction k. (4) Sign:
  condensation warms the parcel, raises K' and reduces the step compared with fixed T. (5) The temperature
  update is Newton on U(T) at fixed composition and converges in one pass for constant cv.
- **Check.** `check_ch4_uv.py` line 2a: final T against an independent bisection of U(T), at most 1.4e-8 K
  (tol 1e-6); U changed by 3.3e-16 and water by 2.2e-16 (relative); PASS.
- **Home and status.** `04-phase-equilibrium/_equilibrate-uv.qmd:44-100`. PRESENT; add step 4.
- **[FIX: D12]** Derive with the energy model ThermoY actually uses (the pin passes constant offsets even
  with the H2 heat capacity, `src/thermo/thermo_y.cpp:347-356`).

### C4-e Partition method: one scalar equation in T

- **Question.** If every reaction is "one vapour -> one condensate" and no species is shared, why does the UV
  problem reduce to one equation in T, and why is its root unique?
- **Start.** Qualification test (`src/thermo/thermo_y.cpp:139-163`, choice `:338-345`); conserved totals
  `W_r = c_v + (nu_v/nu_c) c_c` (`src/thermo/equilibrate_uv.h:138-158`).
- **End.** `c_v(T) = min(W_r, K_r^(1/nu_v)/(R T))`, `c_c = (W_r - c_v) nu_c/nu_v`; `U(T) = sum u_i c_i`;
  `dU/dT = sum cv_i c_i + sum_saturated c_v (d ln K/dT / nu_v - 1/T)(u_v - (nu_c/nu_v) u_c)`
  (`src/thermo/equilibrate_uv.h:59-118`); bracketing then safeguarded Newton (`:174-222`); success test
  (`:163-164`, `:226`).
- **Steps.** (1) At fixed T each disjoint pair has a closed-form equilibrium (saturated or fully
  evaporated). (2) The state is then a function of T alone: `U(T) = U0`. (3) Differentiate: the second
  term is the latent energy of the moving split. (4) Both terms are positive (latent energy positive,
  `dc_v/dT > 0` on the saturated branch), so U(T) is monotone and the root unique, which justifies
  bracketing. (5) For qualifying sets the KKT path must give the same T.
- **Check.** `check_ch4_uv.py`: T against the C4-d oracle, 5.7e-14 K (tol 1e-9); partition and KKT agree to
  1.4e-8 K; smallest dU/dT 9.4e3 J/(K m^3) > 0 and analytic dU/dT against a finite difference 4.6e-11
  (tol 1e-7); PASS. Line 2c (D6): starts at 299, 300, 301 K return diag -1 with T left at the start,
  3.0-3.5 K off (EXPECTED-FAIL).
- **Home and status.** `04-phase-equilibrium/_equilibrate-uv.qmd:115-153`. PARTIAL: steps 2-4 (c_v(T), U(T),
  dU/dT and monotonicity) are missing.
- **[FIX: D6, K4]** The success tolerance is absolute in a reference where U is near zero around Tref (D6);
  the Newton passes share the outer iteration cap (K4). Write the convergence paragraph for the fixed code.

### C4-f Active-set least squares with non-negative amounts

- **Question.** The step must not drive any amount negative. How is "solve G xi = b as well as possible
  subject to x + S xi >= 0" solved, and what do the multipliers mean?
- **Start.** Callers pass `A = G`, `C = -S_active`, `d = x` (`src/thermo/equilibrate_tp.h:259-263`,
  `src/thermo/equilibrate_uv.h:500-504`); x = 0 extent is feasible because d >= 0
  (`src/math/leastsq_kkt.h:214-233`); scaling (`:170-194`).
- **End.** Working-set KKT block `[A^T A, C_w^T; C_w, 0][xi; mu] = [A^T b; d_w]` (`src/math/leastsq_kkt.h:245-296`),
  or the direct form for square A (`:77-127`); drop rows with `mu < 0` (`:326-345`); add the most violated
  independent row (`:368-408`); stop when the working set repeats (`:410-414`).
- **Steps.** (1) Lagrangian `1/2 |A xi - b|^2 + mu^T (C xi - d)`; stationarity, primal and dual
  feasibility, complementarity. (2) With the working set held as equalities this is the block system.
  (3) `mu < 0` means moving off that bound lowers the objective, so the row is released. (4) Direct form:
  multiply the first block row by `A^-T` to avoid squaring the condition number. (5) Two condensates on one
  vapour give dependent rows; only independent rows are added, so the caller clips each extent to its
  reactant stock. (6) `-S xi <= x` is `x + S xi >= 0`.
- **Check.** No Python binding; indirect: `check_ch4_tp.py` cells with two condensates sharing NH3 stay
  non-negative and conserve N and S. A direct C++ test (2x2 problem with one active bound against the
  analytic KKT solution) is the stronger check; propose it in the Tests layer.
- **Home and status.** `04-phase-equilibrium/_active-set.qmd:44-75`. PARTIAL: steps 1-4 are deferred to the
  literature; write them here (`10-numerics/_kkt.qmd` can then cite this section).

---

## Chapter 5: chemical equilibrium

### C5-a ln K from Gibbs energies

- **Question.** Where does the dimensionless equilibrium constant come from?
- **Start.** `nasa9_gibbs_RT` (`src/thermo/nasa9.hpp:27-62`); `Nasa9LogK.__call__`
  (`python/equilibrium/nasa9.py:23-28`); independent reaction columns (`src/equilibrium/equilibrium.cpp:78-80`).
- **End.** `ln K0_r = -sum_n nu_nr g0_n/(R T)` (`python/equilibrium/nasa9.py:28`).
- **Steps.** (1) `mu_n = g0_n + R T ln a_n`; `sum nu mu = 0` gives `sum nu ln a = ln K0`. (2) `g = h - T s`
  from C2-a. (3) Gas standard state p0, so `a = x p/p0`; pressure enters only through activities.
  (4) Van 't Hoff `d ln K0/dT = Delta h0/(R T^2)` (needed by C6-d).
- **Check.** `check_ch5_equilibrium.py` line 3c: residual 8.0e-12 (tol 1e-10), H and O conserved to 2.2e-16,
  van 't Hoff derivative against a finite difference 4.7e-10 (tol 1e-6); PASS.
- **Home and status.** `05-chemical-equilibrium/_log-k.qmd:43-69`. PRESENT; step 4 is new and short.

### C5-b Activity conditions; element conservation by construction

- **Question.** What equations does EquilibriumTP solve, and why are elements conserved without being imposed?
- **Start.** Activities `(N_n/N_phase)(p/p0)` in the gas and `N_n/N_phase` otherwise
  (`src/equilibrium/phase_equilibrate_tp.h:22-36`).
- **End.** `r_r = sum_n nu_nr ln a_n - ln K0_r` (`src/equilibrium/phase_equilibrate_tp.h:27-35`);
  `N = N0 + S xi` with bounds from `-S` (`:113-119`).
- **Steps.** (1) Ideal mixing in each phase. (2) Reaction equilibrium gives `r_r = 0`. (3) A one-species
  condensed phase has unit activity (ties to C4-a). (4) `E S = 0` for balanced reactions, so `E N = E N0`.
- **Check.** `check_ch5_equilibrium.py` line 3a: two-phase vapour-liquid case against the analytic
  `n_v = n_N2 p_sat/(p - p_sat)`, 2.3e-12 (tol 1e-10) in 4 iterations, PASS.
- **Home and status.** `05-chemical-equilibrium/_conditions.qmd:43-81`. PRESENT.

### C5-c Newton in reaction extents: Jacobian, bounds, line search, diagnostics

- **Question.** How are extents updated so that residuals fall and amounts stay above the floor, and what
  does the reported error mean?
- **Start.** Phase sums `nu_{pi,k} = sum_{n in pi} nu_nk` (`src/equilibrium/phase_equilibrate_tp.h:79-83`).
- **End.** `J_rk = sum_n nu_nr (nu_nk/N_n - nu_{pi(n),k}/N_{pi(n)})` (`src/equilibrium/phase_equilibrate_tp.h:97-111`);
  LU solve with constrained least-squares fallback (`src/math/constrained_newton.h:27-57`); halving line
  search on `max|r|` (`src/equilibrium/phase_equilibrate_tp.h:132-153`); stop at `max|r| <= log1p(ftol)` and
  reported error `exp(max|r|) - 1` (`:84`, `:156-163`).
- **Steps.** (1) `d ln(N_n/N_pi)/dxi_k = nu_nk/N_n - nu_{pi,k}/N_pi`. (2) A one-species phase contributes
  zero. (3) Direct LU keeps cond(J) instead of its square. (4) Feasibility as linear inequalities. (5) The
  merit function and what it does not guarantee. (6) `exp|r| - 1` is the relative mismatch between quotient
  and constant, so the stopping test is a relative tolerance.
- **Check.** `check_ch5_equilibrium.py` line 3b: Jacobian formula against a finite difference at the
  converged state, 2.1e-10 (tol 1e-8), PASS.
- **Home and status.** `05-chemical-equilibrium/_newton.qmd:47-85`, `_diagnostics.qmd:13-40`. PRESENT; add
  that the returned gain is formed at the iterate before the last.

---

## Chapter 6: kinetics

### C6-a Mass action and species tendency

- **Question.** Why is a rate "k times a product of concentrations", and how do rates become tendencies?
- **Start.** Stoichiometry with reversible reactions appended as negated columns (`src/kinetics/kinetics.cpp:106-128`);
  forward orders (`:277-294`); concentration floor (`:491-492`).
- **End.** `r_j = k_j prod_i max(c_i, floor)^{order_ij}` (`src/kinetics/kinetics.cpp:495`); `dc/dt = S r`.
- **Steps.** (1) Event rate per volume proportional to each partner's number density. (2) Units of k.
  (3) `dc_i/dt = sum_j S_ij r_j`. (4) A reversible reaction as two columns gives `r_f - r_r`. (5) Any atom
  vector a with `a S = 0` is conserved exactly.
- **Check.** `check_ch6_rates.py` lines a1-a2 (four reactions including `2 H => H2` and a termolecular one):
  rate against `k prod c^order` exactly (0, tol 1e-13); atom matrix times S exactly 0; PASS.
- **Home and status.** `06-kinetics/_mass-action.qmd:42-58`. PRESENT; add step 5.

### C6-b Arrhenius law and the unit factor

- **Question.** What does the input pre-factor mean and by what factor is it rescaled?
- **Start.** Modified Arrhenius with defaults (`src/kinetics/arrhenius.cpp:95-97`; an omitted `Ea_R` is 1 K,
  not 0, `:96`; the rate reference temperature is its own option, 300 K, `src/kinetics/arrhenius.hpp:62`,
  separate from the thermodynamic Tref); unit string from the reaction order (`:71-74`, `:87-90`).
- **End.** `A_SI = A_input (N_A 1e-6)^(n-1)` (`src/kinetics/arrhenius.cpp:87-90`);
  `k = A (T/Tref)^b exp(-Ea_R/T)` (`:291-292`), temperature bands (`:298-305`).
- **Steps.** (1) Same physical rate in both unit systems. (2) `c[molecule/cm^3] = N_A 1e-6 c[mol/m^3]`.
  (3) Hence the factor `(N_A 1e-6)^(n-1)`. (4) Band selection makes k piecewise but single-valued.
- **Check.** `check_ch6_rates.py` line b: stored A against `A_in (N_A 1e-6)^(n-1)` for n = 1, 2, 3, at most
  2.2e-16 (tol 1e-12); k against the formula, 2.2e-16; PASS.
- **Home and status.** `06-kinetics/_arrhenius.qmd:54-65`. PARTIAL: steps 1-3 ("not drafted yet", `:65`).

### C6-c Fall-off from the Lindemann mechanism; pressure switch

- **Question.** How do pressure-dependent rate constants interpolate between low- and high-pressure limits?
- **Start.** Three-body concentration `[M] = sum eps_n c_n` (`src/kinetics/three_body.cpp`); fall-off forms
  in `src/kinetics/lindemann_falloff.cpp`, `troe_falloff.cpp`, `sri_falloff.cpp`; switch
  (`src/kinetics/arrhenius.cpp:308-313`).
- **End.** `k = k0 [M] / (1 + Pr) F`, `Pr = k0 [M]/k_inf` (cite the evaluating lines in the fall-off files);
  switch `where(P < p_th, f k, k)` (`src/kinetics/arrhenius.cpp:313`).
- **Steps.** (1) Mechanism `A + M <-> A* + M`, `A* -> P`; steady state of A* gives
  `k = k0 [M]/(1 + k0 [M]/k_inf)`. (2) The two limits. (3) Broadening factors are empirical
  interpolations in `log10 Pr`. (4) k0 carries one more concentration order, so its unit factor has one
  more power. (5) The switch is a step in p with no derivative.
- **Check.** `check_ch6_rates.py` lines c1-c3: Lindemann k against `k0[M]/(1+Pr)` for Pr = 1e-6..1e6 with a
  third-body efficiency, 4.4e-16 (tol 1e-12); both limits reached to 1e-6 at Pr = 1e-6 and 1e6; PASS.
- **Home and status.** `06-kinetics/_falloff.qmd:38-80`, `_pressure-switch.qmd:36-48`. PARTIAL: step 1 is
  missing.

### C6-d Reverse rates from K_c (detailed balance) and their T-derivative

- **Question.** Why is `k_r = k_f / K_c`, how does K_c follow from Gibbs energies with concentration units,
  and what is `dk_r/dT`?
- **Start.** Reversible columns (`src/kinetics/kinetics.cpp:92-128`); `g/RT` per species (`:510-511`);
  `Delta n` = products minus reactants (`:268-271`).
- **End.** `ln K_c = -Delta g/(R T) + Delta n ln(P_ref/(R T))` (`src/kinetics/kinetics.cpp:512-516`);
  `k_r = k_f / max(K_c, 1e-250)` (`:524-526`); `dk_r/dc = (dk_f/dc)/K_c` (`:532-534`); at the pin
  `dk_r/dT` is a plain copy of `dk_f/dT` (`:536-539`).
- **Steps.** (1) At equilibrium each elementary forward rate equals its reverse rate. (2)
  `mu = g0 + R T ln(c R T/P_ref)`. (3) `sum S mu = 0` gives `prod c^S = K_c`. (4) Hence the kinetic fixed
  point is the chemical equilibrium of chapter 5. (5) `d ln k_r/dT = d ln k_f/dT - d ln K_c/dT`, and
  `d ln K_c/dT = Delta u0/(R T^2)` (C5-a step 4 in concentration units), so
  `dk_r/dT = (dk_f/dT)/K_c - k_r d ln K_c/dT`. The pin copies `dk_f/dT`, which lacks both the factor 1/K_c
  and the second term; the error is far larger than the van 't Hoff term alone unless K_c is near 1.
  Write the derivation for the correct expression and record the pin's behaviour in Limits.
- **Check.** `check_ch6_rates.py` line d1, `O + O2 <=> O3` and `O + O3 <=> 2 O2` at 300 and 1500 K (both
  NASA-9 ranges): K_c from the code (k_f/k_r) against an independent K_c from `data/nasa9.dat`, at most
  1.1e-14; per-reaction imbalance at a state with `prod c^S = K_c`, at most 1.1e-14 (tol 1e-10); PASS.
  Line d2: forward dk/dT against a finite difference 2.4e-10, PASS; reverse column -81.9 against the true
  4.8e-8, EXPECTED-FAIL; the observed error equals the predicted `dk_f/dT - dk_r/dT` to 2.4e-10, PASS.
- **Home and status.** `06-kinetics/_mass-action.qmd:60-62`. MISSING ("not drafted yet").

### C6-e Evaporation rate and its fixed point at saturation

- **Question.** Why is the evaporation rate zero exactly at saturation and never negative, and where does
  `kappa = 12 D v_m / d^2` come from?
- **Start.** `D = D0 (T/Tref)^aT (p/pref)^ap` (`src/kinetics/evaporation.cpp:218-219`); the same
  saturation function as the thermodynamics (`:260-261`); one condensed reactant with coefficient 1
  (`:252-258`).
- **End.** `kappa = 12 D v_m / d^2` (`src/kinetics/evaporation.cpp:221`); `K = exp(ln p_sat - (sum nu) ln(R T))`
  (`:267-268`); `eta = max(K - c_v, 0)` (`:276-278`); two products: closed-form extent (`:281-306`); general:
  implicit extent (`:309-325`); rate `kappa eta c_p` (`:326`, `src/kinetics/kinetics.cpp:496-502`).
- **Steps.** (1) Diffusion-limited growth of a sphere: flux `4 pi a D (c_sat - c_inf)` per particle.
  (2) Particles per volume `c_p v_m/(pi d^3/6)`; multiply to get `12 D v_m c_p (K - c)/d^2` (this reading of
  the factor 12 must be confirmed against the code author's source before it is printed as fact).
  (3) `K_p -> K_c` with `p = c R T`. (4) The rate vanishes at `c_v = K`, the phase-equilibrium condition
  (O-2). (5) The clamp makes the column one-way: supersaturation is relieved by the condensation path, not
  by a negative evaporation rate. (6) Two products: `(c1 + x)(c2 + x) = K`, root written without
  cancellation.
- **Check.** `check_ch6_evaporation.py`: rate against `kappa c_p (K - c_v)` at `c_v = 0.5 K`, 1.7e-16
  (tol 1e-10); at `c_v = K`, 1.4e-16 of the scale; at `1.5 K`, exactly 0; two-product root
  `(c1 + x)(c2 + x) = K` at four states including c1 = 0, 2.5e-15 (tol 1e-12); PASS.
- **Home and status.** `06-kinetics/_evaporation.qmd:38-61`. PARTIAL: steps 1-5 ("not drafted yet", `:61`).

### C6-f Kessler form in mole fractions

- **Question.** Why does `kappa = k3/n` reproduce Kessler's `dx_v/dt = k3 x_p (x_sat - x_v)`?
- **Start/End.** `n = P/(R T) + sum c_condensed` and `kappa = k3/n` (`src/kinetics/evaporation.cpp:244-249`).
- **Steps.** Substitute `c = n x`; n is constant in a closed cell for one-to-one conversion; divide by n;
  closed-form box solution.
- **Check.** Existing `tests/test_evaporation_kessler.py` (closed form and Jacobian).
- **Home and status.** `06-kinetics/_kessler.qmd:36-62`. PRESENT.

### C6-g Jacobian with temperature feedback at fixed internal energy

- **Question.** What is `dr_j/dc_k` when temperature is not held fixed but follows from energy conservation?
- **Start.** `dk/dc`, `dk/dT` from autograd (`src/kinetics/kinetics.cpp:421-467`); the evolve-temperature
  switch (`:409-411`); `u_k = R eval_intEng_R` (`:373`, `src/thermo/eval_uhs.cpp:266-301`); caller supplies C_V.
- **End.** `J_jk = P_j dk_j/dc_k + order_kj r_j/c_k - P_j (dk_j/dT) u_k / C_V`
  (`src/kinetics/kinetics.cpp:370-376`), with `P_j = prod c^order` (evaporation rows use `c_p`, `:343-369`).
- **Steps.** (1) Product rule at fixed T. (2) Closed cell, fixed volume, no heating: `dU = 0` with
  `U = sum c_k u_k(T)`. (3) `(dT/dc_k)_U = -u_k/C_V`. (4) Chain rule:
  `(dr/dc_k)_U = (dr/dc_k)_T + (dr/dT)_c (dT/dc_k)_U`, with `(dr/dT)_c = P dk/dT`. (5) The energies must
  carry the same offsets as ThermoY (O-2), and C_V must be at constant volume.
- **Check.** `check_ch6_jacobian.py`: analytic Jacobian against a central difference of `r(c, T(c))` with T
  solved from fixed U, at most 1.5e-10 (tol 1e-8), PASS. The fixed-T derivatives have the wrong sign for
  one entry and are 0 for another where the feedback value is 1.4e7, so the test does see step 4.
- **Home and status.** `06-kinetics/_jacobian.qmd:35-52`. PARTIAL: steps 2-4 ("not drafted yet", `:52`).
- Rerun the check after the fix batch, which edits the energy function this Jacobian calls.

### C6-h Linearly implicit step and the two-stage Rosenbrock variant

- **Question.** What linear system does one step solve, and of what order is it?
- **Start.** `dc/dt = S r(c)`, J from C6-g; per-cell solve (`src/kinetics/evolve_implicit_impl.h`).
- **End.** `(I/dt - S J) delta = S r(c^n)`; Rosenbrock `W = I/(gamma dt) - S J`, `gamma = 1 + 1/sqrt 2`,
  stage and weight coefficients at `src/kinetics/evolve_implicit.hpp:48-70`, `:92-98`.
- **Steps.** (1) Backward Euler linearised once about c^n; local error O(dt^2), global O(dt). (2) Expand the
  two Rosenbrock stages in dt; the order-2 conditions hold for any W (W-method). (3) This gamma makes the
  stability function vanish at infinity (L-stable).
- **Check.** `check_ch6_implicit.py`: error ratio when the step halves (N = 50 to 100), 1.992 for backward
  Euler and 3.882 for Rosenbrock (expected 2 and 4, within 10%); atom drift at most 5.6e-16; PASS.
- **Home and status.** `06-kinetics/_implicit.qmd:33-52`. PARTIAL: steps 2-3 and a measured order.

---

## Chapter 9: atm2d

### C9-a Eddy diffusion in concentration and mixing-ratio forms

- **Question.** Why does the mixing-ratio form use the face density, and why does a uniform mixing ratio
  give zero flux?
- **Start.** Face diffusivity mean (`python/atm2d/transport.py:984`, `:994`); face density
  `0.5 (n_i + n_{i+1})` (`:77`).
- **End.** `F = K n_f (c_{i+1}/n_{i+1} - c_i/n_i)/dx` assembled in `_assemble_vertical_scalar_diffusion`
  (`python/atm2d/transport.py:474`) and distributed by `_add_two_cell_block` (`:641`).
- **Steps.** (1) Eddy mixing conserves the mixing ratio of a parcel, so the flux is `-K n d(c/n)/dz`.
  (2) Cell integral, centred face gradient. (3) Telescoping sum: exact column conservation. (4) Uniform
  mixing ratio gives F = 0 identically.
- **Check.** `check_ch9_atm2d.py` lines a1-a2 (random density, K and non-uniform grid): uniform mixing ratio
  gives 1.1e-16 of the scale, column integral 6.3e-17 (tol 1e-13); PASS.
- **Home and status.** `09-atm2d/_transport.qmd:40-77`. PRESENT; step 1 is asserted, give its one-line reason.

### C9-b Molecular diffusion and the diffusive-equilibrium profile

- **Question.** Why is a species' own-scale-height profile an equilibrium of the mixing-ratio forms but not
  of the concentration form?
- **Start.** Centred gravitational term (`python/atm2d/transport.py:533`); exponential scheme
  (`:315`, `:397-398`); hybrid threshold (`:452`).
- **End.** Centred: `F_i = -D (dc_i/dz + c_i/H_i)`; exponential:
  `F_i = (D/dz)(c_L e^{-S} - c_R e^{S})`, `S = dz/(2 H_eff)` (`python/atm2d/transport.py:315-420`).
- **Steps.** (1) Textbook flux of a minor species, `-D(dc/dz + c/H_i + (1 + alpha_T) (c/T) dT/dz)`; drop
  the thermal term when isothermal, and say whether the code keeps it. (2) With `d ln n/dz = -1/H`,
  `-D n d(c/n)/dz = -D(dc/dz + c/H)`; adding the separation term gives `c/H_i`. (3) F = 0 gives
  `c_i ~ exp(-z/H_i)`. (4) The exponential flux vanishes exactly for that ratio at any dz; the centred form
  is exact only when the species mass equals the mean, and is second order in dz otherwise in interior
  cells; boundary rows are one-sided and first order. (5) Small-S expansion recovers the centred form.
- **Check.** `check_ch9_atm2d.py` lines b1-b2: own-scale-height profile at dz = H/2 is stationary under
  both mixing-ratio forms (1e-15) and not under the concentration form (2.6 D c/H^2); minor species with
  twice the mean mass: exponential scheme stationary to 7.4e-14 on three grids, centred scheme interior
  error falls by 4.05 and 4.01 per halving (with boundary cells only about 2.2); PASS.
- **Home and status.** `09-atm2d/_molecular.qmd:41-87`. PARTIAL: steps 1 and 4.

### C9-c Source linearisation and stoichiometric mapping

- **Question.** How do kinetics Jacobian blocks enter the species Jacobian?
- **Start/End.** `build_source_linearization` (`python/atm2d/sources/combine.py`); `build_chemistry_jacobian`
  (`python/atm2d/chemistry.py`): `J_nm = sum_r nu_nr dR_r/dc_m`.
- **Steps.** Chain rule through `dc/dt = S r(c)`; mass-action column; boundary flux; charge-balance fold.
- **Check.** `check_ch9_sources.py`: FD of the source tendencies against their Jacobians, 1e-7 relative (mass
  action, a kintera network, boundary sources, the charge-balance fold); 8 PASS.
- **Home and status.** `09-atm2d/_sources.qmd:39-71`. PRESENT.

### C9-d Implicit assembly and Rosenbrock-2 order

- **Question.** What system does a step solve, and why is the two-stage Rosenbrock scheme second order even
  with an approximate Jacobian?
- **Start.** `build_implicit_step_system` (`python/atm2d/assembly.py:116`); `gamma = 1 + 1/sqrt 2`
  (`python/atm2d/rosenbrock.py:42`); `rosenbrock2_step` (`:81`).
- **End.** `A = I/(gamma dt) - L`; two stages; `c1 = c0 + (1.5/gamma) k1 + (0.5/gamma) k2`
  (`python/atm2d/rosenbrock.py:165`); embedded estimate `|c1 - y2|`.
- **Steps.** (1) Expand both stages for `y' = f(y)` with an arbitrary matrix L. (2) Order-2 conditions in
  this scaling, independent of L. (3) L-stability from this gamma. (4) The first stage is first order, so
  the difference estimates the error.
- **Check.** `check_ch9_atm2d.py` line c: error ratio under dt halving 3.86 with the exact Jacobian and 3.82
  with half of it (expected 4 within 10%; the ratio from 20 to 40 steps, 3.7, is not yet asymptotic); PASS.
  Steps 3 and 4 also: `check_ch9_ros2_stability.py` (7 PASS) and `check_ch9_ros2_error.py` (8 PASS).
- **Home and status.** `09-atm2d/_assembly.qmd:36-53` PRESENT, `_rosenbrock.qmd:36-60` steps 1-3 cited not
  derived: PARTIAL.

### C9-e Newton iteration and the steady-state limit

- **Question.** Why is the re-linearised backward-Euler system Newton's method, and what is its large-dt limit?
- **Start/End.** `newton_implicit_step` (`python/atm2d/newton/coupled.py:21`):
  `(I - dt L(c^k)) c~ = c0 + dt [S(c^k) - J(c^k) c^k]`, damped and clipped update.
- **Steps.** Residual `G(c) = c - c0 - dt [T c + S(c)]`; Newton step rearranged; `dt -> infinity` gives
  Newton on `T c + S(c) = 0`; clipping and damping lose quadratic convergence.
- **Check.** `check_ch9_newton.py`: one iteration against a hand Newton step, observed order and the residual ratio
  `|G_{k+1}|/|G_k|^2` bounded near the root, linear rate under damping, and the 1/dt approach to the steady state;
  6 PASS.
- **Home and status.** `09-atm2d/_newton.qmd:37-54`. PRESENT; the large-dt limit is derived (step 4).

### C9-f Atomic-budget projection

- **Question.** What does the conservation repair do, and when does it remove exactly the excess?
- **Start/End.** `project_atomic_budget` (`python/atm2d/conservation/atomic.py:79`): excess
  `X_e = max(0, sum A_n - B_e)` removed proportionally from species above the mean, with floors
  (`:124`, `:130`, `:133`).
- **Steps.** Atoms per species; proportional removal sums to `X_e` when the floor is inactive; one element at
  a time is not a projection onto all budgets at once.
- **Check.** `check_ch9_atm2d.py` line d: post-projection total equals the budget exactly (0, tol 1e-13), PASS.
  The removal weight divides by a hog total clamped to at least 1 (`python/atm2d/conservation/atomic.py:130`),
  so below 1 the excess is removed only in part (info line: 0.405 left against a budget of 0.3); the
  derivation must state this condition.
- **[FIX: K9]** The hog-total floor at `python/atm2d/conservation/atomic.py:130` is defect K9 of #54. Derive the
  corrected rule (division by the hog total itself); the pinned code coincides with it for a hog total of at least 1
  and differs below, which stays as a Limits note. `check_ch9_budget_below1.py` has two EXPECTED-FAIL lines that are
  expected to pass after the fix.
- **Home and status.** `09-atm2d/_conservation.qmd:35-60`. PRESENT.
