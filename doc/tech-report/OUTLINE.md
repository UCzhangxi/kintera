# kintera Technical Report: outline (DRAFT for discussion)

> Status: **draft chapter list for the chapter authors to discuss**, not an approved plan. Built from kintera's own
> source tree at the code pin (`code_pin.yml`, chengcli/kintera). Every path below exists at that pin (checked by
> listing the tree). Binding style: `STYLE.md`. Symbols: `NOTATION.md`.

## How to read this outline

- **Chapter by chapter.** Each chapter lists the source files it covers, the tests that exist for it at the pin,
  and its derivation status. The authors split each chapter into schemes (`#### N.M`), each with the six layers of
  STYLE.md 2 (summary, derivation, numerical method, code, tests, limits), and fill the derivation status.
- **Derivation status** is `unknown` everywhere in this draft: nobody has yet checked which schemes have a
  step-by-step derivation in a published source and which must be derived on the page.
- **Tests.** "registered" means `tests/CMakeLists.txt` adds the test to `ctest` at the pin: C++ tests through
  `setup_test(...)`, Python tests through the `test*.py` glob (eight of them share one `test_python_subprocess`
  entry). A C++ file listed as "not registered" is in `tests/` but no `setup_test` line builds it.
- Each chapter becomes `book/chapters/NN-slug.qmd`, with one section file per scheme,
  `book/chapters/NN-slug/_<scheme>.qmd` (STYLE.md 2 and 10.1). Today every chapter file is a stub.
- Paths are relative to the kintera repository root.

## Outline at a glance

| # | chapter | main source | tests at the pin |
|---|---|---|---|
| 1 | Overview and quick start | `README.md`, `src/`, `python/`, `examples/` | examples only |
| 2 | Species and thermodynamic data | `src/species.*`, `src/thermo/nasa9.hpp`, `src/thermo/log_svp.*`, `src/vapors/`, `data/` | 7 |
| 3 | Equation of state and thermodynamic functions | `src/thermo/thermo*.{hpp,cpp}`, `src/thermo/eval_uhs.*` | 5 (+5 not registered) |
| 4 | Phase equilibrium of multiple condensables | `src/thermo/equilibrate_tp.h`, `src/thermo/equilibrate_uv.h`, `src/thermo/nucleation.*` | 12 (+1 not registered) |
| 5 | Multiphase chemical equilibrium | `src/equilibrium/` | 3 |
| 6 | Kinetics | `src/kinetics/`, `src/reaction.*` | 17 |
| 7 | Photochemistry | `src/photochem/` | 6 |
| 8 | Diffusion | `src/diffusion/` | 1 |
| 9 | The two-dimensional atmosphere solver | `python/atm2d/` | 3 |
| 10 | Numerical solvers | `src/math/` | 1 |
| 11 | YAML configuration and the Python/C++ API | `src/utils/parse_yaml.*`, `python/csrc/`, `python/kintera.pyi` | 4 |
| 12 | GPU execution | `*.cu`, `*_dispatch.*`, `src/loops.cuh` | 1 |
| 13 | Tests and validation | `tests/`, `examples/` | all |
| 14 | Coupling to snapy and paddle | the public API of chapters 3, 4, 6, 11 | none in kintera |
| A-F | Appendices: notation, derivation index, test index, topic index, task map, glossary | generated (`tools/`) | |

## Chapter 1. Overview and quick start

- **Covers:** what kintera computes (thermodynamics, phase and chemical equilibrium, kinetics, photochemistry,
  diffusion) for a mixture of gases and condensates; the code map; build and install; a first run.
- **Source files:** `README.md`, `CMakeLists.txt`, `setup.py`, `pyproject.toml`, `src/CMakeLists.txt`,
  `src/constants.h`, `src/kintera_formatter.hpp`, `src/add_arg.h`, `python/__init__.py`, `examples/example_earth.py`,
  `examples/example_earth_dry.py`, `examples/example_jupiter.py`, `examples/example_jupiter_adiabat.py`,
  `examples/example_chapman_cycle.py`.
- **Tests:** none of its own; the examples above are the quick-start runs.
- **Derivation status:** unknown.

## Chapter 2. Species and thermodynamic data

- **Covers:** the species registry; molar masses and composition strings; NASA polynomials for heat capacity,
  enthalpy and entropy; saturation vapor pressure fits and their autograd form; units.
