> Update: the separate six-entry C12 specification has now arrived. The missing-spec conclusion below is historical; see [six-entry mapping and complementary measurements](spec-update/report.md).

# Chapter 12 supplied-check validation

I accept bounded ownership of chapter 12 check-script validation for Tianhao, home thread `C0C2D3PCW20:1792350030.238029`. Validation and a chapter-scoped integration package are complete. No implementation change, new commit, GitHub write, external post, other-chapter execution, or edit to Claude's checkout/shared helper was made. The completed 102-comparison preparation campaign was not rerun.

## Bundle and specification finding

I read the full attachment, including all other-chapter blocks for inventory/context. It is 80,380 bytes / 1,394 lines, SHA256 `e997abfcb04ba59a4f004af3e1317d063bec2455ad9c4a714e556ccd026290d9`. The only extracted blocks are:

| Block | Attachment location | SHA256 |
|---|---|---|
| `common.py` | lines 5–55 | `424bf765e0e718bb45fce7e848668df24399267fcd24a20f4cf63f1e8a63a43e` |
| `check_ch12_twins.py` | lines 847–1043 | `0eb92e33f391f4f6fc79c2713b82714e0d08a7b5607cccd124953871dfa11319` |
| `check_ch12_twins.out` | lines 1333–1355 | `98b47efb81d238655755e7ab6e54cf5423c50b54338d5d2f31ab222dbe2447ef` |

Sources: [attachment](../../data_in/F0CBNQV9RUG/round2_checks_bundle.md), [extraction manifest](manifest.json), [extractor](extract.py). The script's direct dependencies are `common.py`, NumPy, PyTorch, Kintera, Python standard library and the implementation source files it reads. `common.py` also defines unrelated helper functions, but the C12 script imports only `version_line`, `kintera`, `torch`, `WT`. No other chapter script is needed.

**The six C12 specification entries are not included.** This file contains file blocks for chapters 7, 8, 10, 12 and 14 and their outputs; it has no six-entry specification, requirement IDs or specification-to-check mapping. The supplied C12 script has checks `(a)`–`(k)`, with eight `(f-...)` subchecks. These cannot be relabeled as six specification entries. Coverage against the six unspecified requirements is therefore unassessable, not six passes or six failures. The measured check coverage below can be mapped once the actual entries arrive.

## Pin and environment verification

Implementation source is unchanged at **`0d9f67f97d841147e23283d2dcdab302238d2c45`**. `git status --short` reports only the pre-existing untracked `build` symlink. The existing worker2 exact-pin build and historical worker1 Python environment were reused read-only. `results/identity.json` rechecks loaded-library paths/hashes against preparation; all saved binary hashes match. The original source and shared environment were not modified.

- Python 3.11.13; NumPy 2.4.6; PyTorch 2.10.0+cu128; CPU/BLAS threads=1.
- GPU 0 only: RTX 5090, compute capability 12.0, driver 615.71.09.
- Existing build: Release, GCC 11.5.0, CUDA ON, nvcc 12.9, architecture 120; process has the previously recorded mixed CUDA 12 and CUDA 13.2 runtime linkage. This is not a new build or a pure-CUDA-12.9 claim.
- Loaded native CPU SHA256 `950280d238fc79800d88c00919b281905121559b585a4c57590791129f08893c`; CUDA `44a91be2a89b13514d0710e5cc2623441626b06cb44edc60b2a3c4465300bc21`; extension `eb1b81569889eb405463dd0565353157b13f439d5cde7c65953c2b10d7d73dd3`.
- Initial load from `uptime`: 21.14/21.05/21.03; GPU 0 utilization 100%, 6600 MiB used. Later snapshot remains 100% with load 21.21/21.15/21.07. No timing claim. Only 64 regular cells and one singular cell per dtype/device were used in the device supplement, serially, without building or scheduling anything.

Evidence: [run wrapper](run_local.sh), [fresh identity](results/identity.json), [package metadata](results/metadata.json), [GPU snapshot](results/gpu.txt), [load snapshot](results/load.txt). Metadata timestamp is `2026-10-21T00:53:51.414150+00:00` (October 20 local).

