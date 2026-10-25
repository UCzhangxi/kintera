# Verified historical measurements and recovery checks

Xi's ruling permits verified historical measurements while retaining their source attribution and next-repin list.
Implementation ownership remains under [issue 101](https://github.com/UCzhangxi/kintera/issues/101).

## Evidence boundary

The immutable report witness is `94ef3f6d6675d4af9448347ec8ba557ef772e782`.
All 104 registered tags name scientific source `0d9f67f97d841147e23283d2dcdab302238d2c45`,
a verified ancestor of the current pin `e357792d50639d68e9090b542edf038d2b029aa2`.
`git merge-base --is-ancestor 0d9f67f97d841147e23283d2dcdab302238d2c45 e357792d50639d68e9090b542edf038d2b029aa2`
exits 0. Verification means the source label and complete claim/command match that immutable report record;
it does not claim a new execution of historical hardware or timing experiments.

Each tag gains an explicit `historical:` label. The registry binds file and stable footnote ID to the witness/source;
the gate compares the claim, producing command and source, allowing prose whitespace reflow and the historical field
only. Deleted, duplicate or altered rows, wrong labels (including substitution of the current source pin),
unknown witnesses, non-ancestral sources and unregistered labels fail closed. Attribution failures cannot be
baselined away. Future off-pin sources also fail without being mistaken for ancestral measurements.

Every provenance check and ratchet run prints the verified total plus the current file:line and full source SHA
for each row. The list remains the next-repin to-do. No numerical results, tolerances, original output artifacts
or scientific source pins change.

## RED/GREEN

Commands run from `doc/tech-report`:

- `python -m pytest tools/tests/test_provenance.py -q -k historical`: three failures / three passes before;
  six passes after initial implementation. The regressions demonstrate unlabeled off-pin RED, verified-label
  GREEN, current-pin relabeling failure, wrong historical label failure, changed-claim failure, missing-registry
  failure, repeated mandatory listing, and retention of unrelated ratchet findings.
- The additional `-k 'waived or future_source'` checks both fail before the strict-source repair and pass after:
  a raised count baseline cannot waive a wrong label, and an unlabeled future source is not current-pin evidence.
- `python -m pytest tools/tests/test_audit_artifacts.py tools/tests/test_ch13_probe_provenance.py -q` initially
  exposes three integration failures: scratch-directory JSON lookup, inline-code dollar parsing, and ch13
  history/incoming-reference findings. The audit now resolves report-owned JSON inputs before entering scratch;
  the math checker skips matching inline-code spans while still rejecting adjacent malformed mathematics.
  The invariant source history moves to a footnote with its SHA and numbers retained, and the implicit-step
  section links to its repeated-update invariant tests.
- Combined provenance, ratchet, ch13 and audit tests: **108 passed** after repair.
- Full report tooling in the pinned Docker image: **427 passed, three skipped**. The chapter-merge
  fixture retains its immutable witness objects; writable TeX caches are supplied by the test harness.
- Inserting a new current-pin footnote fails before stable historical IDs are implemented and passes after;
  existing evidence remains valid when its current line number changes.
- `python tools/check_math_spans.py --self-test`: exit 0.
- `python tools/check_provenance.py --base-ref origin/fix/report-environment-99`: exit 0;
  **123 tags, 104 verified historical measurements, zero provenance problems**, baseline remains zero.
- `python tools/ratchet_gate.py check --base-ref origin/fix/report-environment-99`: exit 0 after the documented
  pin-move baseline update. Counts are **history 0, offpin 182, status 0, xref 3**.

The 182 other off-pin references remain visible and counted: the exception applies only to validated historical
tag spans. Their baseline is regenerated under the existing rule permitting a baseline change with a source-pin
move (the stored baseline still named 0d9f67f). No history or new cross-reference defect is absorbed into it;
the three existing appendix reference findings remain unchanged. Adding an unrelated off-pin reference still
raises its count and fails the ratchet.

## Reproduction boundary

The completed audit at the witness report head remains preserved: `MAX_JOBS=8 bash doc/tech-report/environment/reproduce.sh`
exited 1 with 129 executions and nine nonzero exits. Both CTest runs passed 52/52; both Python suites passed
455 with 182 skips; figures passed 14/14 and strict guard coverage passed 138/138. Full rendering exited 0;
the render gate passed 32/33, failing provenance. Both deferred PDF checks passed.

A new final-head fresh-report-clone reproduction and exact-head CI are required after this change. Verified
unchanged scientific source build caches may be reused; that reuse must be reported separately from the prior
clean native builds. The ch12 missing probe and three package scripts remain separate owner-routed failures.
Neither PR becomes ready unless reproduction exits 0 and its relevant exact-head CI is green. #100 remains
unchanged and environment-only. No merge or reviewer approval is claimed.

### Container-owned fixture follow-up

The fresh audit at `7a7ae09309af9ac7b695318e4a4975877f040ace` exposed one additional fixture defect:
`python -m pytest tools/tests -q` exited 1 (439 passed, two skipped, one failure). A direct local fetch of the
historical witness invoked Git upload-pack against the host-owned `.git` directory, which the root container
correctly rejected even though the report worktree itself was trusted. The fixture now creates a temporary
bundle from that trusted worktree and fetches the bundle, preserving the witness objects without broadening
Git trust. The same chapter-merge regression passes in the root-container/host-owned-checkout configuration
(one passed, exit 0). The prior audit is retained; final-head reproduction and CI must be refreshed after this fix.
