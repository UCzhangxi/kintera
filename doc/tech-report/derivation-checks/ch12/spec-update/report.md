# Chapter 12: six-entry mapping and bounded complements

I accept continued bounded ownership of C12 check validation for Tianhao, home `C0C2D3PCW20:1792350030.238029`. I read all C12-a through C12-f and the S12-1 suspect in the separate specification. This updates the earlier check-validation report: the checks bundle did not contain the six entries; the newly supplied specification does. The prior 102-comparison campaign and eight passing targeted tests were preserved, not rerun. No implementation fix, chapter edit, external post, GitHub write or new commit was made.

## Inputs and identity

- Separate specification: `DERIVATION_SPEC_round2.md`, 91,435 bytes, SHA256 `c46adfbf0f327dfba99d18cfe3763570179d0fa32431bbce0b8f7c5705bb0301`; C12 is lines 523–642, S12-1 lines 967–987. The extracted C12 section is included beside this report.
- Authoritative checks-bundle SHA256: `e997abfcb04ba59a4f004af3e1317d063bec2455ad9c4a714e556ccd026290d9`.
- Implementation **`0d9f67f97d841147e23283d2dcdab302238d2c45`**; tracked source clean, pre-existing untracked `build` symlink. Loaded binaries rehashed and equal to preparation. The historical worker1 environment is only the interpreter; actual code comes from the verified worker2 exact-pin build.
- Python 3.11.13, NumPy 2.4.6, torch 2.10.0+cu128; Release/GCC11.5/nvcc12.9/architecture120 build. GPU0 RTX5090, driver615.71.09. Loaded CUDA12 and CUDA13.2 runtime libraries remain as recorded; not a pure12.9 runtime claim. One CPU/BLAS thread, GPU0 only, read-only environment reuse, no build/install/scheduler job.
- CPU library SHA256 `950280d238fc79800d88c00919b281905121559b585a4c57590791129f08893c`; CUDA library `44a91be2a89b13514d0710e5cc2623441626b06cb44edc60b2a3c4465300bc21`; extension `eb1b81569889eb405463dd0565353157b13f439d5cde7c65953c2b10d7d73dd3`.
- Saved report head `0d525973c0b3659adaae91c22c251b4640a32126`, parent `f97ca7e4c0427cfb6046e8f0bc17d9b93c362404`, report/main merge base `4dc613d04f24621b3119d343c5c7c9b93628895b`. These are the previously verified preparation refs, not a claim to have queried a new chapter branch. No chapter branch was touched. Last verified live implementation fix branch was `0d5ce16b5a8b1ea90a3313a10894500e40c86205`.

Before complementary runs, load was 21.47/21.20/21.10, GPU0 100% utilized with 6600 MiB occupied. Only two 12-variable paired sparse solves, three one-cell launch-boundary cases, and CPU-only condition reconstruction were added serially, each command capped at 90 seconds. No performance claim.

## Requirement map