The shared helper prepends `$KINTERA_WT/_pyinstall`, but does not enforce a git or binary pin. On this machine that path is absent; the explicit `PYTHONPATH` selects the verified installation. The printed version line is not itself proof of the build identity. Preserve the identity record when using these results.

## Pre-execution script/oracle audit

The original script was audited before running it and is copied byte-for-byte in the package. It reads source text, constructs small tensors, and prints checks; it has no external writes/builds/network operations. Shared dependency `common.py` is also unchanged.

All implementation citations below refer to full pin `0d9f67f97d841147e23283d2dcdab302238d2c45`:

| Check | What it establishes at this pin | Coverage limit |
|---|---|---|
| a,b | Parsed `func1` names/host/device lists match (22/22/23); func2/3 are empty on host and nullptr-only on device. [Host tables](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/func_table.cpp#L10), [device tables](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/func_table.cu#L9). | Source-list equality, not compiled function-pointer evaluation or a test of registration errors. |
| c | Eight stubs in four listed translation-unit pairs have textual CPU and CUDA registrations. [Thermo registrations](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/thermo/thermo_dispatch.cpp#L182). | A regex over selected files, not complete repository discovery or link/runtime registration proof. |
| d | Eight listed twins have the same parsed pointer names/data indices. | Regex ignores pointed-to types, offsets/strides, remaining arguments and backend semantics. It does not prove equivalent execution. General equilibrium explicitly uses [DisortGlobal/gpu_chunk_kernel](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/equilibrium/equilibrium_dispatch.cu#L38). |
| e | Exact inline-name sentinel replacement occurs twice in each thermo driver file. | Text-count guard only; does not execute inline-vs-named equivalence. |
| f | Seven selected direct allocation sequences match selected `bump` size expressions, plus partition allocation expressions match a literal expected list. [Size functions](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/utils/alloc.h#L109). | Parsing stops before `return`; nested workspace additions, pool-state overhead, alignment, lifetime/rewind and capacity are not checked. The partition check does not actually parse its size function. |
| g | Handwritten double-precision arithmetic equals `32 ns² + 48 ns` for ns=1..59. This agrees with the inspected [implicit workspace function](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_impl.h#L24) plus [psolve workspace](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/utils/alloc.h#L94). | It does not call/parse the native size function here; both arithmetic sides are handwritten. No float32 padded-size validation. |
| h | Fixed M=49152 arithmetic gives 32 threads at ns=6, 25 at ns=7, fit at 38, overflow at 39. | No launch or error is actually triggered. M is an illustrative assumption, not this GPU's measured limit. Actual code queries [device shared-memory limits](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/loops.cuh#L18) and uses them in [gpu_mem_kernel](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/loops.cuh#L90). |
| i | CPU implicit step against independent NumPy solve of `(I/dt − S J) delta = S r`, seed 12, ns=5, nr=4, 64 cells, dt=.3, double. [Per-cell implementation](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_impl.h#L65). | Synthetic random S is not a chemical conservation deck. Metric is global-scale error, not a per-component bound. |
| j | The exactly singular diagonal system returns `[0,-.8,0]`, equal to NumPy's minimum-norm least-squares result. [Exact-zero LU test](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/math/core.h#L189), [fallback](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_impl.h#L77). | RHS has a nonzero null-row component, so zero equation residual is impossible. NumPy pinv cutoff differs from the implementation's eigenvalue cutoff generally; this simple spectrum `{0,.5,1}` avoids that ambiguity. Does not validate general pseudoinverse behavior. |
| k | Float32 CPU result compared to the original float64 NumPy oracle, INFO. | Includes input/inverse-dt quantization and solver arithmetic; no float32 tolerance or CUDA result supplied. It cannot set a universal CPU/CUDA error bound. |

The same per-cell implicit function is called by the [CPU HostBump driver](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_dispatch.cpp#L49) and [CUDA shared-memory driver](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_dispatch.cu#L15). The supplementary script uses this actual CUDA path for i/j/k; static checks a–h are not relabeled as CUDA runtime tests.

**Exit/nonfinite handling:** supplied `ok()` only prints PASS/FAIL; numerical FAIL does not cause nonzero exit. Its i/j comparisons reject NaN by the `<` test, but no explicit finite-mask accounting exists, and k always prints INFO. The package adds a separate output validator requiring all 18 expected labels, 17 PASS + 1 INFO, and no printed NaN/inf. The numeric device supplement asserts finite outputs/oracles, synchronizes CUDA, and exits nonzero on failed double-precision comparisons. Float32 remains INFO, not EXPECTED-FAIL. `evolve_implicit` returns no iteration/status/branch diagnostic; normal return and finiteness are recorded, while fallback selection is inferred from the constructed exact-zero pivot and inspected source, not instrumented.

## Locally reproduced output versus supplied output

The unchanged supplied script completed with exit **0**, empty stderr, **17 PASS / 1 INFO / 0 FAIL / 0 EXPECTED-FAIL**. The output validator also exits **0**. All static lines and the singular result reproduce; version location and two numerical values differ:

| Line | Supplied output | Local unchanged script |
|---|---|---|
| i: `max|d-ref| / max|ref|`, double | `1.78e-13`, PASS | `2.92e-13`, PASS; tolerance `1e-12` |
| j: maximum absolute difference, singular double | `0`, PASS | `0`, PASS; tolerance `1e-12` |
| k: global relative error vs original double oracle | `5.35e-05`, INFO | `6.14e-05`, INFO |

The bundle calls its outputs “committed”; no output commit identity is supplied there. They are retained as **supplied evidence**, not claimed as our execution or verified historical commit. Differences in build/platform arithmetic are a possible explanation, not a tested attribution.

Fresh supplement: **exit 0**, empty stderr, 6 double PASS measurements, 6 float32 INFO measurements. Inputs are generated using the supplied NumPy seed/sequence and cast once on CPU before copying to CUDA. It measures 320 regular output components and 3 singular components per dtype/device, all finite (646 components/device over both dtypes), with zero finite-mask mismatches. Maximum regular-system condition number is `25601.187318119006`.

| Case/metric | CPU | CUDA | CPU–CUDA |
|---|---:|---:|---:|
| Regular double, global relative to double NumPy oracle | `2.924739371725018e-13` | `1.1305580840949085e-13` | `1.7941812876295846e-13` |
| Regular double, maximum absolute difference to oracle | `1.0396661309641786e-10` | `4.0188297134591267e-11` | `6.377831596182659e-11` |
| Regular float32, global relative to original double oracle (INFO) | `6.139094636438168e-5` | `5.349269106448288e-5` | `7.898677821431327e-6` |
| Regular float32, maximum absolute difference (INFO) | `0.021822829172378988` | `0.019015211984878988` | `0.0028076171875` |
| Singular double, maximum absolute difference | `0` | `0` | `0` |
| Singular float32, maximum absolute difference to double oracle (INFO) | `1.1920928910669204e-8` | `1.1920928910669204e-8` | `0` |

For oracle comparisons, relative denominator is `max|oracle|`. For the pair column, denominator is `max(max|CPU|,max|CUDA|)`. Double regular and paired relative tolerance is `1e-12`; double singular oracle tolerance is absolute `1e-12`. All values are over the full listed component domain. Float32 has no pass/fail tolerance beyond requiring finite outputs. Residuals and normal-equation residuals are preserved in the output; for the singular double case `max|A delta-b|=.7` and `max|Aᵀ(A delta-b)|=0`, as expected for the inconsistent least-squares problem. There is no chemical conservation invariant for this synthetic random stoichiometry.

Files: [supplied output](supplied/check_ch12_twins.out), [local CPU output](results/check_ch12_twins.cpu.out), [literal diff](results/supplied-vs-local.diff), [device supplement output](results/check_ch12_numeric_devices.out), [exit/status records](results/metadata.json). The diff command exits 1 because the output text differs; this is not a failed numerical check.

## Issue #54 mapping and retained limits

Read-only live `gh issue view 54 -R UCzhangxi/kintera --json title,state,assignees,body,comments` confirms OPEN, no issue-level assignees. The captured body/comments are in `issue54.json`.

**There are no C12 EXPECTED-FAIL lines in the supplied or reproduced output, so the C12 EXPECTED-FAIL → K-row mapping is empty.** Other chapters' S-labels are outside this extraction and were not relabeled. Related boundaries verified in the live issue:

- [K21](https://github.com/UCzhangxi/kintera/issues/54): pseudoinverse rotation cap and absolute stopping threshold; the one simple diagonal fallback PASS does not resolve it. Pinned [psolve implementation](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/math/psolve.h#L47).
- K25 in the same issue: >4 GiB CUDA offset indexing, explicitly unverified on GPU. These tiny batches do not exercise it. No EXPECTED-FAIL was fabricated for it.

The previously measured float32 TP `ftol=1e-12` status split remains **measured tolerance sensitivity**, not an established defect. No new saturation probe or prior campaign rerun was needed here. K15 absent-gas CUDA and extreme cancellation remain untested; this implicit-solve check provides no K15 evidence. No performance conclusion is supported under the observed contention.

## Integration handoff for Claude worker-2ac5885a-9c2a-442f-9d3c-c5e7799148cc

The package is ready at:

`/home/tianhaol/fridica-snapy/worker2/ch12-check-validation/integration/`

Suggested destination: `doc/tech-report/derivation-checks/ch12/`. Copy the eight files together. This keeps the unmodified bundled `common.py` chapter-local and avoids overwriting another chapter's helper. The package contains:

- `common.py`, `check_ch12_twins.py`: byte-identical extracted originals.
- `check_ch12_twins.supplied.out`: sender-supplied historical output.
- `check_ch12_twins.out`: locally reproduced original-script output.
- `check_ch12_numeric_devices.py`, `.out`: clearly separate bounded CPU/CUDA supplement.
- `validate_ch12_output.py`, `.out`: exit-code enforcement for original textual results.

The chapter should quote locally reproduced numbers as local and retain provenance for supplied numbers. Use the coverage table above to qualify “PASS”: allocation-expression equality is not allocator safety, fixed-M algebra is not an actual launch, matching pointer order is not runtime parity. Do not assert the six entries are covered until their text is available. The supplied C12 result has no EXPECTED-FAIL line to annotate with a K row.

I retain responsibility for these validation records. Claude owns chapter integration once explicitly accepted; completion means the chapter references the correct local output, retains the limitations, and does not overwrite shared helpers. No handoff acceptance has been received in this session. No new commit exists; all results are tied to implementation pin `0d9f67f97d841147e23283d2dcdab302238d2c45`. The preparation report checkout remains at `0d525973c0b3659adaae91c22c251b4640a32126` and was not edited.

## Exact execution commands

From `/home/tianhaol/fridica-snapy/worker2`:

```sh
ch12-cpu-cuda/run.sh /home/tianhaol/fridica-snapy/worker2/ch12-check-validation/extract.py
ch12-check-validation/run_local.sh /home/tianhaol/fridica-snapy/worker2/ch12-cpu-cuda/identity.py > ch12-check-validation/results/identity.json
ch12-check-validation/run_local.sh supplied/check_ch12_twins.py > ch12-check-validation/results/check_ch12_twins.cpu.out 2> ch12-check-validation/results/check_ch12_twins.cpu.err
# exit 0, saved separately in results/check_ch12_twins.cpu.exit
ch12-check-validation/run_local.sh integration/check_ch12_numeric_devices.py > ch12-check-validation/results/check_ch12_numeric_devices.out 2> ch12-check-validation/results/check_ch12_numeric_devices.err
# exit 0, saved separately in results/check_ch12_numeric_devices.exit
ch12-check-validation/run_local.sh integration/validate_ch12_output.py results/check_ch12_twins.cpu.out > ch12-check-validation/results/validate_ch12_output.out 2> ch12-check-validation/results/validate_ch12_output.err
# exit 0, saved separately in results/validate_ch12_output.exit
ch12-check-validation/run_local.sh package_metadata.py > ch12-check-validation/results/metadata-validation.out
# exit 0; asserts unchanged binary identities and exact extracted source copies
```

`run_local.sh` selects the existing interpreter, exact installation, source pin directory, GPU 0, one CPU/BLAS thread, disabled bytecode writes, and cache/temp directories within this task folder. For another checkout use its own equivalent environment and verify the pin/build first; do not use the supplied version string as the identity check.
