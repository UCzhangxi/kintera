# Chapter 13 GPU probe integration

Starting report: `c2b14040028eab144e714b3a314593fa5d9289b3`. Scientific source:
`e357792d50639d68e9090b542edf038d2b029aa2`. Ownership and the numerical-comparison reproduction were recorded
[before edits on issue 101](https://github.com/UCzhangxi/kintera/issues/101#issuecomment-6381836702).

## Source identity and deviations

The supplied 120-line source extracted exactly to SHA256
`c04084548c55ef39dae2b7de1c7216d0e3236d5ab0b379da0110842cb325b5a2`, Git blob
`8d4db4234fa3759782e1a60bb9f8c74046da4015`. That original is retained in the implementation evidence.
The integrated source SHA256 is `a8a9bb435438ecae7abcd6b18ecd57e7641fb164cb854985a4dfcb354f35b0b5`.

Independent review found that `max(0., nan)` hides a nonfinite result in the original accumulator. Tensor
broadcasting could also hide incompatible shapes. The regression suite failed **8 of 13** cases against the
supplied source and passes **13 of 13** against the integrated source, on both the retained CPU installation and
the new CUDA installation. Invalid shapes and nonfinite data now produce an infinite error, hence FAIL. The
finite error formula, seed, decks, 64 cells, 10-second step and `1e-13` tolerance are unchanged. Additional
changes validate finite/nonnegative tolerance and finite/positive step, clean temporary YAML files, and document
the original absolute-error fallback for an all-zero CPU reference. No scientific source or baseline changed.

## Separate measurements

| Measurement | Environment | Largest relative error | Exit | Attribution |
|---|---|---:|---:|---|
| Supplied original probe | GTX 1080 Ti; Torch 2.10.0+cu126; CUDA 12.6; source e357792d | 5.08e-16 | 0 | Supplied review output; not executed here |
| Original probe, new run | Quadro RTX 4000; Torch 2.10.0+cu128; compiler CUDA 12.9.86 / runtime 12.8; source e357792d | 5.08e-16 | 0 | New local CUDA execution |
| Corrected probe, new run | Same RTX 4000 source build | 5.08e-16 | 0 | New local execution; stdout byte-identical to original probe on this device |
| Corrected probe, GPU hidden | Same CUDA installation, `CUDA_VISIBLE_DEVICES=` | Nothing compared | 3 | New local execution; **not PASS** |

The chapter quotes only the new RTX 4000 run, committed as
`src/kintera_report/ch13/runs/gpu_probe-rtx4000.out`; no-GPU stdout is in `gpu_probe-no-gpu.out`.
The maximum is the pressure-switch implicit step (output line 9; summary line 10). Rates/constants/Jacobians
have a maximum of 1.15e-16 (line 6), and the switched constants and Jacobian are bitwise equal (lines 7-8).
These limited cases are not proof of universal GPU correctness or coverage of every native-suite assertion.

## Build and execution

A clean checkout at the scientific pin followed the README configure/build/install sequence:

```sh
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCUDA=ON -DNETCDF=ON -DCMAKE_CUDA_ARCHITECTURES=75
cmake --build build --parallel 4
python -m pip install . --no-build-isolation --no-deps --target <isolated-target>
```

All three commands completed successfully. The source CMakeLists.txt overrides the requested architecture with
its supported list (60, 61, 70, 75, 80, 86, 89, 90, 120); this effective configuration is retained, not patched.
CUDA compiler 12.9.86, GCC 12.2.0, Python 3.11.13, source-built Kintera 2.6.7, Torch 2.10.0+cu128, driver 610.57.04.
The imported module path was verified to belong to the isolated CUDA target. The retained CPU installation was
not edited or replaced. No scientific source files differ from the pin.

From `doc/tech-report`, with `PYTHONPATH` pointing to that target and `KINTERA_REPO` to the pinned checkout:

```sh
CUDA_VISIBLE_DEVICES=0 python -P src/kintera_report/ch13/runs/gpu_probe.py
CUDA_VISIBLE_DEVICES= python -P src/kintera_report/ch13/runs/gpu_probe.py
python -m pytest tools/tests/test_gpu_probe.py -q -p no:cacheprovider
```

Results: exits 0 / 3 / 0; the final command passes 13 tests. The CUDA-enabled source's related native Python
checks also pass **200/200**, launched from the source root:

```sh
python -m pytest tests/test_evaporation_kessler.py tests/test_coagulation_pressure_switch.py tests/test_evaporation_general.py -q -p no:cacheprovider
```

The first native-check invocation used the report directory and had 199 passes plus one missing relative
`tests/earth.yaml` failure. Correcting only the working directory produced 200 passes in 8.89 seconds; that first
log remains retained. This was a harness error, not a scientific-source fix.

## Content and audit boundaries

Three content checks failed before integration (missing probe, obsolete uncommitted/unreproduced wording,
old probe provenance) and pass after integration. The paragraph and footnote now describe the committed probe
and the measured RTX 4000 result. Other historical footnotes are unchanged. CPU reproduction still classifies
`gpu_probe` as GPU-only; the separately measured no-GPU exit is not counted as a numerical pass.

The complete fresh 128-command reproduction remains evidence at report
`a5c3bd46a6ac95996d5a980ccc1676678b12237d`, exit 1 with seven failures. This scoped correction does not claim a new
complete audit. Its final-head report/render/CI results are returned in the implementation ledger. #100, original
evidence, figure baselines, strict invariant inputs and tolerances remain unchanged. Historical provenance and
ratchet failures, chapter 12 continuation, chapter 14 interpretation and package-script bugs remain open.
Independent chapter-owner recheck is needed; no approval, readiness or merge is claimed.
