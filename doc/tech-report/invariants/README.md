# 2603 invariant checks

The supplied specification replaces the previously missing “2603” definition.
Run from the report environment:

```sh
python invariants/check_invariants.py --output invariants-result.json
python invariants/check_guard_effects.py
python invariants/inventory_guards.py .reproduce/sources/kintera --check
python invariants/inventory_guards.py .reproduce/sources/kintera --check --require-effects
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

## Floor inventory limitations

`guard-inventory.json` records every hit of the committed broad lexical search
across 137 C/C++/CUDA source files, with file hashes, full-SHA links, surrounding
statements and explicit evidence status. It includes false positives, dimensional
bounds and comments so exclusions are auditable. `guard-inventory.md` is its
readable table. Per-occurrence native effect coverage and whole-report
non-reachability are **not yet established** for all rows. The selected two decks
do not dispatch photochemistry, evaporation/falloff or TP equilibrium; this
limited non-dispatch result must not be generalized to the other report cases.

The separate `--require-effects` gate exits 1 while per-occurrence evidence is
incomplete. The one-command audit includes this gate so inventory completeness
cannot be mistaken for verified physical coverage.

### Reviewed classification and extracted native operations

`guard-classification.json` / `.md` classify all 250 original candidates and
17 additional unique hits (267 total). The extra search used
`(1\.?0?e-|1\.e-|1e-)|\b(?:epsilon|tiny|floor)\b|[?:].*0\.` and manual review
of constrained Newton, phase-equilibrium and KKT conditions. Literal search
also finds units, comments and tolerances; those are not automatically species
floors. The original hashed inventory remains unchanged.

There are 138 applicable physical/numerical operations and 129 excluded
comments, diagnostics, dimensions, model selections, stoichiometric definitions
or uses of an already inventoried bound. These are **not 138 concentration
floors**. The row descriptions distinguish amounts from derivative denominators,
rate coefficients, tolerances and state masks.

```sh
python invariants/probe_guard_operations.py .reproduce/sources/kintera \
  --output .reproduce/logs/guard-operations.json \
  --build .reproduce/logs/guard-operation-build
python invariants/test_guard_coverage.py
python invariants/inventory_guards.py .reproduce/sources/kintera --check \
  --require-effects --effects .reproduce/logs/guard-operations.json
```

The first command extracts 43 clamp calls from the pinned native source,
compiles their C++/LibTorch operations, binds the intermediate physical quantity,
and compares active/boundary/inactive binary64 inputs **exactly**, including
adjacent representable boundary values. It verifies all 137 source-file hashes
before compiling. The gas-floor option is explicitly bound to its documented
1e-20 default; interpolation uses four coordinates; dtype-dependent `tiny`
uses the binary64 branch. It does not claim execution of the containing solver,
full-report branch reachability, float32 or CUDA coverage. Other predicates and
state transitions need additional source-bound or whole-function checks.

The coverage command still **exits 1: 43 measured, 95 unresolved**. Classification
alone produces 0 measured / 138 unresolved. Hand-transcribed operation fixtures
are not credited as native-source evidence. Negative controls reject an omitted
original candidate and a changed observed value. The unchanged 1000-step
invariants and actual-source mutations remain the full-solver checks.
