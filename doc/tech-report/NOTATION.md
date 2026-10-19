# Notation for the kintera Technical Report

One symbol, one meaning, across all chapters. A symbol used only within one scheme is defined at its first use there.
Where a published source uses a different letter, the chapter translates to this table; the "source letter" column
records the common translations.

Units are SI and every dimensional symbol carries them in its row; a dimensionless symbol is marked [-] and a count is
marked "count", and an empty unit cell means that no unit or shape is specified here. Each row states whether its
quantity is molar or specific (per kilogram).

The tables below start empty except for symbols that every atmospheric thermodynamics text writes the same way. The
editor adds a row when a chapter first needs a symbol; a chapter never adds a row itself. A row's "code"
column gives the name kintera uses at the pin of `code_pin.yml`, and is left empty until a chapter has checked it there.

## 1. Coordinates and grids

| symbol | meaning | code | source letter |
|---|---|---|---|

## 2. State, thermodynamics and species

| symbol | meaning | code | source letter |
|---|---|---|---|
| $p$ | pressure [Pa] | | |
| $T$ | temperature [K] | | |
| $\mathcal R$ | universal gas constant [J mol$^{-1}$ K$^{-1}$]; a molar quantity | | |
| $c_n$ | molar concentration of species $n$ per unit volume of the whole mixture [mol m$^{-3}$]; gases $n < N_{\mathrm g}$ first, then condensates | `conc` | |
| $N_{\mathrm g}$ | number of gas species [count] | `vapor_ids().size()` | |
| $x_n$ | mole fraction of species $n$ among all species, gas and condensed [-]; molar | `xfrac` | |
| $x_{\mathrm g}$ | sum of the gas mole fractions [-]; molar | | |
| $y_n$ | mass fraction of species $n$ [-]; specific | `yfrac` | |
| $\rho$ | total density of the mixture [kg m$^{-3}$] | `rho` | |
| $\rho_n$ | partial density of species $n$, mass per unit volume of the mixture [kg m$^{-3}$] | `ivol` | |
| $z_n$ | compressibility factor of gas $n$ [-] | `czh` | $Z$ |
| $U$ | internal energy per unit volume of the mixture [J m$^{-3}$] | `intEng` | |
| $H$ | enthalpy per unit volume of the mixture [J m$^{-3}$] | | |
| $C_V$ | heat capacity at constant volume per unit volume [J m$^{-3}$ K$^{-1}$] | | |
| $C_p$ | heat capacity at constant pressure per unit volume [J m$^{-3}$ K$^{-1}$] | | |

## 2a. Species thermodynamics, phase change and reactions

| symbol | meaning | code |
|---|---|---|
| $c_{v,n}$ | molar heat capacity at constant volume of species $n$ [J mol$^{-1}$ K$^{-1}$] | `eval_cv_R` |
| $u_n$ | molar internal energy of species $n$ [J mol$^{-1}$] | `eval_intEng_R` |
| $h_n$ | molar enthalpy of species $n$ [J mol$^{-1}$] | `eval_enthalpy_R` |
| $s_n$ | molar entropy of species $n$ [J mol$^{-1}$ K$^{-1}$] | `eval_entropy_R` |
| $c^{\star}_n$ | constant heat-capacity coefficient of species $n$, $c_{v,n}/\mathcal R$ without extra terms [-] | `cref_R` (YAML `cv_R`) |
| $u^{\star}_n$ | internal energy of species $n$ at $T_\star$, divided by $\mathcal R$ [K] | `uref_R` (YAML `u0_R`) |
| $s^{\star}_n$ | entropy of gas $n$ at $T_\star$ and $p_\star$, divided by $\mathcal R$ [-] | `sref_R` (YAML `s0_R`) |
| $K_r$ | saturation constant of condensation reaction $r$: the product over the gases of the reaction of their partial pressures on the saturation curve, each raised to $-\nu_{nr}$ (positive for a gas consumed, negative for a gas produced) [Pa$^{m}$, $m = -\sum_{n<N_{\mathrm g}} \nu_{nr}$] | `eval_logsvp` (its logarithm; the solvers' `logsvp` also holds the pressure or $\mathcal R T$ term) |
| $L_r$ | latent heat of reaction $r$ at constant volume, internal energy released per unit extent [J mol$^{-1}$] | |
| $\mathrm{RH}_r$ | relative humidity of reaction $r$, the gas partial-pressure product of $K_r$ at the actual partial pressures, over $K_r$ [-] | `relative_humidity` |
| $\nu_{nr}$ | stoichiometric coefficient of species $n$ in reaction $r$, negative for a reactant, positive for a product [-] | `stoich` |
| $\xi_r$ | extent of reaction $r$: a change $\xi_r$ changes the amount of each species $n$ by $\nu_{nr}\,\xi_r$; in the units of those amounts, mole fraction [-] or concentration [mol m$^{-3}$] | `rhs` in the saturation solvers, after the least-squares solve |
| $\Delta_r$ | saturation deficit of reaction $r$, $\ln K_r(T) + \sum_{n<N_{\mathrm g}} \nu_{nr} \ln p_n$, positive when subsaturated [-] | `logsvp - log_frac_sum` |
| $\mathcal N_n$ | amount of species $n$ in a cell [mol]; molar | `moles` |
| $a_n$ | activity of species $n$ in its phase: its mole fraction within the phase, times $p/p^\circ$ for a gas [-] | |
| $p^\circ$ | standard pressure of the equilibrium constants [Pa] | `standard_pressure` (YAML `standard-pressure`) |
| $g^\circ_n$ | molar Gibbs energy of species $n$ at $T$ and the standard pressure [J mol$^{-1}$]; molar | `nasa9_gibbs_rt` (as $g^\circ_n/\mathcal R T$) |
| $K^\circ_r$ | standard equilibrium constant of reaction $r$, $\exp(-\sum_n \nu_{nr} g^\circ_n/\mathcal R T)$ [-] | `log_k` (its logarithm) |

## 3. Fluxes and transport

| symbol | meaning | code |
|---|---|---|

## 4. Operators and averages

| symbol | meaning |
|---|---|

## 5. Gravity and potential energy

| symbol | meaning | code |
|---|---|---|

## 6. Reference states

| symbol | meaning | code |
|---|---|---|
| $T_\star$ | thermodynamic reference temperature [K] | `Tref` |
| $p_\star$ | thermodynamic reference pressure [Pa] | `Pref` |

## 7. Time integration and the implicit solver

| symbol | meaning | code |
|---|---|---|
| $\mathsf I$ | the identity matrix, sized by context | |

## 8. Diffusion

| symbol | meaning |
|---|---|

## 8a. Radiation and photochemistry

| symbol | meaning | code |
|---|---|---|
| $\sigma_{\mathrm{SB}}$ | Stefan-Boltzmann constant [W m$^{-2}$ K$^{-4}$] | |

## 9. Diagnostics and errors

| symbol | meaning |
|---|---|

## 10. Reserved letters (do not reuse)

None yet. When two chapters need the same letter for different things, the editor rules which keeps it, lists the
letter here with its one meaning, and gives the other meaning a new symbol in its section's table.

- $O(\cdot)$, italic capital O, is always the Landau order symbol.
