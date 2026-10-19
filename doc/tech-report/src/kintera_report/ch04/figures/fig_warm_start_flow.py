"""What a warm start passes to the saturation solvers (@sec-ch04-warm-start-failures), as read from
src/thermo/thermo_x.cpp, thermo_y.cpp, equilibrate_tp.h and equilibrate_uv.h at
kintera@0d9f67f97d841147e23283d2dcdab302238d2c45. No data file."""
from kintera_report.ch04.flow import flow


def make_fig():
    return flow(["warm_start\n=True", "stored order\nand count", "solver re-tests\nall reactions",
                 "result and\ndiagnostic", "failure count\n(ThermoY)"],
                notes=[(0, "same shape\nand device"), (1, "count is\nnever read"), (2, "order sets\nvisit order"),
                       (3, "n, -100, -1,\n-(100 s + n)")],
                height=1.9)
