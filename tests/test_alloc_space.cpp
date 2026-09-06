// external
#include <gtest/gtest.h>

// C/C++
#include <cstddef>
#include <cstdint>
#include <cstdio>

// kintera
#include <kintera/utils/alloc.h>

using namespace kintera;

namespace {

// Each walk repeats the alloc_from sequence of the function it is named after,
// so the bytes it consumes are what the matching *_space budget must cover.
template <typename T>
void walk_ludcmp(char*& work, int n) {
  alloc_from<T>(work, n);  // vv
}

template <typename T>
void walk_leastsq_kkt(char*& work, int n2, int n3) {
  int size = n2 + n3;
  alloc_from<T>(work, size * size);  // aug
  alloc_from<T>(work, n2 * n2);      // ata
  alloc_from<T>(work, n2);           // atb
  alloc_from<T>(work, size);         // rhs
  alloc_from<T>(work, n3);           // eval
  alloc_from<int>(work, n3);         // ct_indx
  alloc_from<int>(work, size);       // lu_indx
  alloc_from<int>(work, size);       // skip_row
  walk_ludcmp<T>(work, size);        // n2 + nactive <= size
}

template <typename T>
void walk_equilibrate_tp(char*& work, int nspecies, int nreaction) {
  alloc_from<T>(work, nreaction);              // logsvp
  alloc_from<T>(work, nreaction * nspecies);   // weight
  alloc_from<T>(work, nreaction);              // rhs
  alloc_from<T>(work, nspecies * nreaction);   // stoich_active
  alloc_from<T>(work, nreaction);              // stoich_sum
  alloc_from<T>(work, nspecies);               // xfrac0
  alloc_from<T>(work, nreaction * nreaction);  // gain_cpy
  walk_leastsq_kkt<T>(work, nreaction, nspecies);
}

template <typename T>
void walk_equilibrate_uv(char*& work, int nspecies, int nreaction) {
  alloc_from<T>(work, nspecies);               // intEng
  alloc_from<T>(work, nspecies);               // intEng_ddT
  alloc_from<T>(work, nreaction);              // logsvp
  alloc_from<T>(work, nreaction);              // logsvp_ddT
  alloc_from<T>(work, nreaction * nspecies);   // weight
  alloc_from<T>(work, nreaction);              // rhs
  alloc_from<T>(work, nspecies * nreaction);   // stoich_active
  alloc_from<T>(work, nspecies);               // conc0
  alloc_from<T>(work, nreaction * nreaction);  // gain_cpy
  walk_leastsq_kkt<T>(work, nreaction, nspecies);
}

alignas(64) char buffer[1 << 16];

// consumed <= advertised, and advertised is a multiple of alignof(T) so that
// the per-thread stride smem + tid * mem_size (loops.cuh) stays aligned.
template <typename T, typename Walk>
void check_budget(const char* name, size_t advertised, Walk walk) {
  char* work = buffer;
  walk(work);
  size_t consumed = static_cast<size_t>(work - buffer);
  EXPECT_LE(consumed, advertised) << name;
  EXPECT_EQ(advertised % alignof(T), 0u) << name;
}

template <typename T>
class AllocSpaceTest : public ::testing::Test {};

using ScalarTypes = ::testing::Types<float, double>;
TYPED_TEST_SUITE(AllocSpaceTest, ScalarTypes);

TYPED_TEST(AllocSpaceTest, budget_covers_walk) {
  using T = TypeParam;
  char name[64];
  for (int nspecies = 2; nspecies <= 11; ++nspecies) {
    for (int nreaction = 1; nreaction <= 5; ++nreaction) {
      snprintf(name, sizeof(name), "nspecies=%d nreaction=%d", nspecies,
               nreaction);
      check_budget<T>(
          name, leastsq_kkt_space<T>(nreaction, nspecies),
          [&](char*& w) { walk_leastsq_kkt<T>(w, nreaction, nspecies); });
      check_budget<T>(
          name, equilibrate_tp_space<T>(nspecies, nreaction),
          [&](char*& w) { walk_equilibrate_tp<T>(w, nspecies, nreaction); });
      check_budget<T>(
          name, equilibrate_uv_space<T>(nspecies, nreaction),
          [&](char*& w) { walk_equilibrate_uv<T>(w, nspecies, nreaction); });
    }
  }
}

}  // namespace
