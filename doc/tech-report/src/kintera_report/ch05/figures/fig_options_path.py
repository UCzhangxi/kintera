"""From a YAML input to the buffers of EquilibriumTP (@sec-ch05-options), as read from
src/equilibrium/equilibrium_options.cpp and src/equilibrium/equilibrium.cpp at
kintera@0d9f67f97d841147e23283d2dcdab302238d2c45. No data file."""
from kintera_report.ch04.flow import flow


def make_fig():
    return flow(["phases:\nspecies by phase", "species:\ncompositions", "reactions:\ntype equilibrium",
                 "validate", "EquilibriumTP:\nstoich, phase_ids"],
                notes=[(0, "one ideal-gas\nphase"), (2, "each balanced\nin every element"),
                       (3, "≤ 64 components"), (4, "reactions\nindependent")],
                height=1.9)
