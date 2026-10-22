# Reproduction environment

From a fresh checkout, on a Linux x86-64 machine with Git and Docker Engine:

```bash
bash doc/tech-report/environment/reproduce.sh
```

Allow at least 32 GiB RAM and 80 GiB free disk space. The build uses two compiler
jobs and runs CPU checks. No GPU result is inferred from a CPU build. Docker must
be accessible to the invoking account. The command does not install packages on
the host. Network access to public GitHub, PyPI and Debian snapshots is required.

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

**Unresolved dependency:** Paddle's current public pin requires Torch <=2.7.1,
whereas these kintera/snapy source builds require Torch 2.10.0. Its source is
checked out for citations, but its runtime is not installed in the main
environment. A passing main-environment `pip check` does not establish Paddle
compatibility. A compatible public Paddle pin or an explicitly separate legacy
runtime is still required to close this part of the reproduction gap.

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
