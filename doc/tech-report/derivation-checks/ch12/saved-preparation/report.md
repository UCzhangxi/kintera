# Chapter 12: paired CPU/CUDA measurements

I accept ownership of the chapter 12 numerical measurements for Tianhao in home thread `C0C2D3PCW20:1792350030.238029`. This completes the bounded evidence preparation assignment, while the C12 derivation specification and independent derivation review remain pending. No Slack, upstream, issue, PR, branch push or implementation write was performed. All new files are in worker2. The source checkouts and reused environment/build were not modified.

## Refs and runtime identity

Live ref verification at `2026-10-21T00:30:46Z` (October 20 local):

| Item | Actual value |
|---|---|
| Report repository/ref | `UCzhangxi/kintera:refs/heads/tech-report` |
| Report head | `0d525973c0b3659adaae91c22c251b4640a32126` |
| Report tree | `2d0d3294b6201bdac930d95bf02722668d583f98` |
| Report head parent | `f97ca7e4c0427cfb6046e8f0bc17d9b93c362404` |
| Actual report/main merge base and fork main | `4dc613d04f24621b3119d343c5c7c9b93628895b` |
| PR #85 | MERGED; head `8d1180c23a8bc717299c5120962d9ffd5c771ddc`, ref `linfeng/ch04-ch05-followup`; reported API base `d15c135cadc4ce8358e6a455b214041ede54d66c`, ref `tech-report`; merge `0d525973c0b3659adaae91c22c251b4640a32126` |
| Implementation pin | `0d9f67f97d841147e23283d2dcdab302238d2c45` |
| Upstream fetched ref | `chengcli/kintera:refs/heads/main`, exactly the implementation pin |
| Live staging ref | `UCzhangxi/kintera:refs/heads/fix/thermo-20261019` = `0d5ce16b5a8b1ea90a3313a10894500e40c86205` |
| Staging/main merge base | `4dc613d04f24621b3119d343c5c7c9b93628895b` |
| Authorized fork ownership | GitHub reports owner `happysky19`, fork `happysky19/kintera`, parent `chengcli/kintera`; read only |

Sources: exact commands in [commands.txt](commands.txt); saved GitHub responses and git outputs in `live-refs.txt`, `pr85.json`, `report-head.txt`, `report-merge-base.txt`, `fix-base.txt`, `fork.json` and `issue54.json`. The report checkout is detached and clean. The reused implementation checkout has no tracked differences; its only untracked entry is the pre-existing `build` symlink.

