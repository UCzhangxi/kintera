# Reader tasks (N2)

Sources are the original IDs in `reader-navigation-inventory.json`. Q01 maps to Q-001, and so on.
The four paired exclusions remain excluded in that inventory even when this expanded book offers a route.
The 21 follow-up rows map to their original question rows, plus A04; overlapping tasks are not duplicated.
A section route is not a new FULL grade. Partly documented rows retain unresolved or unverified scope.

| id | task | source(s) | answered at (anchor) or not provided (reason) | note |
|---|---|---|---|---|
| Q-001 | How are gases and condensates ordered in species data? | Q01 | sec-ch02-species-registry | 2.1; Frozen PARTIAL; partly documented; paired eligible; no new grade. |
| Q-002 | What does reference-pressure mean and what units does it use? | Q02 | sec-ch03-reference-state | 3.3; Frozen FULL; paired eligible; no new grade. |
| Q-003 | How do I add a species with thermodynamic data? | Q03 | sec-ch02-species-registry | 2.1; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-004 | How are mass and mole fractions converted and what happens to the implicit dry species? | Q04 | sec-ch03-thermo-y | 3.4; Frozen FULL; paired eligible; no new grade. |
| Q-005 | How are mixture heat capacities computed and in what units? | Q05 | sec-ch03-thermo-y | 3.4; Frozen PARTIAL; partly documented; paired eligible; no new grade. |
| Q-006 | What is the Shomate representation and its temperature convention? | Q06 | not provided: outside scope: Shomate is outside the frozen scope; NASA-9 is described in sec-ch02-nasa9 | 3. Frozen NO-ENTRY; excluded from paired denominator. |
| Q-007 | How is condensate entropy derived from saturation equilibrium? | Q07 | sec-ch03-species-functions | 3.2; Frozen FULL; paired eligible; no new grade. |
| Q-008 | How do I add a new saturation vapor pressure law? | Q08 | sec-ch02-svp | 2.4; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-009 | How does the implicit kinetics update work and what are its limitations? | Q09 | sec-ch06-implicit | 6.9; Frozen FULL; paired eligible; no new grade. |
| Q-010 | What is a third-body reaction and how is effective concentration defined? | Q10 | sec-ch06-falloff | 6.4; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-011 | What are the Arrhenius rate parameters and their units? | Q11 | sec-ch06-arrhenius | 6.2; Frozen FULL; paired eligible; no new grade. |
| Q-012 | How do I add a reaction rate law? | Q12 | sec-ch06-arrhenius | 6.2; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-013 | What diffusion flux is solved and what are its boundary assumptions? | Q13 | sec-ch08-tendency | 8.2; Frozen FULL; paired eligible; no new grade. |
| Q-014 | What is binary diffusion and what units does its coefficient have? | Q14 | sec-ch09-molecular | 9.3; Frozen NO-ENTRY; partly documented; excluded from paired denominator. |
| Q-015 | How is the diffusion discretization derived? | Q15 | sec-ch08-operator | 8.1; Frozen FULL; paired eligible; no new grade. |
| Q-016 | How do I configure molecular diffusion coefficients? | Q16 | sec-ch09-molecular | 9.3; Frozen NO-ENTRY; partly documented; excluded from paired denominator. |
| Q-017 | How do I load a YAML mechanism and construct Python modules? | Q17 | sec-ch11-yaml-input | 11.1; Frozen FULL; paired eligible; no new grade. |
| Q-018 | What does ADD_ARG mean for an option? | Q18 | sec-ch11-options | 11.3; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-019 | How are resource files located? | Q19 | sec-ch11-resources | 11.5; Frozen FULL; paired eligible; no new grade. |
| Q-020 | How do I add a YAML configuration option? | Q20 | sec-ch11-options | 11.3; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-021 | How do I move a module to GPU and what tensors must share its device? | Q21 | sec-ch12-dispatch | 12.2; Frozen PARTIAL; partly documented; paired eligible; no new grade. |
| Q-022 | What is a batch dimension in this API? | Q22 | sec-ch12-dispatch | 12.2; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-023 | What dtype and device limitations apply to execution? | Q23 | sec-ch12-dispatch | 12.2; Frozen PARTIAL; partly documented; paired eligible; no new grade. |
| Q-024 | How do I benchmark GPU speedup reliably? | Q24 | sec-ch12-dispatch | 12.2; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-025 | Which tests verify equilibrium conservation and what do they establish? | Q25 | sec-ch13-suite | 13.1; Frozen PARTIAL; partly documented; paired eligible; no new grade. |
| Q-026 | What is a validation tolerance and how is it chosen? | Q26 | sec-ch13-suite | 13.1; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-027 | Where can I find test coverage and its limits? | Q27 | sec-ch13-device-coverage | 13.3; Frozen FULL; paired eligible; no new grade. |
| Q-028 | How do I run verification tests? | Q28 | sec-ch13-suite | 13.1; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-029 | How do I couple chemistry to a hydrodynamics step and who owns the timestep? | Q29 | sec-ch14-kinetics | 14.3; Frozen FULL; paired eligible; no new grade. |
| Q-030 | What is operator splitting and what accuracy is promised? | Q30 | sec-ch14-kinetics | 14.3; Frozen NO-ENTRY; partly documented; paired eligible; no new grade. |
| Q-031 | What units and state conversions are needed at the host interface? | Q31 | sec-ch14-kinetics | 14.3; Frozen FULL; paired eligible; no new grade. |
| Q-032 | How do I couple radiation to photochemistry? | Q32 | sec-ch09-sources | 9.4; Frozen NO-ENTRY; partly documented; excluded from paired denominator. |
| A04 | Can the shared notation index define the diffusion face spacing and units? | A04 | sec-ch08-operator | 8.1; partly documented: local spacing definition available; shared notation group remains incomplete. |
