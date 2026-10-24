# kintera Technical Report (work in progress)

This branch (`tech-report` on UCzhangxi/kintera) holds a technical description of kintera, in the style of the
WRF, MPAS and CESM technical notes. It is never merged into kintera main and never opened as a pull request to
it. The report is a Quarto book of 14 chapters and appendices A to F (OUTLINE.md).

## Reproduction setup

On Linux x86-64 with Docker, run `bash doc/tech-report/environment/reproduce.sh`
from the repository root. The [environment guide](environment/README.md) describes
the pinned build/render dependencies, CPU scope, retained logs and the validated
public Paddle migration. Use a fresh disposable checkout for the audit.

## Files

- `STYLE.md`: the binding style guide, covering the six-layer template, citations, evidence, figures and checks.
- `NOTATION.md`: every symbol, with one meaning each.
- `OUTLINE.md`: the plan, chapter by chapter and scheme by scheme: 1 Overview and quick start, 2 Species and
  thermodynamic data, 3 Equation of state and thermodynamic functions, 4 Phase equilibrium of multiple
  condensables, 5 Multiphase chemical equilibrium, 6 Kinetics, 7 Photochemistry, 8 Diffusion, 9 The
  two-dimensional atmosphere solver, 10 Numerical solvers, 11 YAML configuration and the Python/C++ API, 12 GPU
  execution, 13 Tests and validation, 14 Coupling to snapy and paddle; appendices A notation, B derivation index,
  C test index, D topic index, E task map, F glossary.
- `READING.md`: the reading list for chapters 2-5, pairing published sources with the kintera code they explain.
- `DERIVATION_SPEC.md`: the derivation each chapter's Derivation layer must carry (chapters 2-6 and 9 and a
  proposed overview), entry by entry: question, start, end at the code's file:line, steps, check, home and
  status. Its checks are the scripts in `derivation-checks/`, each with its committed output `<name>.out`.
- `AUTHOR-CHECKLIST.md`: the gates to run before opening a chapter PR, with the command for each and what it must
  say, and what belongs in the PR body.
- `REVIEW-RECORD.md`: the template a reviewer fills when a review is requested (head/tree/base shas with read
  times, the gate table against the base, the render run, findings, verdict).
- `CONTRIBUTING.md`: how an author opens, checks and merges a pull request into this branch.
- `LOOKUP-TEST.md`: the method for testing whether a reader can find answers through the book's routes.
- `FIGURES.md`: the figure manifest, every figure with its section file, modules, data and writer.
- `code_pin.yml`: the one commit every `{{< code >}}` citation resolves at. It is the single source of truth
  for the kintera pin; no other file restates that sha.
- `book/`: the Quarto book. `src/`: the Python package `kintera_report` (figures, checks, their data).
  `tools/`: the gates, generators and their tests. `reviews/`: the review record.

## Where things live

One home per kind of resource. Homes marked "planned" have no files yet.

| what | home | written by | read by |
|---|---|---|---|
| chapter text | `book/chapters/NN-slug.qmd` and its sections `book/chapters/NN-slug/_<scheme>.qmd` | authors | Quarto |
| figure code (planned) | `src/kintera_report/chNN/figures/fig_<name>.py`: one module per figure, `make_fig()` returns it | authors | the figure's `{python}` cell in its section file |
| chapter helpers (planned) | `src/kintera_report/chNN/*.py`; the one figure style module `src/kintera_report/figstyle.py` | authors | figure modules and checks |
| executable checks (planned) | `src/kintera_report/chNN/checks/<name>_check.py` with its committed output `<name>_check.out` | authors | the chapter's footnotes, Appendix B (`tools/gen_derivation_index.py`) |
| figure data (planned) | `src/kintera_report/chNN/data/` | the check or run script `FIGURES.md` names next to the file | figure modules |
| generated appendices | the appendix fragments under `book/chapters/` (`_app*.qmd`) | the pre-render generators in `book/_quarto.yml`, from their inputs in `tools/` (`*.yaml`, `*.json`, `reader-tasks.md`, `derivation-statements/`) | the appendix chapters |
| execution cache | `book/_freeze/` | Quarto (`freeze: auto`) | Quarto |
| gates and their baselines | `tools/*.py`, `tools/*-baseline.json`; their tests `tools/tests/`, fixtures `tools/tests/fixtures/` | authors; a baseline by its gate's `--update` | CI, `AUTHOR-CHECKLIST.md` |
| ownership and review record | `tools/chapter-owners.tsv`, `reviews/review-record.tsv` | the editor (owners); reviewers (record) | the ratchet gate |
| drawn figures | `build/figures/<chapter>/<label>.svg\|pdf\|png` (gitignored) | `tools/render_figures.py` | you |

