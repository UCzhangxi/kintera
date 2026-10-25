# Round 3 source-pin review

Base report: `fb86705d6726ab5398301c7accda064affb7b35e` (draft #100), stacked on `fix/report-environment-99`.
Report baseline: `68fea828ca5c6a0cffd22ca7a103c2bbcc960b34`.
Scientific source: `0d9f67f97d841147e23283d2dcdab302238d2c45` → `e357792d50639d68e9090b542edf038d2b029aa2`.
The new source is the public merge of chengcli/kintera #151, following #150.

This is a scientific-source migration, separate from #100's environment setup.
No chapter-owner or reviewer approval is implied by a changed pin or a passing check.
The six owner-authored appendix content exclusions remain in force.

## Supplied invariant specification

The lead supplied the full 2603 definition in the continuation: exact zero rates,
1000-step nonnegativity, source-floor inventory, many-step atom/energy budgets
at 1e-12 relative per step and actual-source break tests. See
[invariant inputs and definitions](invariants/README.md). Per-occurrence source
guard effect coverage remains explicitly incomplete; no missing specification
is now claimed.

## Chapter continuations

The chapter 12 owner's public head `abc96e3f486942568d0a058722ad56c73a0f4b47` was resolved and inspected
but is not incorporated here. Its chapter-12 drivers and claims remain the chapter owner’s work; they
need reconciliation against the new scientific source before integration. The reported
The chapter 4/5/13 owner commits `81f803c97ae425fc1710661424b8b3c1d1373a50` and
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

## Measured CPU changes and strict regressions

These are development source-build measurements, pending the committed fresh-clone audit.
The old leg uses source `0d9f67f97d841147e23283d2dcdab302238d2c45`; the new leg uses
`e357792d50639d68e9090b542edf038d2b029aa2` (installed Kintera 2.6.7, Torch 2.10.0).
The exact tests are `python derivation-checks/check_ch4_uv.py`,
`python derivation-checks/check_ch4_tp.py`, and `python derivation-checks/check_ch6_jacobian.py`.
Each tightened check exits 1 at the old source and 0 at the new source. No tolerance was relaxed.

| Check | Old | New | Unchanged acceptance |
|---|---|---|---|
| UV near-reference starts | 3/7 fail, including 302 K returning 302 K | 0/7 fail; 302 K returns 304.80206565 K; worst error 3.4e-13 K | converged and temperature error ≤1e-9 K |
| TP cold starts 130–250 K | default cap 10; 12/13 fail | upstream default cap 100; 0/13 fail | zero nonconverged cells |
| Reverse-rate Jacobian | worst relative error 5.859e9 | 8.915e-9 | ≤1e-8 |
| EOS cloud at zero dry fraction | infinity | 4.4545330709435165 mol/m³; relative error zero | ≤1e-13 |
| Current native test inventory | 49 entries | 52 entries | generated from configured source, not an assertion of test success |

The 17 recorded derivation outputs contain 30 old EXPECTED-FAIL measurement lines and
8 new ones (summary lines excluded): 21 now pass, and one removed `mmdot_t` API is
explicitly REMOVED rather than counted as passing. Remaining findings are K16 (PXS),
S7-1/S7-2 (photolysis), S10-2/S10-3/S10-4 (dense), S10-7 (interpolation), and S14-1
(coupling). Their assertions and tolerances remain unchanged.

| Script | Old EXPECTED-FAIL lines | New EXPECTED-FAIL lines |
|---|---:|---:|
| `check_ch3_eos.py` | 1 | 0 |
| `check_ch3_condensate_entropy.py` | 2 | 0 |
| `check_ch3_reference.py` | 2 | 0 |
| `check_ch3_adiabat.py` | 1 | 0 |
| `check_ch3_adiabat_slope.py` | 1 | 0 |
| `check_ch3_pxs.py` | 3 | 1 |
| `check_ch3_thermo_y.py` | 2 | 0 |
| `check_ch4_tp.py` | 1 | 0 |
| `check_ch4_uv.py` | 1 | 0 |
| `check_ch6_rates.py` | 1 | 0 |
| `check_ch6_jacobian.py` | 1 | 0 |
| `check_ch6_evaporation.py` | 0 | 0 |
| `check_ch07_photolysis.py` | 4 | 2 |
| `check_ch9_budget_below1.py` | 3 | 0 |
| `check_ch10_dense.py` | 5 | 3 |
| `check_ch10_interp.py` | 1 | 1 |
| `check_ch14_coupling.py` | 1 | 1 |

The full old/new value diff is in [SOURCE-PIN-VALUES.md](SOURCE-PIN-VALUES.md).
These numbers require chapter-owner review; the chapter 4 owner covers chapter 4, and the two designated reviewers cover
chapter 14. Ownership for changed values in chapters 3, 6, 7, 9 and 10 needs routing;
no author approval is claimed. Chapter 12 remains with its designated owner, and the chapter 4/5/13 owner's
chapter 5 acceptance and chapter 13 GPU continuation remain separate owner evidence.
Historical provenance is intentionally retained at the source actually measured until
the corresponding claim is independently rerun or its owner migrates it. Consequently,
this draft does not yet represent a fully reconciled current-source narrative.
