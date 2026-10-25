# Pending numerical and chapter review

The runtime Paddle pin is `a4cac94451ab5fc800735edb00180e98859a20c2` from
`elijah-mullens/paddle`. `paddle_migration.py` uses the public zero-condensate
regression card and real native thermodynamics, kinetics and implicit solver.
The supplied EOS returns the card's fixed 120 K; this is not a coupled CRM run.

Old/new evidence has three columns: unmodified old driver, an explicitly labeled
API-only adapter mapping the removed Snapy index namespace, and migrated driver.
The adapter is diagnostic evidence, not an original-runtime reproduction. There
is no invented old number where old execution fails. The output JSON records
all gas/solid density increments, mass residuals and comparison deltas.

The model/data reference for figures is the unchanged figure code and committed
inputs at report `1839c0dc5e51bbb4de5ee4c9ddd7340478ec7518`. The committed
`figure-values.json` captures all plotted arrays, schematic geometry and labels,
plus all five external numerical datasets used by the 14 figures. Nine figures
are self-contained schematics; comparing their geometry is not evidence of GPU
execution. The checker reruns all three public data writers, deletes prior named
outputs, redirects figure reads to the fresh files, and fails on missing inputs,
missing/new figures, changed shapes, or values outside the numerical threshold.

Eight binary64 ULPs permit only floating arithmetic/serialization roundoff (the
observed water differences are one or two ULPs). There is no absolute scientific
error allowance. Status/iteration values, array structure, strings and nonfinite
classes are exact. Every changed leaf is reported even when accepted. A passing
check is numerical evidence, not chapter-owner approval of changed numbers.

## Review requests needed; none approved

The formal `tools/chapter-owners.tsv` entries remain `unassigned`. Routing below
uses provenance authors and history; the editor must confirm final responsibility.

| Chapter | Evidence of authorship | Review needed |
|---|---|---|
| 14 | [_kinetics.qmd](https://github.com/UCzhangxi/kintera/blob/1839c0dc5e51bbb4de5ee4c9ddd7340478ec7518/doc/tech-report/book/chapters/14-coupling/_kinetics.qmd#L7) provenance identifies the chapter author; later derivation commit `fae7276404b540a1bfc27bb52607175de41e12a9` identifies the derivation contributor | Six-argument API, source/citation migration, all four newly measured Paddle cases and conservation tolerances |
| 5 | [_diagnostics.qmd](https://github.com/UCzhangxi/kintera/blob/1839c0dc5e51bbb4de5ee4c9ddd7340478ec7518/doc/tech-report/book/chapters/05-chemical-equilibrium/_diagnostics.qmd#L7) provenance identifies the chapter owner | Every changed water-input and plotted-coordinate value, even though within eight ULPs |
| 4 | [_equilibrate-uv.qmd](https://github.com/UCzhangxi/kintera/blob/1839c0dc5e51bbb4de5ee4c9ddd7340478ec7518/doc/tech-report/book/chapters/04-phase-equilibrium/_equilibrate-uv.qmd#L7) provenance identifies the chapter owner | Disputed 302 K versus 304.80206565 K result; no scientific value was changed here |
| 12 | `_device-functions.qmd` / `_dispatch.qmd` identify the chapter owner; later correction `a31e59be3cad1895070e750cff8fbeb40e43fb1e` identifies the chapter 12 owner | Missing probe/patch and paired campaign drivers; schematic equality does not establish the missing GPU experiments |
| 13 | `_device-coverage.qmd` / `_results.qmd` identify the chapter owner | Missing GPU probe and external resources, with CPU/GPU distinctions retained |

Chapter 4/12/13 files are not modified by this migration. The six owner-authored
appendix content exclusions remain. Known documented example failures and missing
resource failures stay visible in the audit; no status is changed to manufacture
success. PR #100 remains draft until the committed fresh-clone reproduction exits
0, required numerical/source reviews are complete, and the owner decides merge.
