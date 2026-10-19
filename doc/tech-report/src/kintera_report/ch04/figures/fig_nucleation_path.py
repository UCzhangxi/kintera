"""From a YAML reaction entry to a saturation constant (@sec-ch04-nucleation), as read from
src/thermo/nucleation.cpp at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45. No data file."""
from kintera_report.ch04.flow import flow


def make_fig():
    return flow(["YAML\nreaction entry", "type:\nnucleation?", "formula", "$\\ln K_j(T)$", "conditions of\nboth solvers"],
                notes=[(1, "other types\nskipped"), (2, "ideal, antoine\nor named fit"), (3, "minT, maxT\nunused")],
                height=1.9)