## Citing code

Cite kintera code by file and symbol, never by line number:
`{{< code src/kinetics/arrhenius.cpp ArrheniusImpl::forward >}}` renders as a link to the symbol's lines at the
one pinned commit, `code_pin.yml`. The symbol is a function, method, class, struct, member or variable; C++ names
keep their classes and drop their namespaces, gtest tests are `Suite.Name`, Python symbols are `Class.method`, and
a file alone is `{{< code <path> >}}`. If the gate reports a symbol as ambiguous (overloads), add the `overload=N`
it lists. `python3 tools/code_anchors.py check` resolves every citation at the pin (Universal Ctags:
`brew install universal-ctags` or set `CTAGS=<binary>`; sources from a clone holding the pin in `KINTERA_REPO`,
else fetched into `~/.cache/kintera-report`); it runs in the render's pre-render and as a CI step, and either fails
on a citation that does not resolve. To move the pin: `python3 tools/code_anchors.py bump <full-sha>` lists the
cited symbols whose body changed (re-read those, and fix the claims they carry), and writes the new sha into
`code_pin.yml` only when every citation resolves there; `diff <old> <new>` prints the same list for any two commits.

Citations that cannot be a symbol (lines across several symbols, top-level code, other repositories) are STYLE
10.6 links. `tools/check_citations.py` checks that every such link and every `path:line@sha` resolves at its sha,
that the cited lines exist and, in a `.qmd`, contain the link's anchor symbol, and that the repository is one
STYLE 3.1 allows: chengcli/kintera, UCzhangxi/kintera, chengcli/snapy, UCzhangxi/snapy, chengcli/pyharp,
chengcli/paddle. A link with no repository prefix means kintera; any other repository is named in front. Commits
are looked up in local clones first, then in cache clones under `~/.cache/kintera-report-citations`.

## Tools

- **Ratchet gate.** `tools/ratchet_gate.py` counts four things per chapter (and for the preface, `book/index.qmd`)
  and compares them with the committed baseline `tools/ratchet-baseline.json`. **history**: change history in
  body text (PR or issue numbers, "the previous pin", "is now" and the other phrases of `HISTORY_PATTERNS`; words
  that also describe physics count only in their history forms); footnotes, HTML comments (PROVENANCE),
  shortcodes and fenced code are not body text. **offpin**: a sha of a cited package that is not that package's
  one pin (`code_pin.yml` for kintera, `tools/package-pins.json` for the others), anywhere in the file.
  **status**: a file whose PROVENANCE says `reviewed` or `approved` without a valid entry in
  `reviews/review-record.tsv`. **xref**: a reference that resolves nowhere, and every `sec-` label no other
  chapter cites. A rise fails; a fall must lower the baseline in the same pull request
  (`python3 tools/ratchet_gate.py update`). The baseline records the pin it was measured at and may rise only with
  a move of that pin; `check --base-ref <target>` (what CI runs) enforces this against the target branch.
  `counts -v` lists every instance. **Owners**: `tools/chapter-owners.tsv` names one owner per chapter; it is the
  lock (`check` fails on none or two) and the source of the per-owner burn-down table. **Review record**: one
  tab-separated line per event, newest last (`file kind reviewer author pin sha256 date note`), written with
  `ratchet_gate.py record review <file> --reviewer R --author A` or `record restamp <file> --reviewer R --note
  "..."`; a reviewed file passes when its newest entry has the current hash and pin and a reviewer who is not
  its author.
