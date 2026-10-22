# Reproduction environment

From a fresh checkout, on a Linux x86-64 machine with Git and Docker Engine:

```bash
bash doc/tech-report/environment/reproduce.sh
```

Allow at least 32 GiB RAM and 80 GiB free disk space. The build uses two compiler
jobs and runs CPU checks. No GPU result is inferred from a CPU build. Docker must
be accessible to the invoking account. The command does not install packages on
the host. Network access to public GitHub, PyPI and Debian snapshots is required.
Use a full-history checkout. The provenance gate compares against the immutable
audited report baseline `68fea828ca5c6a0cffd22ca7a103c2bbcc960b34`, so a
single-branch clone works without an `origin/tech-report` ref or a fetch.
To increase bounded compilation on a sufficiently provisioned machine, use
`MAX_JOBS=4 bash doc/tech-report/environment/reproduce.sh`; values 1–8 are accepted.

The image fixes Python 3.11.13 by image digest, Debian packages by the immutable
20250929 snapshot, Universal Ctags 6.2.1 by source commit, Quarto 1.10.19 by archive
SHA-256, and the complete Python dependency set in `python.lock`. The installed
system package versions are recorded in `/opt/system-packages.lock` in the image.
The snapshot selects NetCDF C 4.9.0 (`1:4.9.0-3+b1`), TeX Live base
`2022.20230122-3`, and TeX binaries `2022.20220321.62855-5.1+deb12u2`.
NetCDF includes both the C headers/link library and the Python package; installing
only the Python package is insufficient. TeX comes from the same Debian snapshot;
the audit’s explicit full-render command disables automatic TeX package installation.
Writable TeX, Matplotlib and citation caches live under `.reproduce/`.

The source builder reads `../code_pin.yml` and `../tools/package-pins.json` rather
than restating their pins. It follows the package README configure/build/install
sequence, explicitly selects Release/CPU, bounds compilation, and installs the
Python bindings without build isolation after provisioning their dependencies.
Snapy uses its documented Gloo-only option (`UCX=OFF`); PNETCDF is also disabled.
The kintera source pin is v2.6.5, satisfying snapy's >=2.6.3 floor. Source version
metadata and native imports are checked after installation.

**Paddle migration:** the runtime now installs public Paddle
`a4cac94451ab5fc800735edb00180e98859a20c2` from `elijah-mullens/paddle`,
which permits Torch 2.10.0. The installed requirements are checked. The old pin
is cloned only for labeled old/new regression evidence, never installed into
the runtime. `environment/paddle_migration.py` exercises four cases with real
native thermodynamics/kinetics; its JSON distinguishes original-driver failures,
an explicitly labeled API-only compatibility adapter, and migrated values.
See [compatibility history and review boundary](paddle-compatibility.md).

**Figure values:** `python tools/check_figure_values.py` regenerates model inputs
and compares every figure's underlying data and plotted arrays/schematic geometry
against `environment/figure-values.json`. Missing inputs or figures fail. Eight
binary64 ULPs allow floating arithmetic/serialization roundoff only; status,
iteration counts, structure and strings are exact. Every changed leaf is reported
for chapter-owner review even if within this numerical threshold. This is not a
scientific acceptance tolerance. No SVG hash is used to establish equivalence.
The explicit `--write-baseline` maintenance option requires review; the audit
never invokes it or updates its reference. Nine figures are schematics and five
read model datasets; checking a schematic does not reproduce a GPU campaign.

Use `bash doc/tech-report/environment/reproduce.sh build` to stop after builds
and the environment smoke test. The default continues through derivation scripts,
provenance commands, examples, figure/table writers, shared gates and a full
HTML/PDF render without the committed Quarto freeze. Missing drivers and GPU-only
commands remain classified explicitly. Appendix A/B/C/D/E/F content reviews are
excluded because their reading guides are owner-authored; shared generators and
rendering still execute. The test-index refresh and render can change generated
files in this disposable checkout.

Logs, command/exit-code JSON and the extracted inventory are under
`.reproduce/logs/`. A zero command exit is **not** a numerical reproduction
verdict: compare the output with the chapter's stated tolerances. The runner exits
nonzero if an executed command fails and retains subsequent results for review.
It does not repair missing experiments, chapter content, or numerical outputs.
