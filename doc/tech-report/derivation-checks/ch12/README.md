# Chapter 12 checks

Evidence for @sec-ch12, at the code pin `chengcli/kintera@0d9f67f97d841147e23283d2dcdab302238d2c45`.
The chapter's main check, `check_ch12_twins.py`, lives one directory up with the other chapters'.

| what | needs | output |
|---|---|---|
| `../check_ch12_twins.py` | CPU | `../check_ch12_twins.out` (x86_64); `check_ch12_twins.supplied.out` is the same script on arm64 |
| `validate_ch12_output.py <out>` | CPU | `validate_ch12_output.out`; enforces 17 PASS / 1 INFO / 0 FAIL, since the twins script exits 0 even when a line prints FAIL |
| `check_ch12_spec_complement.py conditioning` | CPU | `check_ch12_spec_complement.conditioning.out` |
| `check_ch12_spec_complement.py sparse` | **CUDA** | `check_ch12_spec_complement.sparse.out` |
| `check_ch12_spec_complement.py launch` | **CUDA**, Linux (reads `/proc/self/maps`) | `check_ch12_spec_complement.launch.out` |
| `check_ch12_numeric_devices.py` | **CUDA** (raises without it) | `check_ch12_numeric_devices.out` |
| `check_ch12_k42.py` | **CUDA** | `check_ch12_k42.out`; K42, 2000 paired singular-solve trials plus exact and ill-conditioned controls |
| `check_ch12_atm2d_reach.py` | **CUDA** | `check_ch12_atm2d_reach.out`; in-tree atm2d systems. `--newton-only` gives `check_ch12_atm2d_newton.out`, the backward-Euler shift-loss case |

`check_ch12_atm2d_reach.py` imports `check_ch12_k42.py`; keep the two together.

Most modes cannot run without a GPU. Their committed outputs record the kintera version and a
relative install path only; the device, torch version and build are in the chapter's own run footnotes.

## Running one

    export KINTERA_WT=<build tree at the pin>      # twins
    export KINTERA_REPO=<source tree at the pin>   # spec complement, for tests/jupiter.yaml
    export CH12_SAVED=$PWD/saved-preparation       # saved inputs the conditioning mode reads
    cd "$(mktemp -d)" && python <this dir>/check_ch12_spec_complement.py conditioning

`saved-preparation/` holds only what a retained check reads: `kinetics{64,32}.jsonl` supply the measured
CPU-CUDA differences that `conditioning` divides by its recomputed $\kappa_2$; the two `test_*.yaml` cards and
`one-cell.yaml` are the decks behind the conditioning and `ftol` figures the chapter quotes.