| Requirement | Actual evidence | Remaining boundary or correction |
|---|---|---|
| C12-a table indexing | Original checks a,b: exact 22 names/22 host/23 device entries with leading null; empty func2/3. Saved native function probes execute all 22 value/derivative names on CPU/CUDA. | Static list equality is not a future registration guarantee; function probes use the relative-humidity exp/log transform, not an independent direct scalar oracle. Float32 has 11 matching transformed infinities in extrapolated KCl/NaH2S ranges. |
| C12-b twin calls | Original c,d,e are source-text registration/pointer-order/sentinel checks. Saved CPU/CUDA measurements exercise kinetics, TP, UV partition/KKT, phase equilibrium and named functions. | Do not describe static/CPU checks as CUDA execution or claim universal bitwise/1e-15 pointwise parity. The supplied random solve has global relative CPU/CUDA difference 1.794e-13; Jupiter step pointwise relative reaches 2.742e-14. General equilibrium uses a DisortGlobal chunk workspace, not shared memory. |
| C12-c scratch/block size | Original f,g,h reproduce allocation-expression and handwritten arithmetic checks. Saved eight-pair ThermoX deck has 17 species and 200 cells; measured double CPU/CUDA agreement and convergence. New native launch cases cover ns39,55,56. | f does not check nested capacity, pool lifetime/rewinds, allocator-state overhead or float32 padding. h assumes M49152. Actual M101376 changes first failing double ns to56. Predicted ThermoX block is9 threads, from source/formula; no profiler measured the block dimensions. |
| C12-d implicit solve/fallback | Original i,j CPU oracle checks pass. Separate device script runs the exact 64 regular +1 singular cases per dtype on both devices; all646 output components/device finite. Double oracle checks and paired comparison pass1e-12; float32 is INFO. | One diagonal fallback checks minimum-norm least squares in that case, not general pseudoinverse accuracy. K21 remains open/latent. CPU execution alone never substitutes for the explicit CUDA results. |
| C12-e error scale | Saved paired forward_with_rate_constants, jacobian, evolve_implicit and ThermoX.forward in float64/float32; new CPU-only reconstruction adds κ₂ for the same deterministic kinetics systems. Tables below compare global relative error against max κ₂ε and TP ftol. | Global bounds are not per-cell bounds or strict theorems. rc_ddT is None with temperature evolution off. Float32 ftol1e-12 convergence-status sensitivity persists; ftol1e-5 converges on both. No universal claim that output error is bounded by ftol. |
| C12-f sparse QR vs LU | **New assembled atm2d transport matrix** (2 columns×3 layers×2 species), identical rounded A,b on both devices, dense κ₂/oracle/residuals, both dtypes. Saved singular/near-singular runs supplement this. | Earlier manually specified sparse matrices alone did not fulfill assembled-atm2d coverage. New test assembles on CPU and copies A to CUDA; it does not test GPU assembly, large grids or all singularity/rank decisions. |

All six entries now have mapped evidence, with the explicit partial/unverified boundaries above. This is not six unrestricted proofs or a blanket chapter approval.

## Supplied script and oracle audit retained

`check_ch12_twins.py` and `common.py` remain byte-identical to the extracted bundle. The original script exits0 even if it prints FAIL; the separate output validator enforces 17 PASS, 1 INFO, all18 labels and no printed nonfinite tokens. The local unchanged run had exit0, empty stderr, **17 PASS /1 INFO /0 FAIL /0 EXPECTED-FAIL**. Static a–h do not execute CUDA. Numeric i,j,k execute CPU; the separately named device supplement supplies actual CUDA coverage.

Supplied i was1.78e-13; local i2.92e-13 (both PASS at1e-12). Supplied k5.35e-5; local k6.14e-5 (both INFO against original float64 NumPy oracle). Singular j was exactly0 in both outputs. Both supplied and local outputs are packaged distinctly. The supplied output has no verified producing commit identity. Its differing arithmetic is not attributed to a specific compiler/device without evidence.

The device supplement's regular pair global relative differences are1.7941812876295846e-13 (double) and7.898677821431327e-6 (single), over320 components/dtype. maxκ₂=25601.187318119006, giving κ₂ε≈5.685e-12 /3.052e-3. Singular 3-component pair difference is0 for both precisions; single error to the original double oracle is1.1920928910669204e-8. The singular inconsistent system has residual0.7 but normal-equation residual0, as expected. No iteration/branch diagnostic exists for evolve_implicit; branch selection is inferred from constructed zero pivot and source, not instrumented.

## New assembled sparse measurement: C12-f

Command: `timeout 90s ch12-check-validation/run_local.sh integration/check_ch12_spec_complement.py sparse`; raw stdout/stderr and exit0 are packaged. The only stderr is PyTorch's sparse-CSR beta warning.

