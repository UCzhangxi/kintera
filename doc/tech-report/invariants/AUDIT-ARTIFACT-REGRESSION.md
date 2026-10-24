# Preserve numerical evidence during audit execution

Issue-first ownership and reproduction: [issue #101](https://github.com/UCzhangxi/kintera/issues/101#issuecomment-6380033523).

At report head `ba2266a29942537124bd7eb64eb6c7316c8236a7`, the fresh source-effect runner passed 100 fixtures covering 95 operations, but the audit's `run()` subsequently overwrote `guard-source-effects.json` with execution metadata. The strict coverage gate exited 1 with `KeyError: source`. The clean invariant numerical output had the same basename collision. No numerical assertion was relaxed.

The regression executes the actual `run()` function extracted from `environment/audit.py`, launches a child that writes a two-value numerical JSON result, and requires that both numerical output and execution metadata survive. This is an artifact-lifecycle check, independent of the scientific fixtures.

Command: `python -m pytest tools/tests/test_audit_artifacts.py -q`.

* RED before repair: 1 failed; numerical result was replaced with `{name, command, cwd, exit, seconds, log}`.
* GREEN after repair: 1 passed; numerical values `[0.0, 1.0]` and source identity survive unchanged. Metadata uses `<name>.execution.json`.
* `python invariants/test_guard_coverage.py`: 11 passed after repair; missing/corrupt evidence remains rejected.

The complete superseded fresh run is retained separately. A new fresh public clone is required for final validation; successful standalone probes alone do not establish integrated audit success. This repair changes only execution metadata filenames, not command outputs, execution selection, scientific inputs, tolerances or failure handling.
