Reading list for chapters 2-5 of the kintera Technical Report.
# PUBLIC_READING — deriving kintera's thermodynamics and phase equilibrium from public sources

Shareable. Built only from published literature and the public kintera source at commit
0d9f67f97d841147e23283d2dcdab302238d2c45 (read with `git show 0d9f67f:<path>`). Every DOI below resolves (checked
2026-10-18). Each item reads "to understand X, read Y and code Z". When a source and the code disagree, the code
at 0d9f67f is what the report must describe.

## References (with DOI)
- [LIO18] Li, C., Ingersoll, A. P., & Oyafuso, F. (2018). Moist adiabats with multiple condensing species: a new
  theory with application to giant-planet atmospheres. J. Atmos. Sci. 75, 1063-1072. doi:10.1175/JAS-D-17-0257.1
- [LC19] Li, C., & Chen, X. (2019). Simulating nonhydrostatic atmospheres on planets (SNAP): formulation,
  validation, and application to the Jovian atmosphere. ApJS 240, 37. doi:10.3847/1538-4365/aafdaa
- [PD16] Pierrehumbert, R. T., & Ding, F. (2016). Dynamics of atmospheres with a non-dilute condensible component.
  Proc. R. Soc. A (vol. 472, article 20160107). doi:10.1098/rspa.2016.0107
- [L69] Lewis, J. S. (1969). The clouds of Jupiter and the NH3-H2O and NH3-H2S systems. Icarus 10, 365-378.
  doi:10.1016/0019-1035(69)90091-8
- [BF02] Bryan, G. H., & Fritsch, J. M. (2002). A benchmark simulation for moist nonhydrostatic numerical models.
  Mon. Wea. Rev. 130, 2917-2928. doi:10.1175/1520-0493(2002)130<2917:ABSFMN>2.0.CO;2
- [E94] Emanuel, K. A. (1994). Atmospheric Convection. Oxford University Press. doi:10.1093/oso/9780195066302.001.0001
- [NW06] Nocedal, J., & Wright, S. J. (2006). Numerical Optimization, 2nd ed. Springer. doi:10.1007/978-0-387-40065-5
- [LH95] Lawson, C. L., & Hanson, R. J. (1995). Solving Least Squares Problems. SIAM. doi:10.1137/1.9781611971217

## 1. Species, phases and composition variables
- To understand why gases and condensates are tracked separately and why the gas-only total matters, read [PD16]
  (sections on the non-dilute regime) and [LIO18] §2. Then read the code: src/thermo/thermo_x.cpp:320-368 (the
  mole-fraction to concentration step; partial pressures use the gas-only sum) and src/thermo/thermo_y.cpp:405-422
  (mass-fraction to mole-fraction step, dry species implicit).
- To understand the phase ordering convention (gases first, then condensates), read
  docs/source/equilibrium_algorithms.rst:16-52.

## 2. Thermodynamic data and per-species functions
- To understand energies, enthalpies and heat capacities of gases vs condensates, read [E94] ch. 4 (moist
  thermodynamics). Then read src/thermo/eval_uhs.cpp:190-221 (cp; gases get the extra R),
  src/thermo/eval_uhs.cpp:266-302 (internal energy) and src/thermo/eval_uhs.cpp:462-489 (enthalpy; compare the gas and
  condensate branches).
- To understand reference states and where latent heat comes from, read docs/h2o_bryan_latent_heat.md:9-40
  (Kirchhoff form, with [BF02] as the reference), src/thermo/thermo_y.cpp:63-83 (offsets) and
  src/thermo/thermo_options.cpp:134-158 (sign check on the implied latent heat).
- To understand condensate entropy, read src/thermo/eval_uhs.cpp:421-455. The code computes it from the condition
  that each reaction's Gibbs energy change vanishes on the saturation curve; the Gibbs-energy reasoning is in
  [E94] ch. 4. Gas entropy is at src/thermo/eval_uhs.cpp:416-419.
- To understand mixture totals, read src/thermo/thermo.hpp:225-272 (ThermoY: U and S per volume) and
  src/thermo/thermo.hpp:390-426 (ThermoX: cp, H, S per volume).