Domain: seed20261020; 2 columns, 3 layers, 2 species,12 unknowns,40 nonzeros. Vertical faces [0,1e5,2.5e5,4e5], horizontal faces [0,8e4,2e5]; T250, P[1e5,1e4,1e3] per column, initial concentrations0.5e-6. kzz=[[1e5,2e5,3e5],[1.5e5,2.5e5,3.5e5]], kyy=2e5, concentration-form closed/no-flux diffusion. Native in-tree assembly `build_eddy_diffusion_matrix` produces L; its sparse `affine_with_identity` forms A=I−1e5L. Seeded random RHS is rounded once per dtype on CPU. CPU SciPy LU and native CUDA QR receive exactly the same A,b. A is densified only for the small independent NumPy solve/condition calculation and copying to CUDA's SparseSystemMatrix. CUDA entry uses tol0/reorder0 as at the pin.

Here Aerr=max|xCPU−xCUDA|, G=Aerr/max(max|xCPU|,max|xCUDA|), and R=max_i |difference_i|/max(|xCPU_i|,|xCUDA_i|,tiny). κ₂ is NumPy's 2-norm dense condition of the actual rounded matrix cast to double. Every output is explicitly checked finite; exceptions are failures for this regular case. Exploratory acceptance is G≤20κ₂ε and each device's max-error/max|dense oracle|≤20κ₂ε; the factor20 is declared by this supplementary script, not required by the supplied spec or a theorem.

| dtype | κ₂ | κ₂ε | Aerr | G | R | G/(κ₂ε) |
|---|---:|---:|---:|---:|---:|---:|
| double |8.8382475963|1.962485196e-15|5.551115123e-16|8.306266655e-16|1.142562071e-15|0.42325245|
| single |8.8382486448|1.053601342e-6|4.768371582e-7|7.135027724e-7|8.178777442e-7|0.67720374|

All48 scalar outputs (12×2 devices×2 dtypes) finite; both devices returned normally in both dtypes; no finite-mask mismatch. CPU/CUDA max absolute residuals are5.551e-16/2.776e-15 double and2.723e-7/1.495e-6 single. Backward error∞ = ||Ax−b||∞/(||A||∞||x||∞+||b||∞) is7.407e-17/3.703e-16 double,3.633e-8/1.995e-7 single. The assembled no-flux operator's max species volume-weighted conservation imbalance divided by max species volume-weighted absolute tendency is4.869e-17 double /6.535e-8 single.

Reused singular evidence: diag[4,4,0] raises on both CPU and CUDA, both dtypes; CPU says “Factor is exactly singular”, CUDA “cusolver sparse solve detected singularity at row 2”. diag[4,4,1e-14] returns finite on both; its mathematical diagonal κ≈4e14, double pair difference0, single max absolute2,097,152 but global relative7.014e-8. This illustrates conditioning and scale; exact-zero behavior in this diagonal family is not proof that numerical QR/LU always classify arbitrary singular matrices identically.

## Launch complement: C12-c

Command: `timeout 90s ch12-check-validation/run_local.sh integration/check_ch12_spec_complement.py launch`; exit0, stderr empty. Both actually loaded CUDA runtimes report ordinary49152 and opt-in101376 bytes via `cudaDeviceGetAttribute` attributes8/97. Source selects their maximum. Native one-cell implicit systems use double, S=I,J=0,dt=1,r_i=(i+1)/ns; independent exact oracle is r.

| ns | b=32ns²+48ns | CPU | CUDA | Predicted CUDA threads |
|---|---:|---|---|---:|
|39|50544|finite, exact oracle|finite, exact oracle|2|
|55|99440|finite, exact oracle|finite, exact oracle|1|
|56|103040|finite, exact oracle|expected size exception|1 before rejection|

The exact error is `Requested shared memory (103040 bytes) exceeds device maximum (101376 bytes).` This expected resource-limit exception is not a numerical defect or an EXPECTED-FAIL/K-row claim. With M49152 the original algebra's ns39 failure remains correct; it is not this GPU's effective M.

