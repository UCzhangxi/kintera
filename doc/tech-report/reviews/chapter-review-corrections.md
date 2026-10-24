# Chapter 4/5/13 correction follow-up

This follow-up starts from report `a5c3bd46a6ac95996d5a980ccc1676678b12237d` and keeps the scientific source
at `e357792d50639d68e9090b542edf038d2b029aa2`. The completed fresh audit (128 commands, seven nonzero exits)
belongs to that report revision. It is retained evidence, not a new full audit of this follow-up.

Ownership and reproduction were recorded on [issue 101](https://github.com/UCzhangxi/kintera/issues/101#issuecomment-6381701171)
before editing. The independent before/after content check failed all five checks before correction and passed
all five afterward. No numerical output, figure baseline, scientific tolerance or source pin changed.

| Reviewer point | Disposition | Evidence / correction |
|---|---|---|
| Ch4 TP says YAML max-iter (10) | Corrected | `src/thermo/thermo.hpp:80` and `src/thermo/thermo_options.cpp:92` at the source pin define 100; text uses 100. Existing TP output lines 35-36 remains unchanged. |
| Ch5 residual row differs between x86 builds | Corrected attribution | Kept `1.2e-16`, `1.8e17`, `4.9e-15` from our committed output lines 26-27 and identified Intel Xeon E-2236. A new execution matches these values. The peer's `1.6e-17`, `1.4e18`, `5.5e-15` are reported measurements on AMD Ryzen 9 7950X, not independent measurements here. No claim of a universal x86 value or validated architecture-wide range. |
| Ch5 footnote mixes 2.6.7/current source and 2.6.5/old source | Corrected | Separate current Xeon run record from retained arm64 record. Do not upgrade the arm64 evidence to the new pin. |
| Ch5 Pref docstring says 101325 | Corrected | Source `src/kinetics/kinetics.hpp:62` defines 1e5 Pa. Updated docstring; rerun line g retains default 100000 Pa, ratio 1.000000 and relative difference 0.0. |
| Ch13 inventory rows 1/2/4/6 | Corrected | New static `device_inventory.py` and committed JSON reproduce 43 total files, 20 containing literal `cuda`, 23 without. No CUDA execution is implied. |
| Ch13 probe rows 3/5 | Open | Handoff identifies SHA256 `c04084548c55ef39dae2b7de1c7216d0e3236d5ab0b379da0110842cb325b5a2` and Git blob `8d4db4234fa3759782e1a60bb9f8c74046da4015`; neither the probe file nor object was available in the retained workspace. The Markdown contains descriptions and reported output, not executable source. No substitute script or unexecuted CUDA result is presented as integration. |
| Ch13 old-pin references | Partly corrected | The remeasured static-inventory footnote moves to the scientific pin. Probe and other historical source records remain unchanged pending actual replacement evidence. |

The probe's reported `5.08e-16` measurement on a GTX 1080 Ti is peer evidence only. The existing local source-built
environment reports `torch.cuda.is_available() == False`; this correction pass does not claim a CUDA rerun.
The source attachment (or a public commit containing that exact blob) and a compatible CUDA source build are
needed to complete probe integration and validation. The retained historical probe paragraph is not silently
relabelled as a current measurement.

## Executable inventory

From `doc/tech-report`, with `KINTERA_REPO` at the scientific pin:

```sh
python -P src/kintera_report/ch13/runs/device_inventory.py "$KINTERA_REPO" --check src/kintera_report/ch13/runs/device_inventory.json
```

The command compares source identity and the entire list, not only the count. A deliberately stale JSON with
`cuda_named_count: 14` exits 1; the committed inventory exits 0. Its definition is case-sensitive substring
matching in `tests/test*.py`, equivalent to the documented grep, including comments and skipped tests. This
is not per-assertion device coverage.

## Evidence boundaries

The source build, strict 1000-step invariant checks, 138/138 guard coverage, 14/14 numerical figures and complete
native suites at the starting head remain retained evidence. Scientific source and their inputs are unchanged.
The affected chapter check, static inventory, report checks and rendering are rerun for this correction; the
final returned ledger identifies their exact report head and exits. Historical provenance and ratchet findings
remain failures. No owner approval, ready marking, merge or release is claimed; #100 remains unchanged.
