# Chapter 14 C16 and F1 correction

Starting report: `e5706d2bc8844d3d335fd1e4bd9db870b4849bb4`. Existing ownership: issue
[101](https://github.com/UCzhangxi/kintera/issues/101). Scientific source stays
`e357792d50639d68e9090b542edf038d2b029aa2`. Scope: two prose corrections, no numerical output, tolerance,
source-pin, implementation or baseline change.

| Finding | Independent verification | Correction |
|---|---|---|
| C16: current-pin arm64 attribution | The [original footnote](https://github.com/UCzhangxi/kintera/blob/68fea828ca5c6a0cffd22ca7a103c2bbcc960b34/doc/tech-report/book/chapters/14-coupling/_thermo.qmd#L187) associates 1.11e-16 with source 0d9f67f97d841147e23283d2dcdab302238d2c45 / 2.6.5. Current check output identifies Linux x86_64, with no current-pin arm64 record. | State that no arm64 run at this pin is recorded; preserve the original record in history and retained evidence. |
| F1: speculative implementation cause of warming | The committed default and max-iter-10 controls both give the same six warming values at printed precision, but vary only the iteration limit. They do not isolate an implementation change. | Remove the two speculative/inferential sentences. Keep the directly measured iteration-control result and existing output values; introduce no substitute causal claim. |

The supplied reviewer also reports a deck/build swap contradicting the implementation attribution. That matrix
is reviewer evidence, not a newly executed control in this correction. Its proposed deck-based explanation is
not promoted to a chapter claim without a committed, independently validated control.

Two content checks fail before correction and pass afterward: no current-pin attribution of the old arm64
value; no unsupported implementation attribution in the warming paragraph. The historical numerical record
is not erased or relabelled. The original complete reproduction remains attributed to
`a5c3bd46a6ac95996d5a980ccc1676678b12237d` (128 executions, seven nonzero exits); no new complete reproduction is
claimed. Final-head affected-check, report and render results are returned in the implementation ledger.

Completion of this correction means both prose defects are fixed, affected outputs remain unchanged, and the
new head plus validation are available for independent ch14 recheck. It does not close historical provenance,
ratchet, chapter 12 continuation or package-script findings, and does not imply approval or merge readiness.