For saved double ThermoX ns17/nr8, summing rounded outer allocations and nested feasible-origin/KKT/LU workspace gives10152 bytes/cell, hence9 threads. The saved successful 200-cell CUDA run exercises a case that cannot fit32 slices in this device's block limit. The block count is source-derived, not profiler-measured. No allocation-overflow/memory-sanitizer coverage or float32 allocator proof is claimed.

## C12-e: saved measurements against condition and stopping scales

`conditioning` reconstructs only CPU rates/J for the exact saved inputs: seed20261020,64 cells/deck/dtype,dt10; Kessler and pressure-switch T80..120, Jupiter180..220; P10^3.5..10^4.5 with predecessor/exact/successor1e4, concentrations random[0,1e-3], Kessler vapor set to saturation×linspace(.5,1.5). No paired campaign rerun. κ₂ is computed from A=I/10−S J using rounded CPU S,J cast to double; it does not incorporate CUDA-vs-CPU input-J perturbation. G below is the **saved** max|CPU−CUDA|/max(max|CPU|,atol), over all cells/components, not per-cell maxima normalized by each cell.

| Deck/dtype | maxκ₂ | maxκ₂ε | saved step G | G/(maxκ₂ε) |
|---|---:|---:|---:|---:|
|Kessler double|6.869241794|1.525278080e-15|1.334812567e-16|0.08751|
|pressure-switch double|20.13214638|4.470234489e-15|6.332498084e-16|0.14166|
|Jupiter double|1.144487891|2.541273615e-16|9.292640803e-16|3.65669|
|Kessler single|6.869230684|8.188761096e-7|1.039102055e-6|1.26894|
|pressure-switch single|20.13214638|2.399938867e-6|3.399732373e-7|0.14166|
|Jupiter single|1.144487896|1.364335890e-7|3.991156396e-7|2.92535|

Across these three decks, saved direct rate/kf/J global relative differences range0..3.826ε double and0..4.093ε single. Full absolute and pointwise-relative maxima are in `saved-summary.out`; the pointwise metric uses max(|CPU|,|CUDA|,atol), atol1e-12 double /1e-6 single. Original acceptance was |difference|≤atol+rtol|CPU| with rtol1e-10 /1e-4, plus masks; that tolerance is retained rather than retroactively replaced by a universal1e-15 threshold. Rate zero/positive masks agree. Reconstructed condition comparison supports an order-of-magnitude interpretation, not a rigorous uniform one-epsilon bound.

ThermoX saved domain: eight vapor/condensate pairs plus dry gas,200 temperatures250..400K,P1e5, each initial vapor fraction.02, dry remainder, max_iter50. Fractions' global G=1.321694077e-16 in double at ftol1e-12 (G/ftol1.322e-4),1.419157951e-7 in single at either ftol1e-12 or1e-5 (ratios1.419e5 /0.01419). All3400 fractions/device finite in each run. Double status/cloud masks agree; all200 converge. Single tight ftol has CPU15 versus CUDA13 failed cells,22 success-mask differences and44 diagnostic differences; cloud masks agree. Single relaxed ftol has all200 converge with exact diagnostic/cloud agreement. The isolated tight-ftol cell had fraction difference3.725e-9 and CPU11 versus CUDA−2050; at ftol1e-5 both11. This remains **measured tolerance sensitivity**, not an established implementation defect.

The tolerance operates on solver residual/iteration criteria, so “output differences bounded by ftol” needs qualification, especially in float32 or near ill-conditioning. Large gain disagreements at failed tight-ftol exits remain in raw saved logs; do not quote converged-output bounds for them. Pairwise vapor+condensate conservation max error was1.735e-17 double /7.451e-9 single. No absent-gas K15 CUDA campaign or extreme-cancellation test was added.

## Source citations and issue mapping

Every implementation citation below is at full pin `0d9f67f97d841147e23283d2dcdab302238d2c45`:

