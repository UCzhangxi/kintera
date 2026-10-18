# Reader tasks (N2)

The curated reader-task list from which `tools/gen_reader_tasks.py` generates Appendix G. Its seeds are the
questions of the newcomer bank (`tools/task-map.yaml`; a question may be split into parts) and any task the editor
adds. Seeds that are the same task are merged into one row, which lists every source. The list starts empty.

Format: one table, 5 columns, one row per line. `id` is unique. Column 4 is either a bare label `sec-...`, the
section that answers the task, or `not provided: <status>: <reason>`. Column 5 holds the reviewer's note; for an
anchored row it starts with the rendered section number. A literal `|` inside a cell is written `\|`.

| id | task | source(s) | answered at (anchor) or not provided (reason) | note |
|---|---|---|---|---|
