"""Working-set iteration of `leastsq_kkt_feasible_origin` (@sec-ch04-active-set), as read from
src/math/leastsq_kkt.h at kintera@0d9f67f97d841147e23283d2dcdab302238d2c45. No data file."""
from kintera_report.ch04.flow import flow


def make_fig():
    return flow(["working set\nas equalities", "solve the\nKKT system", "drop: negative\nmultiplier",
                 "add: most\nviolated row", "stop"],
                notes=[(1, "direct, then\nregularised"), (3, "independent\nto sqrt(eps)"), (4, "codes\n0, 1, 2, 3")],
                height=1.9, loop_back=(3, 1, "repeat"))
