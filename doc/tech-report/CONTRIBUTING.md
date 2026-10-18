# Contributing to the kintera Technical Report

This file is for a bot author (or any author) writing a chapter of the report. The report lives in
`doc/tech-report/` on branch `tech-report` of UCzhangxi/kintera. Read `README.md` (the map), `STYLE.md` (binding)
and `AUTHOR-CHECKLIST.md` (the gates) before the first pull request.

## Where pull requests go

- Open a pull request into branch `tech-report` of UCzhangxi/kintera, from a branch on that fork.
- Never push to chengcli/kintera, and never open a pull request to kintera main. The report is never merged there.
- Never force-push `tech-report`. Your own branch may be rebased and force-pushed.

## One chapter per pull request

- One chapter, or one scheme of a chapter, per pull request. A pull request that touches two chapters is split.
- `tools/chapter-owners.tsv` is the lock: one owner per chapter. The ratchet gate's `check` fails when a chapter
  has no owner or two. Edit only the files of the chapter you own: its `book/chapters/NN-slug.qmd`, its
  `book/chapters/NN-slug/_<scheme>.qmd` sections, its `src/kintera_report/chNN/` package and its
  `tools/derivation-statements/chNN.json`.
- A contradiction between your chapter and another goes to the editor (STYLE 11.4). Do not edit the other
  chapter, and do not quietly change your own text to match; the editor rules and both chapters follow the ruling.
- Files shared by every chapter (`STYLE.md`, `NOTATION.md`, `OUTLINE.md`, `book/_quarto.yml`, the tools) change
  only in their own pull requests, agreed with the editor.

## Before opening the pull request

- Run every gate of `AUTHOR-CHECKLIST.md` section 1 and put the before-and-after gate table in the PR body,
  with the numbers.
- Fill the PR body as `AUTHOR-CHECKLIST.md` section 2 says: pins with the command and time that read them, one
  line per claim touched, citations whose symbol changed, and anything deliberately left undone.
- No AI attribution line and no `Co-Authored-By` trailer, in the PR body or in any commit message.

## Merging

- CI must be green: both the `tech-report` workflow (render, gates, tool tests) and the `tech-report-ratchet`
  workflow.
- Merge on green. No sign-off is needed (the project owner's rulings of 2026-10-14 and 2026-10-18).
  `REVIEW-RECORD.md` remains available when a review is requested; a requested review is recorded in
  `reviews/review-record.tsv` with `tools/ratchet_gate.py record`.
- Merge by rebase, so `tech-report` stays a linear history.

## Generated files after a rebase

Never hand-merge a generated file (the appendix fragments under `book/chapters/`, `tools/ratchet-baseline.json`).
After rebasing onto `tech-report`, take either side of a conflict in a generated file, then rerun the generators
and commit what they change:

```bash
python3 tools/gen_derivation_index.py
python3 tools/gen_notation_index.py
python3 tools/ratchet_gate.py update   # only if your chapter's counts changed
```

`--check` on each generator and `python3 tools/ratchet_gate.py check` must then pass.

## What may be cited

- kintera code at the pin in `code_pin.yml`, through `{{< code <path> <symbol> >}}` or a STYLE 10.6 link, and
  code of the other repositories STYLE 3.1 allows, at a pinned sha.
- Published literature, through the bibliography (STYLE 10.8).
- Nothing else: no unpublished notes, no private correspondence, no private material of any kind. If a claim
  needs a source that is not public, leave the claim out and say so in the PR body.