- **Source files:** `src/species.cpp`, `src/species.hpp`, `src/thermo/nasa9.hpp`, `src/thermo/log_svp.cpp`,
  `src/thermo/log_svp.hpp`, `src/thermo/svp_eval.h`, `src/vapors/vapor_functions.h`, `src/vapors/ammonia.dat`,
  `src/vapors/fit_ammonia.py`, `data/nasa9.dat`, `python/data/nasa9.dat`, `python/equilibrium/nasa9.py`,
  `src/utils/molar_mass.cpp`, `src/utils/molar_mass.hpp`, `src/utils/parse_comp_string.cpp`,
  `src/utils/parse_comp_string.hpp`, `src/units/units.cpp`, `src/units/units.hpp`, `src/constants.h`.
- **Tests (registered):** `test_species` (`tests/test_species.cpp`), `test_vapor_functions`
  (`tests/test_vapor_functions.cpp`), `tests/test_species_registry.py`, `tests/test_nasa9_cp.py`,
  `tests/test_h2_cp.py`, `tests/test_inline_svp.py`, `tests/test_svp_autograd.py`.
- **Derivation status:** unknown.

## Chapter 3. Equation of state and thermodynamic functions

- **Covers:** the mixture's equation of state; internal energy, enthalpy, entropy and heat capacities of gas and
  condensates; the two state representations (mole fractions, `ThermoX`; mass fractions, `ThermoY`); relative
  humidity; adiabat extrapolation.
- **Source files:** `src/thermo/thermo.hpp`, `src/thermo/thermo_x.cpp`, `src/thermo/thermo_y.cpp`,
  `src/thermo/thermo_options.cpp`, `src/thermo/thermo_prop.hpp`, `src/thermo/thermo_formatter.hpp`,
  `src/thermo/eval_uhs.cpp`, `src/thermo/eval_uhs.hpp`, `src/thermo/extrapolate_ad.cpp`,
  `src/thermo/relative_humidity.cpp`, `src/thermo/relative_humidity.hpp`.
- **Tests (registered):** `test_thermo` (`tests/test_thermo.cpp`), `tests/test_latent_heat_sign.py`,
  `tests/test_effective_cp_heap_state.py`, `tests/test_jupiter_tp_adiabat.py`,
  `tests/test_reference_state_keys.py`.
- **Tests (not registered):** `tests/test_earth_thermo.cpp`, `tests/test_jup_thermo.cpp`,
  `tests/test_moist_adiabat.cpp`, `tests/test_convective_adjustment.cpp`, with their inputs
  `tests/test_moist_adiabat.inp`, `tests/test_convective_adjustment.inp`.
- **Derivation status:** unknown.

## Chapter 4. Phase equilibrium of multiple condensables

- **Covers:** saturation adjustment at given temperature and pressure and at given internal energy and volume, with
  several condensables at once; the active-set choice of which phases are present; nucleation switches; warm
  starts; failure reporting. Expected to be the hardest chapter.
- **Source files:** `src/thermo/equilibrate_tp.h`, `src/thermo/equilibrate_uv.h`, `src/thermo/nucleation.cpp`,
  `src/thermo/nucleation.hpp`, `src/thermo/thermo_dispatch.cpp`, `src/thermo/thermo_dispatch.hpp`,
  `src/thermo/thermo_x.cpp`, `src/thermo/thermo_y.cpp`, `src/math/leastsq_kkt.h`, `src/math/constrained_newton.h`.
- **Tests (registered):** `test_equilibrate_tp_max_iter` (`tests/test_equilibrate_tp_max_iter.cpp`),
  `test_alloc_space` (`tests/test_alloc_space.cpp`, the `equilibrate_uv` workspace case),
  `tests/test_equilibrate_uv_gain.py`, `tests/test_saturation_adjustment_nh4sh.py`,
  `tests/test_saturation_degenerate_bound.py`, `tests/test_saturation_failure_reported.py`,
  `tests/test_warm_start_shape.py`, `tests/test_thermo_x_warm_start_shape.py`,
  `tests/test_thermo_default_nucleation.py`, `tests/test_thermo_none_nucleation.py`,
  `tests/test_thermo_none_nucleation_after_reset.py`, `tests/test_thermo_y_none_nucleation.py`.
- **Tests (not registered):** `tests/test_ammonium_hydrosulfide.cpp` (input `tests/test_ammonium_hydrosulfide.inp`).
- **Derivation status:** unknown.

## Chapter 5. Multiphase chemical equilibrium