- [Function table leading null](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/func_table.cu#L9), [table lookup](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/utils/user_funcs.cu#L26).
- [Device shared-memory selection](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/loops.cuh#L18), [block sizing/guard](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/loops.cuh#L105), [rounded allocator](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/utils/alloc.h#L75), [TP nested size](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/utils/alloc.h#L141).
- [Implicit size](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_impl.h#L24), [implicit system/fallback](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_impl.h#L65), [CPU host-bump pool](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_dispatch.cpp#L59), [actual CUDA per-cell call](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_dispatch.cu#L15).
- [General equilibrium second launch path](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/equilibrium/equilibrium_dispatch.cu#L38) includes pmem state and DisortGlobal; it must not inherit the shared-memory sizing derivation unmodified.
- [atm2d transport assembly](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/python/atm2d/transport.py#L81), [sparse backward-Euler assembly](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/python/atm2d/matrix.py#L135), [CPU factorization](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/python/atm2d/matrix.py#L280), [device solve dispatch/tol/reorder](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/python/atm2d/solver.py#L25), [cuSOLVER QR/singularity check](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/math/sparse_solver.cu#L135).

The captured live [issue54](https://github.com/UCzhangxi/kintera/issues/54) body verifies K21 (pseudoinverse100-rotation/absolute threshold) and K25 (>4GiB offset indexing, GPU-unverified). Separate spec S12-1 matches K25 by location and mechanism; this is a **source-only suspect mapping**, not an EXPECTED-FAIL result. No C12 EXPECTED-FAIL line exists in supplied/local output, so that output-to-K mapping remains empty. Small checks do not cover K25 and do not settle K21. No defect was claimed/owned/fixed here.

## Integration handoff and exact commands

The package is ready in `/home/tianhaol/fridica-snapy/worker2/ch12-check-validation/integration/`. Copy it as a chapter-local subtree to `doc/tech-report/derivation-checks/ch12/`, preserving names and provenance. Do not overwrite another chapter's common.py. It contains unchanged supplied scripts, distinct supplied/local outputs, the CUDA oracle supplement, new three-mode complement, copied saved preparation evidence and audit reports, commands/environment wrappers and a SHA256 manifest. Original build binaries are not copied; all checks require a verified exact-pin installation.

For Claude worker-2ac5885a-9c2a-442f-9d3c-c5e7799148cc: I own these numerical records; chapter integration is ready for your explicit acceptance. Done means the chapter quotes the correct local output and maps all six entries with the boundaries above, corrects the shared/global workspace attribution and hardware-dependent launch threshold, and preserves the float32 tolerance-sensitivity distinction. No acceptance or chapter commit has been observed by this worker. No new validation commit exists; original implementation pin and saved report head are the full SHAs above.

Exact executed commands, redirects, wrapper environment, exit files, identity and resource snapshots are included under `spec-update/` and `provenance/`. New numerical commands all exited0; sparse stderr contains only the CSR warning, other numerical stderr empty. A saved-log summarizer initially rejected an existing native diagnostic line as non-JSON; it was corrected to select JSON records and rerun successfully, without rerunning any model. That was a packaging parser failure, not a numerical failure.

To reproduce only the new work after integration, set KINTERA_REPO and KINTERA_WT to verified pin source, PYTHONPATH to its verified installation, CH12_SAVED to the packaged saved-preparation directory, and use a suitable CUDA-enabled interpreter with one CPU/BLAS thread and CUDA_VISIBLE_DEVICES=0:

```sh
python check_ch12_spec_complement.py sparse
python check_ch12_spec_complement.py launch
python check_ch12_spec_complement.py conditioning
```

Set bytecode/cache/temp outputs inside the caller's assigned writable folder. The exact original absolute-path wrapper is retained as provenance; adapt paths without changing the numerical inputs. Do not rerun the full saved campaign just to integrate these files.