## 3. Saturation vapour pressure, reaction by reaction
- To understand vapour-pressure fits, read [E94] ch. 4 (Clausius-Clapeyron) and [L69] for NH3, H2S and the
  NH4SH formation constant. Then read src/thermo/svp_eval.h:36-60 (three kinds of fit and their derivative),
  src/vapors/vapor_functions.h:12-24 (generic forms), src/vapors/vapor_functions.h:81-86 (NH4SH, a product of two
  partial pressures) and tests/jupiter.yaml:84-86.
- Note for writers: the code attaches the constant to a REACTION (a product of partial pressures with
  stoichiometric powers, in Pa units), see src/thermo/log_svp.cpp:13-41.

## 4. Equilibrium conditions with several condensables
- To understand the conditions (equality when the condensate exists, inequality allowed when it does not;
  amounts never negative), read [LIO18] §2-3 and docs/source/equilibrium_algorithms.rst:53-107 (signed quotient,
  phase conditions, TP equations). Code: src/thermo/equilibrate_tp.h:110-117 and src/thermo/equilibrate_tp.h:141-207.
- To understand the fixed-energy, fixed-volume form and its coupling to temperature, read
  docs/source/equilibrium_algorithms.rst:108-143 and the code src/thermo/equilibrate_uv.h:384-393 (constant in
  concentration units), src/thermo/equilibrate_uv.h:450-470 (which reactions are active),
  src/thermo/equilibrate_uv.h:556-593 (temperature solve).
- To understand the single-vapour-per-condensate shortcut, read docs/source/equilibrate_uv_partition.rst:1-118 and
  src/thermo/equilibrate_uv.h:29-244. Solver selection is at src/thermo/thermo_y.cpp:338-356.

## 5. The solution algorithm (constrained linear least squares)
- To understand the KKT conditions and active-set methods for inequality-constrained least squares, read [NW06]
  ch. 12 and 16 and [LH95] ch. 23 (NNLS and LSI). Then read src/math/leastsq_kkt.h:77-127 (square system solve),
  src/math/leastsq_kkt.h:317-408 (dropping and adding constraints) and src/math/leastsq_kkt.h:410-414 (termination).
- To understand how the equilibrium solver feeds it, read docs/source/equilibrium_algorithms.rst:144-175 and
  src/thermo/equilibrate_uv.h:482-505 (gain matrix and call) and src/thermo/equilibrate_uv.h:510-553 (step limiting).
- To understand stopping criteria and failure reporting, read docs/source/equilibrium_algorithms.rst:236-253,
  src/thermo/thermo_options.cpp:89-113 (max-iter, ftol, solver choice) and src/thermo/thermo_y.cpp:358-375.

## 6. Moist adiabats and the effective heat capacity
- To understand moist adiabats with several condensing species, read [LIO18] (the full paper) and [E94] ch. 4.
  Then read src/thermo/extrapolate_ad.cpp:13-68 (heat capacity that includes condensation's response to
  temperature), src/thermo/extrapolate_ad.cpp:70-176 (stepping in ln P) and src/thermo/extrapolate_ad.cpp:178-304
  (stepping in height).
- A worked deep-atmosphere example is in docs/source/jupiter_tp_adiabat.rst:75-172, with its test
  tests/test_jupiter_tp_adiabat.py:12-22.

## 7. Kinetics next to equilibrium
- To understand implicit (backward Euler) integration of stiff reaction systems, read [NW06] (Newton and linear
  systems background) or any stiff-ODE text. Then read src/kinetics/evolve_implicit_impl.h:54-91,
  src/kinetics/jacobian_mass_action.cpp:14-25 and src/kinetics/kinetics.cpp:326-376.
- To understand cloud microphysics closures (evaporation of falling condensate, Kessler-type conversion), read
  [BF02] (warm-rain setup) and [LC19] (Jovian microphysics in SNAP). Then read src/kinetics/evaporation.cpp:204-327
  and src/kinetics/coagulation.cpp:8-28.
- To understand where equilibrium and kinetics meet, read [LC19]: in the dynamical model, saturation adjustment and
  kinetic steps are applied by the host code. kintera's kinetics module does not call the equilibrium solvers.

## 8. Validation entry points
- tests/test_jupiter_tp_adiabat.py:12-22, tests/test_saturation_adjustment_nh4sh.py:50-69,
  tests/test_equilibrate_uv_gain.py:59-70, tests/test_thermo.cpp:28-64, tests/test_h2_cp.py:51-57,
  tests/test_latent_heat_sign.py:46-52, and docs/source/equilibrium_algorithms.rst:176-235.