- **Covers:** the equilibrium solver of `src/equilibrium/` (components, phases, reactions, the gas phase) and its
  options; equilibrium constants from NASA polynomials.
- **Source files:** `src/equilibrium/equilibrium.cpp`, `src/equilibrium/equilibrium.hpp`,
  `src/equilibrium/equilibrium_options.cpp`, `src/equilibrium/equilibrium_dispatch.cpp`,
  `src/equilibrium/equilibrium_dispatch.hpp`, `src/equilibrium/phase_equilibrate_tp.h`,
  `python/equilibrium/__init__.py`, `python/equilibrium/nasa9.py`, `examples/equilibrium_nasa9.py`,
  `examples/equilibrium_nasa9.yaml`.
- **Tests (registered):** `test_equilibrium` (`tests/test_equilibrium.cpp`), `tests/test_equilibrium.py`,
  `tests/test_reaction_equilibrium.py`.
- **Derivation status:** unknown.

## Chapter 6. Kinetics

- **Covers:** reactions and stoichiometry; rate constants (Arrhenius and its multi-range form, three-body and
  fall-off forms: Lindemann, Troe, SRI, KB); evaporation, including the Kessler form; coagulation; the pressure
  switch on Arrhenius-form rates; the Jacobian; implicit time integration; the `kinetics_base` reaction network
  reader.
- **Source files:** `src/reaction.cpp`, `src/reaction.hpp`, `src/kinetics/kinetics.cpp`, `src/kinetics/kinetics.hpp`,
  `src/kinetics/kinetics_options.cpp`, `src/kinetics/kinetics_formatter.hpp`, `src/kinetics/rate_constant.cpp`,
  `src/kinetics/rate_constant.hpp`, `src/kinetics/arrhenius.cpp`, `src/kinetics/arrhenius.hpp`,
  `src/kinetics/three_body.cpp`, `src/kinetics/three_body.hpp`, `src/kinetics/lindemann_falloff.cpp`,
  `src/kinetics/lindemann_falloff.hpp`, `src/kinetics/troe_falloff.cpp`, `src/kinetics/troe_falloff.hpp`,
  `src/kinetics/sri_falloff.cpp`, `src/kinetics/sri_falloff.hpp`, `src/kinetics/kb_falloff.cpp`,
  `src/kinetics/kb_falloff.hpp`, `src/kinetics/evaporation.cpp`, `src/kinetics/evaporation.hpp`,
  `src/kinetics/evaporation_extent.cpp`, `src/kinetics/evaporation_extent.hpp`, `src/kinetics/coagulation.cpp`,
  `src/kinetics/coagulation.hpp`, `src/kinetics/species_rate.hpp`, `src/kinetics/jacobian_kinetics.hpp`,
  `src/kinetics/jacobian_mass_action.cpp`, `src/kinetics/evolve_implicit.hpp`, `src/kinetics/evolve_implicit_impl.h`,
  `src/kinetics/evolve_implicit_dispatch.cpp`, `src/kinetics/evolve_implicit_dispatch.hpp`,
  `src/utils/stoichiometry.cpp`, `src/utils/stoichiometry.hpp`, `python/kinetics_base/__init__.py`,
  `python/kininput.py`, `python/chemtable.py`, `examples/example_na2s_evaporation.py`.
- **Tests (registered):** `test_reaction` (`tests/test_reaction.cpp`), `test_kinetics` (`tests/test_kinetics.cpp`),
  `test_falloff` (`tests/test_falloff.cpp`), `test_kinetics_base` (`tests/test_kinetics_base.cpp`),
  `tests/test_kinetics_base.py`, `tests/test_kinetics_base_units.py`, `tests/test_kinetics_null_options.py`,
  `tests/test_multirange_arrhenius.py`, `tests/test_multirange_arrhenius_yaml.py`, `tests/test_rate_constant_ddC.py`,
  `tests/test_evaporation_general.py`, `tests/test_evaporation_inputs.py`, `tests/test_evaporation_kessler.py`,
  `tests/test_evaporation_extent.py`, `tests/test_coagulation_pressure_switch.py`, `test_alloc_space`
  (`tests/test_alloc_space.cpp`, the `leastsq_kkt` cases), `tests/test_earth.py`.
- **Tests (not registered):** `tests/test_kinetics_rates.cpp` (its line in `tests/CMakeLists.txt` is commented out).
- **Derivation status:** unknown.

