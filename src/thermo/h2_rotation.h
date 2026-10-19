#pragma once

// C/C++
#include <cmath>

// base
#include <configure.h>

namespace kintera {

// Rigid-rotor H2 internal energy for the saturation adjustment, the same
// model as eval_h2cp (eval_uhs.cpp) used by VT->U and VU->T under use_h2_cp:
// theta_rot = 87.55 K, J = 0..40, referenced to T0 = 300 K,
//   e/R = 3/2 (T - T0) + theta (<m>(T) - <m>(T0)),  m = J(J+1),
//   de/dT / R = 3/2 + cv_rot/R.
// Registered as func2 extras (T, conc; conc is unused) so the CPU and CUDA
// solvers see the energy that VT->U puts in.
constexpr double kH2RotTref = 300.;

// <m> and cv_rot/R of one ensemble: parity 0 even J, 1 odd J, 2 all J with
// ortho weight 3 (equilibrium)
DISPATCH_MACRO
inline void h2_rot_reduce(double T, int parity, double* m1, double* cv_rot) {
  double const theta = 87.55;
  double z = 0., s1 = 0., s2 = 0.;
  for (int J = 0; J <= 40; ++J) {
    bool odd = J % 2 == 1;
    if ((parity == 0 && odd) || (parity == 1 && !odd)) continue;
    double m = J * (J + 1.);
    double w =
        (2. * J + 1.) * (parity == 2 && odd ? 3. : 1.) * exp(-theta * m / T);
    z += w;
    s1 += w * m;
    s2 += w * m * m;
  }
  *m1 = s1 / z;
  *cv_rot = (theta / T) * (theta / T) * (s2 / z - (*m1) * (*m1));
}

// normal: fixed 1:3 para:ortho, each internally equilibrated
DISPATCH_MACRO
inline void h2_rot_normal_moments(double T, double* m1, double* cv_rot) {
  double mp, cp, mo, co;
  h2_rot_reduce(T, 0, &mp, &cp);
  h2_rot_reduce(T, 1, &mo, &co);
  *m1 = 0.25 * mp + 0.75 * mo;
  *cv_rot = 0.25 * cp + 0.75 * co;
}

DISPATCH_MACRO
inline double h2_rot_normal(double T, double) {
  double m1, m1_0, cv;
  h2_rot_normal_moments(T, &m1, &cv);
  h2_rot_normal_moments(kH2RotTref, &m1_0, &cv);
  return 1.5 * (T - kH2RotTref) + 87.55 * (m1 - m1_0);
}

DISPATCH_MACRO
inline double h2_rot_normal_ddT(double T, double) {
  double m1, cv;
  h2_rot_normal_moments(T, &m1, &cv);
  return 1.5 + cv;
}

DISPATCH_MACRO
inline double h2_rot_equilibrium(double T, double) {
  double m1, m1_0, cv;
  h2_rot_reduce(T, 2, &m1, &cv);
  h2_rot_reduce(kH2RotTref, 2, &m1_0, &cv);
  return 1.5 * (T - kH2RotTref) + 87.55 * (m1 - m1_0);
}

DISPATCH_MACRO
inline double h2_rot_equilibrium_ddT(double T, double) {
  double m1, cv;
  h2_rot_reduce(T, 2, &m1, &cv);
  return 1.5 + cv;
}

}  // namespace kintera
