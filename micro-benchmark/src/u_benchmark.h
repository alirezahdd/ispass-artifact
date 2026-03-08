#ifndef U_BENCHMARK_H_
#define U_BENCHMARK_H_

#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <sched.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/uio.h>
#include <sys/syscall.h>

void fill_memory_with_prng(char *memory, size_t size, uint32_t seed);

void print_stats(uint64_t *buffer, int nr_pf, const char *region_start, size_t region_size);

static inline void enable_pf_recording() {
  int ret = syscall(551);
  if (ret) {
    printf("enable_pf_recording syscall failed with return code %d\n", ret);
  }
}

static inline void disable_pf_recording() {
  int ret = syscall(552);
  if (ret) {
    printf("disable_pf_recording syscall failed with return code %d\n", ret);
  }
}

static inline int get_pf_records(uint64_t *buffer, int size) {
  return syscall(553, buffer, size);
}

#endif  // U_BENCHMARK_H_
