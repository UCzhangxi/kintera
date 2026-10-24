# Actual-source invariant results

Pre-#151: `53f3ffcc6fefd34513dc04214d506103b2d917ed` (2.6.6).
Current main: `e357792d50639d68e9090b542edf038d2b029aa2` (2.6.7).
Mutations are dirty disposable builds of current main; their version strings
identify that fact. Torch 2.10.0+cu128, CPU binary64; CUDA was not exercised.

| Source variant | Absent rate | Minimum amount (mol/m³) | Max relative atom drift/step, reaction | Max relative energy drift/step, condensation | Exit |
|---|---:|---:|---:|---:|---:|
| pre (2.6.6) | 1e-300 | -9.9900099900101188e-301 | 2.2204460492503131e-16 | 9.0324883585477738e-16 | 1 |
| clean (2.6.7) | 0 | 0 | 2.2204460492503131e-16 | 9.0324883585477738e-16 | 0 |
| floor (2.6.8.dev0+ge357792d5.d20261024) | 1e-300 | -9.9999900099898874e-301 | 2.2204460492503131e-16 | 9.0324883585477738e-16 | 1 |
| atoms (2.6.8.dev0+ge357792d5.d20261024) | 0 | 0 | 0.00099900099900096517 | 9.0324883585477738e-16 | 1 |
| energy (2.6.8.dev0+ge357792d5.d20261024) | 0 | 0 | 2.2204460492503131e-16 | 0.16551275895197659 | 1 |

Every case executed 1000 updates. JSON includes per-step maxima, total drift,
signed mean drift, final amounts, final temperature and diagnostics. No error
exception was used as mutation evidence: `verify_break_results.py` passes.
Original tolerances and figure baselines are unchanged.

Exact executed procedure (inside the pinned report environment):

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCUDA=OFF -DNETCDF=ON
cmake --build build --parallel 8
MAX_JOBS=8 python -m pip install --no-build-isolation --no-deps --target _pyinstall .
PYTHONPATH="$PWD/_pyinstall" python /work/doc/tech-report/invariants/check_invariants.py
# For clean current main and each actual-source mutation:
python /work/doc/tech-report/invariants/mutate_sources.py "$PWD" floor # or atoms, energy; omitted for clean
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCUDA=OFF -DNETCDF=ON
cmake --build build --parallel 8
MAX_JOBS=8 python -m pip install --no-build-isolation --no-deps --target "_pyinstall_$mutation" .
PYTHONPATH="$PWD/_pyinstall_$mutation" python /work/doc/tech-report/invariants/check_invariants.py --output "$output/$mutation.json"
```

The actual driver scripts and full build logs are retained in the delivered
ledger's evidence directory. The committed `run_source_checks.sh` packages the
same configure/build/isolated-install/check sequence for a new output directory.
The first mutation-driver attempt stopped at Git's bind-mount ownership check
(exit 128); scoped process configuration for this disposable checkout resolved
it before any mutation build. No installed site-packages were edited.

Source mutations are explicit patches beside the JSON. The floor patch raises
both kinetics zero clamps to 1e-300. The atom patch removes production of the
last species in the implicit increment. The energy patch removes the cloud
reference-energy term from native evaluation, retaining the gas terms.
These are sensitivity tests, not proposed upstream fixes.

The inventory integrity check exits 1 on the floor-mutated source and 0 on
clean current source. This does not close the **per-occurrence physical guard
coverage gap**, which remains explicitly marked in the inventory and PR.
