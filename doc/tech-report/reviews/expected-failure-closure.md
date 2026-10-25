# Strict expected failures for the report audit

Accepted before editing under [issue 101](https://github.com/UCzhangxi/kintera/issues/101#issuecomment-6399576383),
starting from report `dfe26fc9829252f162cb05d88908cbd5b51dc233`. This implements Xi's authorized closure policy;
it does not fix the scientific bugs tracked in [issue 103](https://github.com/UCzhangxi/kintera/issues/103).

## Independently verified scientific sources

The prior source abbreviation resolves to **`53f3ffcc6fefd34513dc04214d506103b2d917ed`** (kintera 2.6.6).
It was checked out from Git and built using the README configure/build/install sequence:
`cmake -S <source> -B <source>/build -DCMAKE_BUILD_TYPE=Release -DCUDA=OFF -DNETCDF=ON`,
`cmake --build <source>/build --parallel 8`, then
`python -m pip install --no-build-isolation --no-deps --target <old-install> <source>`.
The existing pinned Python environment was reused (Python 3.11, torch 2.10.0+cu128); no new dependency environment
was necessary. The existing verified source build at **`e357792d50639d68e9090b542edf038d2b029aa2`** supplied
kintera 2.6.7. Each execution recorded the imported package version/location and the checkout's full SHA.

The unchanged example directory from each source was copied to separate scratch directories. With
`CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MPLBACKEND=Agg`, each of these commands ran at **both** commits:

| command | exit at each commit | matched meaningful error |
| --- | --- | --- |
| `python example_chapman_cycle.py` | 1 | `TypeError: forward(): incompatible function arguments`, Arrhenius signature requiring `other`, invoked with three arguments |
| `python example_earth_dry.py` | 1 | `AttributeError: 'ThermoX' object has no attribute 'extrapolate_ad'` |
| `python test_type_hints.py` | 1 | `Skipped: type-hint demonstration only; not a runtime pytest module` |

All three script SHA256 hashes and their complete normalized tracebacks match between sources. The six records
are committed in `environment/expected_failure_evidence.json`; only absolute traceback directory prefixes are
normalized, preserving frame filenames, lines, calls, error types and messages. The policy includes the full
verified current source and script hashes, exact command, exit 1, expected traceback, and #103 link.

**The type-hints command does not segfault as shipped.** Its module-level skip stops execution first. The separate
#103 reproducer `from kintera import SpeciesThermo; st=SpeciesThermo(); st.vapor_ids([1,2,3]); print(st.species())`
was also executed independently at both commits with core dumps disabled: both subprocesses terminated with
signal 11 (`subprocess.returncode == -11`, conventionally shell status 139). That separate failure is not accepted
as a substitute for the script's recorded exit 1. No other underlying scientific behavior is claimed verified here.

## Strict accounting and RED/GREEN

The matcher accepts only the recorded failure. Unexpected success, a changed command/source/script, a different
exit or traceback, signal, timeout, missing log/script, additional error, duplicate traceback, and setup/launch
failure stay red. Missing expected executions also fail. The loader cross-checks each rule against matching
records at both scientific commits. The audit preserves raw exits and logs, adds status/reason/issue fields, and
bases its final exit on unexpected outcomes, not raw nonzero count. The summary reports both counts.

- Initial matcher regressions: **6 failed / 34 passed** before support; **40 passed** after.
- Ledger-accounting regressions: **4 failed / 40 passed** before integration.
- An additional setup error preceding an otherwise matching traceback: **three failures** before repair.
- Final focused matcher, audit-exit and artifact checks: **55 passed**.
- Full pinned-image tooling: **484 passed / three skipped**.
- Reclassification of the preserved 129-command ledger (not a new reproduction): **four raw nonzero exits,
  three EXPECTED-FAIL, one unexpected**. The missing ch12 probe stays red; none of its failure is waived.

The ch12 delivery deadline is Unix **1792949487.284339**, 2026-10-25 **17:31:27.284339 UTC**. Its dependent claim
is untouched before that deadline. Final-head fresh-clone reproduction and exact-head CI remain required after
that delivery/removal decision. Both PRs stay draft until reproduction exits 0 and relevant current-head CI is
green. The separate CI raw layout finding (15 overfull boxes, exit 1 under the existing report-mode policy)
remains visible and unresolved. One-line chapter-owner refreshes will be requested on the final head only;
no merge or formal approval is authorized.
