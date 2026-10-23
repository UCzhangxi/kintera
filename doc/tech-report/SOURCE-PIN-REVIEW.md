# Round 3 source-pin review

Base report: `fb86705d6726ab5398301c7accda064affb7b35e` (draft #100), stacked on `fix/report-environment-99`.
Report baseline: `68fea828ca5c6a0cffd22ca7a103c2bbcc960b34`.
Scientific source: `0d9f67f97d841147e23283d2dcdab302238d2c45` → `e357792d50639d68e9090b542edf038d2b029aa2`.
The new source is the public merge of chengcli/kintera #151, following #150.

This is a scientific-source migration, separate from #100's environment setup.
No chapter-owner or reviewer approval is implied by a changed pin or a passing check.
The six owner-authored appendix content exclusions remain in force.

## Missing requested specification

The phrase “invariant checks of 2603” has no recovered specification in the available
repository, issue #54, PR #150/#151, supplied handoffs, or retained workspace Markdown.
Search hits for the digits in SVG paths are unrelated. The exact referenced message or
issue, the invariant statements, inputs and acceptance tolerances are needed. They have
been requested; existing upstream regressions are not being relabeled as “2603”.

## Chapter continuations

Tianhao's public head `abc96e3f486942568d0a058722ad56c73a0f4b47` was resolved and inspected
but is not incorporated here. Its chapter-12 drivers and claims remain his work; they
need reconciliation against the new scientific source before integration. The reported
Linfeng commits `81f803c97ae425fc1710661424b8b3c1d1373a50` and
`17f1178a32b911c675167662fbd8e050435002d5` were unavailable in this checkout/public fork;
the supplied report is context, not incorporated code or new execution evidence.
The round-3 UV regression concerns convergence at the new pin, not a duplicate GPU probe.

## Removed-symbol citations

| Before | Current source / disposition | Claim change |
|---|---|---|
| `src/kinetics/jacobian_mass_action.cpp:KineticsImpl::_jacobian_mass_action` | `src/kinetics/kinetics.cpp:KineticsImpl::jacobian` | The private helper is absent; the active derivative lives in the public Jacobian method. This is not a renamed helper. |
| `src/math/core.h:mmdot_t` | `src/math/core.h` | The unused transpose-product API is absent. Check (f) asserts its absence and reports REMOVED, not a numerical PASS. |

## Changed cited bodies

The pin tool resolved 1,019 citations (356 distinct) with zero unresolved symbols after
the two mappings above. This list is the review floor; runtime output changes also need
review. Historical provenance and unexecuted claims are not silently reassigned to the
new pin. Gate failures caused by unresolved claim migration remain visible.

```text
# 356 cited symbols; 47 changed body between 0d9f67f97d84 and e357792d5063 (re-read these); 0 do not resolve at e357792d5063
changed	{{< code examples/jupiter.yaml >}}	file
changed	{{< code python/atm2d/chemistry.py build_chemistry_jacobian >}}	L6-L35 -> L6-L38
changed	{{< code python/atm2d/conservation/atomic.py project_atomic_budget >}}	L79-L137 -> L79-L137
changed	{{< code python/atm2d/radiation.py _total_cross_section_by_species >}}	L90-L123 -> L90-L136
changed	{{< code python/atm2d/radiation.py compute_actinic_flux_disort >}}	L23-L87 -> L23-L87
changed	{{< code python/kintera.pyi >}}	file
changed	{{< code src/kinetics/arrhenius.cpp ArrheniusOptionsImpl::from_yaml >}}	L41-L168 -> L41-L168
changed	{{< code src/kinetics/arrhenius.hpp ArrheniusOptionsImpl >}}	L26-L115 -> L26-L115
changed	{{< code src/kinetics/kinetics.cpp KineticsImpl::forward_with_rate_constants >}}	L390-L543 -> L477-L628
changed	{{< code src/kinetics/kinetics.cpp KineticsImpl::jacobian >}}	L304-L378 -> L318-L465
changed	{{< code src/kinetics/kinetics.hpp KineticsImpl >}}	L79-L190 -> L79-L196
changed	{{< code src/kinetics/kinetics.hpp KineticsImpl::jacobian >}}	L134-L158 -> L134-L162
changed	{{< code src/kinetics/kinetics.hpp KineticsOptionsImpl >}}	L27-L76 -> L27-L76
changed	{{< code src/kinetics/kinetics.hpp KineticsOptionsImpl::Pref >}}	L62-L62 -> L62-L62
changed	{{< code src/math/core.h >}}	file
changed	{{< code src/math/leastsq_kkt.h leastsq_kkt_feasible_origin >}}	L528-L571 -> L564-L610
changed	{{< code src/math/leastsq_kkt.h leastsq_kkt_impl >}}	L131-L488 -> L132-L524
changed	{{< code src/photochem/kinetics_base_reader.cpp >}}	file
changed	{{< code src/photochem/kinetics_base_reader.cpp photochem_options_from_kinetics_base >}}	L1392-L1701 -> L1392-L1706
changed	{{< code src/photochem/load_xsection_kin7.cpp load_xsection_kin7 >}}	L12-L102 -> L12-L96
changed	{{< code src/photochem/load_xsection_yaml.cpp load_xsection_yaml >}}	L12-L36 -> L12-L38
changed	{{< code src/photochem/photolysis.cpp >}}	file
changed	{{< code src/photochem/photolysis.cpp PhotolysisImpl::get_effective_stoich >}}	L303-L317 -> L303-L322
changed	{{< code src/species.hpp SpeciesThermoImpl >}}	L45-L122 -> L45-L120
changed	{{< code src/thermo/equilibrate_uv.h >}}	file
changed	{{< code src/thermo/equilibrate_uv.h equilibrate_uv_partition >}}	L122-L244 -> L122-L252
changed	{{< code src/thermo/eval_uhs.cpp eval_entropy_R overload=1 >}}	L304-L364 -> L283-L344
changed	{{< code src/thermo/eval_uhs.cpp eval_entropy_R overload=2 >}}	L366-L460 -> L346-L446
changed	{{< code src/thermo/eval_uhs.cpp eval_h2cp >}}	L95-L148 -> L82-L108
changed	{{< code src/thermo/eval_uhs.cpp eval_nasa9 >}}	L44-L59 -> L52-L68
changed	{{< code src/thermo/nasa9.hpp nasa9_gibbs_RT >}}	L8-L63 -> L8-L66
changed	{{< code src/thermo/nucleation.cpp NucleationOptionsImpl::from_yaml >}}	L43-L107 -> L61-L126
changed	{{< code src/thermo/thermo.hpp ThermoOptionsImpl >}}	L39-L88 -> L39-L92
changed	{{< code src/thermo/thermo.hpp ThermoXImpl >}}	L275-L445 -> L279-L449
changed	{{< code src/thermo/thermo.hpp ThermoXImpl::forward >}}	L358-L369 -> L362-L373
changed	{{< code src/thermo/thermo_options.cpp >}}	file
changed	{{< code src/thermo/thermo_options.cpp ThermoOptionsImpl::from_yaml overload=2 >}}	L38-L252 -> L38-L287
changed	{{< code src/thermo/thermo_x.cpp ThermoXImpl::_entropy_to_temp >}}	L287-L318 -> L278-L321
changed	{{< code src/thermo/thermo_x.cpp ThermoXImpl::_xfrac_to_conc >}}	L320-L368 -> L323-L370
changed	{{< code src/thermo/thermo_x.cpp ThermoXImpl::forward >}}	L204-L270 -> L205-L261
changed	{{< code src/thermo/thermo_x.cpp ThermoXImpl::reset >}}	L38-L132 -> L38-L133
changed	{{< code src/thermo/thermo_y.cpp ThermoYImpl::forward >}}	L275-L383 -> L277-L398
changed	{{< code src/thermo/thermo_y.cpp ThermoYImpl::reset >}}	L38-L172 -> L39-L174
changed	{{< code src/utils/alloc.h leastsq_kkt_feasible_origin_space >}}	L128-L139 -> L128-L140
changed	{{< code tests/test_atm2d.py >}}	file
changed	{{< code tests/test_kinetics_base.cpp >}}	file
changed	{{< code tests/test_thermo.cpp >}}	file
code_pin.yml: 0d9f67f97d84 -> e357792d5063; run `check` to refresh _code_anchors.json
```
