# Ch4/ch5 measurement attribution follow-up

Starting report: `3e7fc24d58a13099d455efb1da42b18d04f00993`.
Ownership and reproduction were recorded before editing under
[issue 101](https://github.com/UCzhangxi/kintera/issues/101#issuecomment-6394999169).

The ch4 active-set paragraph repeated the historical residual without attaching its source footnote.
The [original run](https://github.com/UCzhangxi/kintera/blob/fb86705d6726ab5398301c7accda064affb7b35e/doc/tech-report/derivation-checks/check_ch4_tp.out#L28)
reports `-6.953e-08`; the
[current committed output](https://github.com/UCzhangxi/kintera/blob/3e7fc24d58a13099d455efb1da42b18d04f00993/doc/tech-report/derivation-checks/check_ch4_tp.out#L30)
reports `-1.331e-07`. The smallest correction identifies the paragraph as a historical run and attaches
`ch04-conditions-check`, whose verified historical source remains `0d9f67f97d841147e23283d2dcdab302238d2c45`.
Neither value is presented as a universal bound across builds or relabeled as a current-pin experiment.

Ch5 also needed a build-specific clarification. The
[original x86_64 output](https://github.com/UCzhangxi/kintera/blob/fb86705d6726ab5398301c7accda064affb7b35e/doc/tech-report/derivation-checks/check_ch5_equilibrium.out#L26)
reports `1.6e-17`; the
[current Xeon output](https://github.com/UCzhangxi/kintera/blob/3e7fc24d58a13099d455efb1da42b18d04f00993/doc/tech-report/derivation-checks/check_ch5_equilibrium.out#L26)
reports `1.2e-16`. The Newton paragraph now identifies its historical build and points to the existing
build-specific table for the current Xeon result and attribution. Historical values, footnote bodies,
scientific source pins, check scripts, outputs, tolerances and gate baselines remain unchanged.

RED/GREEN: `python -m pytest tools/tests/test_chapter_measurement_attribution.py -q -p no:cacheprovider`
had two failures before correction and two passes afterward. The checks bind repeated historical claims to
source footnotes, require the current-build comparison, and preserve the distinct committed current outputs.
Provenance passes with 123 tags, 104 historical measurements and zero problems; ratchet remains
history 0 / offpin 182 / status 0 / xref 3. The affected math-span check passes. A direct old-report link in the
book was rejected by the off-pin ratchet; the immutable output links are retained here instead, with no baseline change.

Final-head reproduction and exact-head CI must be refreshed after this change. The prior four-command failure
ledger and CI layout finding remain visible, with chapter-owner/package-fix routing but acceptance unresolved. Both PRs
stay draft unless reproduction exits 0 and relevant CI is green; no merge or review approval is authorized.
