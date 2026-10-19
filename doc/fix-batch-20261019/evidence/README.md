# Evidence for the thermo fix batch of 2026-10-19 (kintera 0d9f67f, v2.6.5)

FORK-ONLY. This directory exists on the staging branch `fix/thermo-20261019` of the fork so that each fixer can
run the RED case of its item. The upstream pull request built from this branch must EXCLUDE
`doc/fix-batch-20261019/`.

- `q346b/` .. `q346e/`: one quick check per item, `<name>.py` -> `<name>.out` (stdout of the run at 0d9f67f).
- `q346g/`: the checks behind items D65, K8, K9 and K10 (from the tech-report derivation spec):
  `check_ch6_rates.py` (D65, line `[d2] reverse column`), `check_ch3_card_latent.py` (K8, the `ratio=` lines),
  `check_ch9_atm2d.py` (K9, line `d' (info) hog total 0.5 < 1`) and `check_arrhenius_ea_default.py` (K10).
- `common.py` loads kintera and builds `ThermoX` from `tests/jupiter.yaml`; `tp_oracle.py` is an independent
  brute-force TP equilibrium for `tests/jupiter.yaml`; `q346b/card_two_cloud_tref0.yaml` is a two-cloud card with
  `Tref: 0` and precipitating condensate copies, used by `q346b/check_d17_precip_copy.py`.
- The copies of `common.py` and `tp_oracle.py` in the five subdirectories are identical.

## Rerun

1. Build kintera from a tree at the commit under test and make its Python package importable, either installed in
   the active environment or placed in `<tree>/_pyinstall` (that directory is put first on `sys.path`).
2. `export KINTERA_WT=<tree>` (the scripts read `<tree>/tests/jupiter.yaml`).
3. Run each check from a scratch directory, because kintera writes `*.pt` dumps into the working directory on a
   failed solve:

   ```
   cd "$(mktemp -d)"
   python <this dir>/q346b/check_tp_maxiter.py > check_tp_maxiter.out
   diff check_tp_maxiter.out <this dir>/q346b/check_tp_maxiter.out
   ```

CPU, float64; each check takes seconds to about a minute (needs torch and numpy). At 0d9f67f every `.out` here is
reproduced byte for byte. After a fix, the item's RED line (listed in the tracking issue) must change as the
issue says; these scripts are evidence, not the regression test: each fix adds its own in-tree test.