## Chapter 7. Photochemistry

- **Covers:** photolysis cross sections and their readers (YAML, KINETICS7 format); actinic flux; photolysis rates
  and their Jacobian; the Chapman cycle and CH4 photolysis cases.
- **Source files:** `src/photochem/photochem.cpp`, `src/photochem/photochem.hpp`, `src/photochem/photolysis.cpp`,
  `src/photochem/photolysis.hpp`, `src/photochem/actinic_flux.hpp`, `src/photochem/jacobian_photolysis.cpp`,
  `src/photochem/jacobian_photolysis.hpp`, `src/photochem/load_xsection.hpp`,
  `src/photochem/load_xsection_kin7.cpp`, `src/photochem/load_xsection_yaml.cpp`,
  `src/photochem/kinetics_base_reader.cpp`, `src/photochem/kinetics_base_reader.hpp`, `data/chapman_cycle.yaml`,
  `data/ch4_photolysis.yaml`, `python/atm2d/radiation.py`.
- **Tests (registered):** `test_photolysis_options` (`tests/test_photolysis_options.cpp`), `test_photolysis_kinetics`
  (`tests/test_photolysis_kinetics.cpp`), `test_actinic_flux` (`tests/test_actinic_flux.cpp`), `test_ch4_photolysis`
  (`tests/test_ch4_photolysis.cpp`), `test_chapman_cycle` (`tests/test_chapman_cycle.cpp`), `tests/test_photolysis.py`.
- **Derivation status:** unknown.

## Chapter 8. Diffusion

- **Covers:** molecular and eddy diffusion coefficients and fluxes.
- **Source files:** `src/diffusion/diffusion.cpp`, `src/diffusion/diffusion.hpp`.
- **Tests (registered):** `test_diffusion` (`tests/test_diffusion.cpp`).
- **Derivation status:** unknown.

## Chapter 9. The two-dimensional atmosphere solver

- **Covers:** the Python solver of `python/atm2d/`: state, transport, chemistry and photochemistry sources, the
  implicit operator and its sparse system, the Rosenbrock and Newton steps, adaptive time steps, conservation of
  atoms and charge.
- **Source files:** `python/atm2d/__init__.py`, `python/atm2d/atm_state2d.py`, `python/atm2d/config.py`,
  `python/atm2d/transport.py`, `python/atm2d/chemistry.py`, `python/atm2d/radiation.py`, `python/atm2d/source.py`,
  `python/atm2d/assembly.py`, `python/atm2d/matrix.py`, `python/atm2d/solver.py`, `python/atm2d/rosenbrock.py`,
  `python/atm2d/timestep.py`, `python/atm2d/schedule.py`, `python/atm2d/pins.py`, `python/atm2d/conservation/`,
  `python/atm2d/newton/`, `python/atm2d/sources/`, `examples/plot_atm2d_steady_diffusion_dirichlet_2d.py`,
  `examples/plot_atm2d_steady_advection_diffusion.py`.
- **Tests (registered):** `tests/test_atm2d.py`, `tests/test_adaptive_timestep.py`, `tests/test_refactor_phase1.py`.
- **Derivation status:** unknown.

## Chapter 10. Numerical solvers

- **Covers:** the shared numerical kernels: LU decomposition and back-substitution, matrix inverse, least squares
  and its KKT form with constraints, the constrained Newton iteration, interpolation, the sparse solver.
- **Source files:** `src/math/core.h`, `src/math/ludcmp.h`, `src/math/lubksb.h`, `src/math/luminv.h`,
  `src/math/leastsq.h`, `src/math/leastsq_kkt.h`, `src/math/constrained_newton.h`, `src/math/psolve.h`,
  `src/math/swap.h`, `src/math/interpolation.cpp`, `src/math/interpolation.hpp`, `src/math/sparse_solver.hpp`,
  `src/math/sparse_solver.cu`, `python/csrc/pysparsesolver.cpp`.
- **Tests (registered):** `test_alloc_space` (`tests/test_alloc_space.cpp`: workspace budgets of `leastsq_kkt`).
- **Derivation status:** unknown.

## Chapter 11. YAML configuration and the Python/C++ API

- **Covers:** the YAML input format and its parser; the options objects (`ADD_ARG`); resource lookup; the Python
  bindings and the type stubs; version handling.
