# 2603 invariant checks

The supplied specification replaces the previously missing “2603” definition.
Run from the report environment:

```sh
python invariants/check_invariants.py --output invariants-result.json
python invariants/check_guard_effects.py
python invariants/inventory_guards.py .reproduce/sources/kintera --check
```

The first command exits 1 for any failed invariant or exception. CPU, binary64,
1000 steps; no clipping, post-step repair, epsilon, or negative allowance.

## Committed inputs and definitions

* `reaction.yaml` is the unchanged A => B card in
  [chapter 6's implicit check](https://github.com/UCzhangxi/kintera/blob/83c4ee3e489139fefbaa863257623ebf80411bb1/doc/tech-report/derivation-checks/check_ch6_implicit.py#L20).
  Both species contain one H atom and have identical constant cv/R=1.5, zero
  formation offset, Tref=0. Two closed one-cubic-metre cells begin with (A,B)
  = (0,1) and (1,0) mol/m³. T=300 K, dt=0.001 s; 1000 implicit Euler steps.
  Rate of the absent-A cell must be **exactly zero at every step**; every amount
  in both cells must be **>=0 at every step**, with no epsilon. The identical
  thermochemistry makes the fixed temperature compatible with an adiabatic,
  rigid volume: no heat, work, transport, photons or external species sources.
  U=R*1.5*T*(A+B). This energy check is intentionally algebraically dependent
  on atom conservation; the phase-change case below tests nontrivial offsets.
* `condensation.yaml` is the chapter 4 water card, selecting its partition solver:
  [original card and cases](https://github.com/UCzhangxi/kintera/blob/83c4ee3e489139fefbaa863257623ebf80411bb1/doc/tech-report/derivation-checks/check_ch4_uv.py#L20).
  rho=1 kg/m³, initial water vapour mass fraction .02, liquid=0, T=280 K.
  1000 closed, rigid-volume UV equilibrium projections; **these are not kinetic
  timesteps**. The first projection condenses water; subsequent projections test
  accumulation at equilibrium. No external heat/work or material sources.
  Independent atom matrix rows H/He/O are (1.5,2,2),(.15,0,0),(0,1,1).
  U=sum_i c_i R [u0_R,i + cv_R,i (T-300)], with cv_R=(2.5,2.5,9) and
  u0_R=(0,0,-3430); this oracle is independent of native energy evaluation.
  R=8.31446 J/(mol K), matching the cited card check. Dry pseudo-species atom
  fractions are retained literally. Solver diagnostics must indicate convergence.

For each budget, report max_j |B_j-B_(j-1)| / S, max_j |B_j-B_0| / S,
and signed (B_N-B_0)/(N*S). The acceptance threshold is **1e-12 per step**,
not a total drift divided by 1000. Atom scales are initial nonzero totals for
individual elements/cells. Energy scales are the initial sum of absolute
reference and sensible contributions, preventing cancellation near zero energy.
All scales in these committed cases are positive. No source exception is used.
Enthalpy is not the conserved potential in these rigid-volume cases.

## Actual-source break tests

`mutate_sources.py SOURCE floor|atoms|energy` requires a clean disposable checkout
of e357792d50639d68e9090b542edf038d2b029aa2 and applies an explicit source patch:

* `floor`: replace the two kinetics concentration-zero clamps by 1e-300 floors;
* `atoms`: remove the last species' implicit production increment;
* `energy`: remove the condensed species' reference-energy term in native
  `eval_intEng_R` (the two gas reference terms remain).

The committed driver `bash invariants/run_source_checks.sh NEW_OUTPUT_DIRECTORY`
clones public source, builds pre/main/three mutations, and rejects runtime errors
masquerading as RED through `verify_break_results.py`. Use the report's committed
environment and a new output directory; allow the five source builds to finish.

Reconfigure/build per the package README and install to a **new** isolated
`--target` directory for each variant; run the unchanged check with that target
first on PYTHONPATH. Never alter an installed package. Patches, builds, exact
commands, source identities and RED/GREEN results are recorded with this PR.
The inventory check also rejects a changed source tree; that is an inventory
integrity test, not a substitute for physical effect coverage.

## Guard inventory and source-bound effects

`guard-inventory.json` preserves the initial 137-file, 250-row lexical inventory.
`guard-classification.json` / `.md` classify those rows plus 17 supplemental hits:
267 total, comprising 138 applicable physical/numerical operations and 129 excluded
comments, diagnostics, dimensions, model selections, stoichiometric definitions
and already-bounded uses. These are not 138 concentration floors. The supplemental
search used `(1\.?0?e-|1\.e-|1e-)|\b(?:epsilon|tiny|floor)\b|[?:].*0\.` plus
manual review of phase, Newton and KKT conditions. This is lexical/manual coverage,
not an AST or macro-expansion proof. The supplementary mole-slack locator was
corrected from line 116 (the following loop) to the assignment at line 115.

```sh
python invariants/probe_guard_operations.py .reproduce/sources/kintera \
  --output .reproduce/logs/guard-operations.json \
  --build .reproduce/logs/guard-operation-build
python invariants/probe_source_effects.py .reproduce/sources/kintera \
  --output .reproduce/logs/guard-source-effects.json \
  --build .reproduce/logs/guard-source-build
python invariants/inventory_guards.py .reproduce/sources/kintera --check \
  --require-effects --effects .reproduce/logs/guard-operations.json \
  --source-effects .reproduce/logs/guard-source-effects.json
python invariants/test_guard_coverage.py
```

The first probe extracts 43 clamp calls and checks 257 boundary values exactly.
The second compiles verbatim production statements/expressions and the complete
native Newton trial function with explicit intermediate physical inputs. Its 97
fixtures cover the other 95 occurrences, including nonfinite-input rejection,
policy-disabled and inactive-gradient controls. See `SOURCE-GUARD-EFFECTS.md` and
the committed JSON inputs/results. The source file hashes, exact fragments,
manifest and probe identities are checked; missing or failed evidence stays red.

Coverage passes only with both measured artifacts: 138 applicable occurrences,
zero missing. Classification alone still has zero measured occurrences; the
clamp-only subset still leaves 95 missing. This does not assert full-report branch
reachability, float32/CUDA behavior or the physical harmlessness of every floor.
It measures each listed operation's local physical/numerical effect. The source
bindings document the binary64 constants, default options and intermediate states.

Exact equality is required except for six log/exp/pow fixtures allowing eight
binary64 eps relative and zero absolute tolerance for transcendental rounding.
All measured errors were zero. Existing exact-zero/nonnegative assertions,
1e-12 per-step budgets and scientific/figure baselines are unchanged. Whole-solver
source mutation checks remain separate and their original evidence is preserved.

### Dtype branch regression

The initial statement run compiled but did not select the explicit float32
constant branches. A new coverage regression failed before adding native
float32 normal-floor, subnormal-floor and negative-power cases; it passes now.
Both dtype branches of those source definitions are exercised. The source-bound
suite has 100 fixtures and 302 scalar observations; together with clamps, 559
observations were exact. This does not claim general float32 solver coverage.
The superseded reproduction at 868ec3206435730c0a79e47d0130662a5d1b1b61 was stopped
with exit 143 during source building; it is not a completed audit or a setup
failure. Its logs are retained, and a new final-head reproduction is required.