Chapter location: [12-gpu.qmd at the verified report head](https://github.com/UCzhangxi/kintera/blob/0d525973c0b3659adaae91c22c251b4640a32126/doc/tech-report/book/chapters/12-gpu.qmd#L1). Five included sections cover build, dispatch, kernels, device functions and sparse solve. The sparse section is still a draft with TODOs: [source](https://github.com/UCzhangxi/kintera/blob/0d525973c0b3659adaae91c22c251b4640a32126/doc/tech-report/book/chapters/12-gpu/_sparse-solver.qmd#L13).

Runtime: dungeon3, GPU 0 only, RTX 5090, compute capability 12.0, driver 615.71.09; Python 3.11.13; PyTorch 2.10.0+cu128; CPU/BLAS threads restricted to one. The existing Python environment supplies dependencies; `PYTHONPATH` explicitly selects worker2's saved Kintera 2.6.5 exact-pin installation. Build logs record the full pin before compilation, Release, CUDA ON, GCC 11.5.0, nvcc 12.9 and architecture 120. Both loaded native libraries are byte-identical to those in that build:

| Binary | SHA256 |
|---|---|
| Python extension | `eb1b81569889eb405463dd0565353157b13f439d5cde7c65953c2b10d7d73dd3` |
| CPU library | `950280d238fc79800d88c00919b281905121559b585a4c57590791129f08893c` |
| CUDA library | `44a91be2a89b13514d0710e5cc2623441626b06cb44edc60b2a3c4465300bc21` |

`identity.py` captures `/proc/self/maps`, exact loaded paths and hashes. The process loads CUDA 12 runtimes through torch/dependencies and CUDA 13.2 through the Python extension linkage; this is the measured mixed-runtime configuration, not a claim of a pure CUDA-12.9 process. No new build or package installation was needed. [identity.json](identity.json), [build-hashes.txt](build-hashes.txt).

Writability was checked in the assigned folder. Initial load average was 21.07/21.02/21.00 and both visible GPUs reported 100% utilization; the later GPU-0 snapshot still showed 100%, 6600 MiB used, with host load 21.41/21.18/21.06. Only GPU 0 was used. No scheduler job, build campaign or timing benchmark was started. Small probes ran serially; the first kinetics retry was started as the preceding small workspace process was finishing. Results establish numerical observations under contention, not performance. [gpu.txt](gpu.txt), [load.txt](load.txt).

## Existing checks and reusable additions

Existing chapter scripts are `batch_probe.py`, `device_probe.py` and `time_dispatch.py`; no committed chapter-specific paired accuracy check was found. The timing script advances one generator inside the device loop, drawing different CPU/CUDA inputs: [report source, lines 58–70](https://github.com/UCzhangxi/kintera/blob/0d525973c0b3659adaae91c22c251b4640a32126/doc/tech-report/src/kintera_report/ch12/runs/time_dispatch.py#L58). This is a source finding, not a measured performance defect. The new probes generate/cast inputs once on CPU, then copy those same tensors to CUDA.

Relevant in-tree checks/decks inspected:

- [Workspace tests](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/tests/test_cuda_workspace.py#L27): eight vapor/cloud pairs, TP and two UV solvers; default dtype double, `ftol=1e-12`, 200 temperatures, comparison `rtol=1e-10, atol=1e-14`.
- [Kessler deck](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/tests/test_evaporation_kessler.py#L38), [pressure-switch deck](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/tests/test_coagulation_pressure_switch.py#L24), and [Jupiter deck](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/tests/jupiter.yaml#L1).
- [Native-curve tests](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/tests/test_reaction_equilibrium.py#L51), including [catalogue reference evaluation](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/docs/reaction_validation.py#L192).
- [Sparse paired test](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/tests/test_atm2d.py#L726), plus cache/dense-reference tests.
- [General equilibrium NASA9 example test](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/tests/test_equilibrium.py#L49).

Reusable local files: [run.sh](run.sh) selects the interpreter/build/device and confines caches to worker2; [probe.py](probe.py) measures kinetics, workspace, function tables and sparse solve; [equilibrium_probe.py](equilibrium_probe.py) measures real-deck TP and NASA9 equilibrium; [one_cell.py](one_cell.py) reproduces the localized discrepancy; [check_evidence.py](check_evidence.py) checks the saved agreement evidence and preserves the expected disagreement. [commands.txt](commands.txt) records exact executed commands, including the full pytest selection.

The probes print JSON records plus occasional native diagnostic lines; parse only lines starting with `{`. All numerical inputs are deterministic. Kinetics and sparse RNG seed is `20261020`; other probes use explicit grids. An initial harness attempt incorrectly assumed optional `rc_ddT` was a tensor; it was corrected to record zero elements when the API returns None, before collecting the kinetics results. Temperature evolution is disabled in these decks: no `dk/dT` validation is claimed. An initial PyTorch kernel-cache warning was resolved by setting `PYTORCH_KERNEL_CACHE_PATH` in the assigned folder; it was not a numerical failure.

## Metrics and domains

For finite CPU/CUDA pairs `a_i,b_i`, report `A=max |a_i-b_i|`; `R=max |a_i-b_i| / max(|a_i|,|b_i|,atol)` (pointwise symmetric relative error); and `G=A/max(max|a|,atol)` (global CPU-scale relative error). All three are in the raw records. `R` can be large for tiny outputs while the absolute comparison still passes.

The declared exploratory acceptance rule is `|a-b| <= atol + rtol*|a|`: double `(atol,rtol)=(1e-12,1e-10)`, single `(1e-6,1e-4)`. These are conservative diagnostic thresholds, not C12 requirements or physical-accuracy guarantees. The independent in-tree tests retain their original, tighter tolerances. NaN masks, finite masks and signed infinities are compared separately; nonfinite entries are excluded from A/R/G and explicitly counted. Exact iteration counts, success masks and cloud/zero-rate masks are separately compared.

- Kinetics: 64 cells per deck per precision, one `dt=10 s` implicit step. Kessler and pressure-switch T in 80–120 K; Jupiter T in 180–220 K. P in `10^3.5–10^4.5 Pa`, with the first three cells set immediately below, exactly at and immediately above `1e4 Pa` in the chosen dtype. Concentrations initially uniform-random in `[0,1e-3)`; Kessler vapor is replaced by `c_sat(T)*linspace(0.5,1.5,64)` to cross activation. Other concentration components remain sampled. Kinetics species excludes the inert dry entry; all API sizes come from the loaded options.
- Workspace: the unmodified eight-pair deck, T=250–400 K on 200 points, P=`1e5 Pa` for TP; UV rho=`1 kg/m³`, initial vapor mass fractions 0.02 each, and internal energy computed once on CPU and copied unchanged. Float32 is a dtype extension of the in-tree double test. A separate float32 run changes only `ftol` to `1e-5`.
- Jupiter TP: 45 states, T `{130,160,190,220,250,273.16,290,310,350} K` × P `{1e2,1e3,1e4,1e5,1e6} Pa`; vapor fractions H2O=.02, NH3=.005, dry remainder; untouched default 10-iteration budget.
- NASA9: in-tree example, nine T values 3000–5000 K, P=`1e5 Pa`, initial moles `[.6,.2,.2]`; LogK generated once on CPU per dtype and copied, so this isolates the equilibrium solver rather than independently comparing the NASA9 evaluator.
- Function tables: all 11 names and all 11 `_ddT` entries, each on 31 T points from 100–1500 K, plus dtype-nextafter triplets around five switches (273.16,195.4,187.63,212.8,90.67 K). Total 712 values per precision/device. These are arithmetic stress domains, not empirical fit validity ranges. Zero stoichiometry through `relative_humidity` yields `exp(-f(T))`; the probe recovers `f=-log(RH)`. Consequently derivative measurements include exp/log roundoff, and extremes can overflow the RH transform. This is not a direct scalar oracle or an autograd test.
- Sparse: the 12×12 in-tree matrix, a synthetic diagonally dominant 63×63 tridiagonal matrix, a singular 3×3 diagonal matrix and a nonsingular 3×3 diagonal matrix with last diagonal `1e-14`, each in both precisions. CPU uses cached SciPy factorization; CUDA uses native cuSOLVER with tol=0, reorder=0: [dispatch](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/python/atm2d/solver.py#L25), [native solve](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/math/sparse_solver.cu#L135).

## Measured agreement and disagreement

**102 nonempty comparisons in the ordinary/relaxed runs meet the declared tolerance and have matching finite/NaN/inf masks.** This includes Jupiter outputs with reported failures; it is explicitly not 102 proofs of convergence. Eight targeted in-tree tests pass (`8 passed, 1 warning`, sparse-CSR beta warning). Commands: `run.sh check_evidence.py` and the full pytest command in `commands.txt`; outputs [check-evidence.txt](check-evidence.txt), [pytest.txt](pytest.txt).

| Path | Double result | Single result |
|---|---|---|
| Kessler step, 64 cells | A `5.4210108624e-20`, R `1.5841808035e-15` | A `4.2200554162e-10`, R `3.6778435389e-6` |
| Pressure-switched step, 64 cells | A `5.4210108624e-19`, R `8.5567317649e-16` | A `2.9103830457e-10`, R `4.7329794958e-7` |
| Jupiter step, 64 cells | A `6.7762635780e-20`, R `2.7418872855e-14` | A `2.9103830457e-11`, R `4.0358827391e-6` |
| Workspace TP fractions, 200 | A `1.1102230246e-16`, all converge, exact diag/cloud agreement | At original ftol, A `1.1920928955e-7`; failures and gains disagree (below) |
| Workspace UV partition fractions, 200 | A `1.9081958236e-16`, all converge, exact diag/cloud agreement | A `5.3085386753e-8`, all converge, exact diag/cloud agreement |
| Workspace UV-KKT fractions, 200 | A `9.3675067703e-17`, all converge, exact diag/cloud agreement | Original ftol: 90 failed cells per device; A `4.5169144869e-8` |
| Jupiter TP fractions, 45 | A `6.9388939039e-18`; 19 failed per device | A `9.7788870335e-9`; same 19 failed per device |
| NASA9 moles, 9 | Bit-identical outputs/diagnostics; all status=0 | A `2.9802322388e-8`; all status=0, exact iteration agreement |
| Function-table transformed values, 712 | All finite; largest A `1.4210854715e-14` | 701 finite per device, identical nonfinite masks; largest finite A `1.4901161194e-7` |
| Sparse, ordinary 12/63 matrices | Largest A `3.8857805862e-16` | Largest A `2.9802322388e-7` |
| Sparse, near-singular diagonal | Identical finite solution | A `2097152`, R `7.0136526359e-8`; large magnitude solution, not a small absolute error |
| Sparse, exactly singular | Both raise; CPU “Factor is exactly singular”, CUDA singularity at row 2 | Both raise the same respective errors |

Rates, Jacobians, intermediate rate constants and all detailed maxima/counts are preserved in the raw result files. Kinetics zero-rate masks match for all decks and both precisions. Float32 transformed native-function nonfinites are three KCl points and eight Na-H2S points, with identical signed-infinity masks; no device-specific nonfinite was observed. The transform and sampled fit extrapolation preclude calling these a function-table defect.

Conservation checks: for the 1:1 Kessler/pressure-switch reactions, `max|sum_species delta c|` is at most `7.5894152074e-19` double and `4.6566128731e-10` single. Workspace vapor+cloud fraction sums are conserved to at most `1.7347234760e-17` double; at relaxed single tolerance the maximum is `7.4505805969e-9`. The failed UV-KKT single run reaches `3.7252902985e-8`. NASA9 elemental residuals `max|(m_out-m_in)·a_element|` are H≤`3.3306690739e-16`, O≤`1.1102230246e-16` double; H≤`1.1920928955e-7`, O≤`5.9604644775e-8` single. Sparse residuals are `max|A x-b|`, computed in CPU double from the returned values; per-device values are in `sparse*.jsonl`. No independent energy oracle or long-trajectory conservation claim is made.

### Localized float32 candidate for coordination

The single-cell reproducer uses exactly the workspace test's deck and initial fractions, with module and inputs converted to float32. T=`250.75376892089844 K`, P=`100000 Pa`, eight vapor fractions `.02`, dry remainder, no initial cloud, `max-iter=50`, `ftol=1e-12`:

```sh
ch12-cpu-cuda/run.sh one_cell.py
```

CPU reports diag=11; CUDA reports diag=-2050. Fractions are finite and differ by at most `3.7252902985e-9`, but gains differ by `5110.3115234375`, R=1, with 15/64 gain entries exceeding the comparison tolerance. Changing only ftol to `1e-5` gives diag=11 on both; gain A=`0.0078125`, R=`1.5287717714e-6`, no tolerance failures. [one-cell.jsonl](one-cell.jsonl).

At 200 cells, original single precision has 15 CPU and 13 CUDA TP failures, 22 success-mask disagreements, 44 exact diagnostic disagreements, and identical cloud masks. TP gain has 348/12800 entries beyond tolerance, all in the 25 cells where at least one device failed. The 175 both-success cells have no gain tolerance failure (A=`0.00244140625`, R=`1.0118346428e-6`). UV-KKT has the same 90 failures on both and 78 gain tolerance failures, all within those failed cells. Repeat/localization reproduces these results. [workspace32-localized.jsonl](workspace32-localized.jsonl).

At ftol=`1e-5`, all 600 workspace solves per device converge. TP and partition have exact diagnostic agreement; KKT has 9/200 different iteration counts but no status or cloud disagreement and no numerical tolerance failure. KKT fraction A=`9.1269612312e-8`, R=`2.0844963172e-4`; the absolute tolerance dominates near small fractions. No “same arithmetic implies same iteration history” claim is justified.

**Classification:** measured precision/tolerance limitation and a candidate for the C12 contract/test coverage, not an established new implementation defect with an authorized fix. The in-tree deck reaches it when explicitly used in float32; the unchanged in-tree test chooses float64 and passes. Hypothesis: floating-point rounding around an unattainably tight float32 logarithmic residual causes active-set/termination differences. The experiment establishes sensitivity to ftol; it does not identify a unique faulty instruction or justify silently changing solver tolerance policy.

Relevant pinned code: [TP active-set condition](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/thermo/equilibrate_tp.h#L184), [TP status encoding](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/thermo/equilibrate_tp.h#L385), [UV active-set condition](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/thermo/equilibrate_uv.h#L450), [UV status encoding](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/thermo/equilibrate_uv.h#L609). Both devices dispatch into the per-cell implementation; the [CUDA kinetics driver](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_dispatch.cu#L15) and [CPU driver](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/src/kinetics/evolve_implicit_dispatch.cpp#L15) were inspected.

Live [tracking issue #54](https://github.com/UCzhangxi/kintera/issues/54) is OPEN with no issue-level assignees, but explicit item owners. Its default-budget cold-start item is **D4, owner Linfeng** (correction to my intermediate D5 label). D6/K4 also belong to Linfeng. The 19/45 Jupiter cold-start failures reproduce that known limitation and were not claimed as new. No row specifically assigns the float32 tolerance/status candidate to Tianhao; coordination is needed before any implementation change. No fix branch, RED/GREEN fix claim or commit was made. Existing K15 CPU-only evidence was not reused as CUDA evidence and this run does not extend the K15 absent-gas campaign.

## Limits and handoff

I retain numerical-evidence ownership; the coordinator owns issue routing and incorporation into the chapter once the C12 specification arrives. A future implementation fix requires confirmed item ownership, an agreed behavior contract, a failing test at the pin, CPU/CUDA GREEN results, a separate commit and independent cross-review. No chapter PR was opened.

Coverage is bounded: one GPU architecture and mixed-runtime build, two dtypes, small systems and one-step kinetics. No timing claims, exhaustive workspace boundary/oversized-cell test, multi-GPU/multi-stream concurrency campaign, sanitizer campaign, malformed-pointer crash run, complete C++ suite, full Python suite or extreme-cancellation K15 campaign was performed. Named-function probes test table dispatch through the RH transform, not direct scalar derivative accuracy. Convergence outcomes and finite masks are preserved so agreement is not mistaken for correctness.