- **Source files:** `src/add_arg.h`, `src/utils/parse_yaml.cpp`, `src/utils/parse_yaml.hpp`,
  `src/utils/find_resource.cpp`, `src/utils/find_resource.hpp`, `src/utils/get_value.hpp`, `src/utils/suggest.cpp`,
  `src/utils/suggest.hpp`, `src/utils/serialize.cpp`, `src/utils/serialize.hpp`, `python/csrc/kintera.cpp`,
  `python/csrc/pythermo.cpp`, `python/csrc/pykinetics.cpp`, `python/csrc/pyequilibrium.cpp`,
  `python/csrc/pyphotolysis.cpp`, `python/csrc/pydiffusion.cpp`, `python/csrc/pyconstants.cpp`,
  `python/csrc/pyoptions.hpp`, `python/kintera.pyi`, `python/STUB_FILES.md`, `python/api/__init__.py`,
  `tests/jupiter.yaml`, `tests/earth.yaml`, `tests/sample_reaction.yaml`.
- **Tests (registered):** `tests/test_version_fallback.py`, `tests/test_version_floor.py`,
  `tests/test_kinetics_null_options.py`, `tests/test_species_registry.py`.
- **Tests (not registered):** `tests/test_yaml_parse.cpp` (its line in `tests/CMakeLists.txt` is commented out);
  `tests/validate_stub_file.py` and `examples/test_type_hints.py` are scripts, not ctest entries.
- **Derivation status:** unknown.

## Chapter 12. GPU execution

- **Covers:** how one call runs on CPU or CUDA: the dispatch stubs, the CUDA loops, per-thread workspaces.
- **Source files:** `src/loops.cuh`, `src/func_table.cpp`, `src/func_table.cu`, `src/thermo/thermo_dispatch.cu`,
  `src/equilibrium/equilibrium_dispatch.cu`, `src/kinetics/evolve_implicit_dispatch.cu`,
  `src/utils/utils_dispatch.cpp`, `src/utils/utils_dispatch.cu`, `src/utils/utils_dispatch.hpp`,
  `src/utils/user_funcs.cu`, `src/utils/user_funcs.hpp`, `src/utils/alloc.h`, `src/math/sparse_solver.cu`,
  `tests/device_testing.hpp`.
- **Tests (registered):** `tests/test_cuda_workspace.py` (skipped without CUDA).
- **Derivation status:** unknown.

## Chapter 13. Tests and validation

- **Covers:** how the test suite is organised and run; what each validation case compares against (reference
  data, analytic limits, other codes); the VULCAN and KINETICS7 comparison cases.
- **Source files:** `tests/CMakeLists.txt`, `tests/device_testing.hpp`, `tests/vulcan/`, `tests/kinetics_base/`,
  `examples/`.
- **Tests (registered):** all of the above chapters; Appendix C lists every `ctest` entry at the pin.
- **Derivation status:** unknown.

## Chapter 14. Coupling to snapy and paddle

- **Covers:** what the hydrodynamic code snapy and the driver paddle call in kintera (thermodynamics, saturation
  adjustment, kinetics), which state they pass and which conventions both sides must agree on.
- **Source files:** the public API of chapters 3, 4, 6 and 11 (`src/thermo/thermo.hpp`, `src/kinetics/kinetics.hpp`,
  `python/csrc/pythermo.cpp`, `python/csrc/pykinetics.cpp`); the calling side lives in chengcli/snapy and
  chengcli/paddle (STYLE 3.1 lists them).
- **Tests:** none in kintera.
- **Derivation status:** unknown.

## Chapter 15. Appendices

- **A. Notation** (`appa-notation.qmd`), generated from `NOTATION.md` by `tools/gen_notation_index.py`.
- **B. Derivation index** (`appb-derivations.qmd`), generated from the chapters' Derivation layers by
  `tools/gen_derivation_index.py`.
- **C. Test index** (`appc-test-index.qmd`), generated from `tools/ctest-index.json` by `tools/gen_test_index.py`.
- **D. Topic index** (`appf-topic-index.qmd`), generated from `tools/topic-index.yaml` by `tools/gen_topic_index.py`.
- **E. Task map** (`appg-task-map.qmd`), generated from `tools/task-map.yaml` by `tools/gen_task_map.py`.
- **F. Glossary** (`apph-glossary.qmd`), generated from `tools/reader-glossary.json` by
  `tools/gen_glossary_appendix.py`.

The appendix files keep the letters of the generators' output names (`appf`, `appg`, `apph`); the book letters them
A to F in this order.