- **Render gate.** `tools/render_gate.py` renders `book/` to HTML and PDF and gates the render (STYLE 10.9).
  Outcomes: pass (exit 0), pending (exit 2: a `kintera_report` function a chapter calls is not written yet, or
  there is no book yet) and fail (exit 1). Nothing is released while anything is pending; `--release` makes
  pending a failure. References into a chapter or scheme that is not written yet are listed in their own gate,
  by target id, as expected failures, apart from the real dangling references.
- **Figure style.** `tools/check_figstyle.py` (STYLE 6): figure code under `src/kintera_report/` may style only
  through the one figure style module. Per chapter, without importing anything, it counts imports of other style
  modules, rcParams writes and inline font settings, and compares them with `tools/figstyle-baseline.json`. A
  chapter above its baseline fails, and so does one below it until `--update` lowers the baseline in the same
  commit (it never raises one); `--list` prints every site. `render_gate.py` runs it as a source gate.
- **Figures.** `python3 tools/render_figures.py` draws every figure cell as the render does, to `build/figures/`
  (`--chapters ch04,ch06` for some chapters; `build/figures/index.json` holds each SVG's sha256, so two draws
  compare byte for byte). To change a figure's data, run the writer `FIGURES.md` names, then draw it. After
  adding a figure, or changing the modules or data files it uses, rewrite the manifest with
  `python3 tools/render_figures.py --manifest` in the same commit; `render_gate.py` checks it (gate
  `figure manifest`).
- **Test index.** `tools/gen_test_index.py` generates Appendix C from `tools/ctest-index.json`, the tests `ctest`
  lists for kintera at the pin. Both are committed; CI runs `python3 tools/gen_test_index.py --check`, which fails
  if the fragment is not what the fixture gives. When the pin moves, refresh both from a clean checkout at the new
  pin (configuring is enough, no build):
  ```bash
  git clone https://github.com/chengcli/kintera kintera-pin && git -C kintera-pin checkout <pin>
  cmake -S kintera-pin -B kintera-pin/build
  python3 tools/gen_test_index.py --refresh kintera-pin/build
  ```
- **Generated files and rebasing.** Appendix A (`tools/gen_notation_index.py`) and Appendix B
  (`tools/gen_derivation_index.py`) are committed only in pieces that one chapter owns: Appendix B is one fragment
  per chapter, and Appendix A depends on `NOTATION.md` alone. Every value that several chapters decide (totals,
  per-chapter counts, symbol counts, "first used") is a `{{< generated ... >}}` shortcode, filled in at render
  from `book/_generated/*.json`, which the generators write in the pre-render step and which is not committed.
  Appendix B's one-line statements are one file per chapter too: `tools/derivation-statements/chNN.json` holds
  that chapter's `eq-chNN-...` labels and no other. So two pull requests that edit different chapters touch
  different files, and git merges them (`tools/tests/test_chapter_prs_merge.py`). After a rebase, never hand-merge
  a generated file: take either side, run `python3 tools/gen_derivation_index.py`,
  `python3 tools/gen_notation_index.py` and, if your chapter's counts changed, `python3 tools/ratchet_gate.py
  update`, and commit what they change. Two pull requests that both edit `NOTATION.md` can still conflict.
- **Chapter list.** `tools/book_chapters.py` writes the chapter list of `book/_quarto.yml` from OUTLINE.md's
  chapter ids and the chapter files that exist, in OUTLINE order; the render gate fails when the list is out of
  date. Run `python3 tools/book_chapters.py` after adding a chapter file.
- **Book.** `book/_quarto.yml`, `book/index.qmd`: KOMA `scrbook` PDF through LuaLaTeX, MathML in the HTML,
  `freeze: auto`. `book/_tex/` lets inline code and long shas break in the PDF; `book/report.css` wraps code in
  the HTML.

All tools are tested by `python3 -m pytest tools/tests`.

## CI

- `tech-report` (`.github/workflows/tech-report.yml`): on every pull request into this branch and every push to
  it, renders the book to HTML and PDF, runs the gates and the tool tests, and uploads both outputs as artifacts.
- `tech-report-ratchet` (`.github/workflows/tech-report-ratchet.yml`): runs the ratchet gate and its tests.
