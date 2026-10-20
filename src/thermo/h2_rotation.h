#pragma once

#include <configure.h>

#include <cmath>

namespace kintera {

constexpr double kNasa9Tref = 300.0;  // matches ThermoOptions default Tref
constexpr double kThetaRot = 87.55;   // K, H2 rotational temperature
constexpr int kJmax = 40;

// Scalar eval_h2cp (eval_uhs.cpp) for the UV solver: <m> and cv_rot/R
DISPATCH_MACRO inline void h2_rot(double T, int eq, double* m1, double* cv) {
  double z[2] = {}, s1[2] = {}, s2[2] = {};
  for (int J = 0; J <= kJmax; ++J) {
    int k = eq ? 0 : J % 2;  // normal: para (even J) and ortho apart
    double m = J * (J + 1.);
    double w =
        (2. * J + 1.) * (eq && J % 2 ? 3. : 1.) * exp(-kThetaRot * m / T);
    z[k] += w;
    s1[k] += w * m;
    s2[k] += w * m * m;
  }
  *m1 = *cv = 0.;
  for (int k = 0; k < 2 - eq; ++k) {
    double f = eq ? 1. : (k ? 0.75 : 0.25), a = s1[k] / z[k];
    *m1 += f * a;
    *cv += f * ((kThetaRot / T) * (kThetaRot / T) * (s2[k] / z[k] - a * a));
  }
}

// e/R - its value at kNasa9Tref, and d(e/R)/dT; conc is unused
DISPATCH_MACRO inline double h2_rot_e(double T, int eq) {
  double m, m0, cv;
  h2_rot(T, eq, &m, &cv);
  h2_rot(kNasa9Tref, eq, &m0, &cv);
  return 1.5 * (T - kNasa9Tref) + kThetaRot * (m - m0);
}
DISPATCH_MACRO inline double h2_rot_cv(double T, int eq) {
  double m, cv;
  h2_rot(T, eq, &m, &cv);
  return 1.5 + cv;
}
DISPATCH_MACRO inline double h2_rot_normal(double T, double) {
  return h2_rot_e(T, 0);
}
DISPATCH_MACRO inline double h2_rot_normal_ddT(double T, double) {
  return h2_rot_cv(T, 0);
}
DISPATCH_MACRO inline double h2_rot_equilibrium(double T, double) {
  return h2_rot_e(T, 1);
}
DISPATCH_MACRO inline double h2_rot_equilibrium_ddT(double T, double) {
  return h2_rot_cv(T, 1);
}

}  // namespace kintera
