# Role-only public-text cleanup

The cleanup starts from report head `91d757b79dd2ca39575ee57f50cb05c2f357051c`,
now based on `tech-report` at `68fea828ca5c6a0cffd22ca7a103c2bbcc960b34`.
It replaces personal workflow attribution with chapter-owner, reviewer, lead and
report-integrator roles. Required repository identifiers and immutable evidence URLs
remain technical source locators. Git author metadata is retained.

The full added-text scan found 50 matching lines across 14 files before cleanup and
zero afterward, including expanded cached chapter metadata and personal workspace paths. The original five flagged
files are included. Thirteen source provenance comments and four corresponding cache
files change only their author-role comments. Eight review/evidence documents receive
role wording; all their full evidence SHAs and URLs are preserved. Four compiler-command
path prefixes in two evidence JSON records use the explicit `<audit-workspace>` placeholder;
all other arguments, recorded outputs and numerical results remain identical. No scientific code,
measurements, source pin, tolerance, expected-failure rule or layout policy changes.

Commit `4a8d7d5a720eda7e5c4db69660af5e900962bda5` is reworded as
`454691128d1b60276a591e9b9b3027579a1b3300`; its tree is identical. The rewritten
messages have no personal attribution matches. The subsequent content commit also
retains its identical tree before this cleanup is applied.

Validation: `git diff --check` passes; tooling has 486 passed and three environment
skips; provenance has 123 tags, zero problems and 103 active historical rows;
ratchet remains history 0/offpin 182/status 0/xref 3. No duplicate scientific
reproduction is needed: the prior fresh-clone run at the starting head exited 0
with 129 executions, three strict expected failures and zero unexpected outcomes.
That is prior-head evidence, not a claimed new-head scientific run. New-head CI is
required separately. The raw CI layout finding of 15 overfull boxes remains open.
