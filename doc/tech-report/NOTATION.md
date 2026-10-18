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

## 2a. Species thermodynamics, phase change and reactions

| symbol | meaning | code |
|---|---|---|

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
