#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include "profiling_utils.h"
#include "u_benchmark.h"

#define MB (1024ULL * 1024)
#define SIZE (4 * MB)
#define PAGE_SIZE 4096
#define NUM_PAGES (SIZE / PAGE_SIZE)
#define STRIDE 8
#define PF_RECORD_BATCH 100

int main(int argc, char *argv[]) {
  if (argc < 2) {
    fprintf(stderr, "Usage: %s <output_file>\n", argv[0]);
    return 1;
  }

  initialize_perf_measurements();
  char *memory = (char *)malloc(SIZE);
  if (!memory) {
    fprintf(stderr, "Memory allocation failed\n");
    return 1;
  }

  fill_memory_with_prng(memory, SIZE, 123456789u);

  long long sum = 0;

  printf("Allocated 4MB, accessing sequentially with page (4KB) stride...\n");

  volatile char dummy;
  int total_iterations = 0;

  long long user_cycles, kernel_cycles, user_instructions, kernel_instructions, major_faults, minor_faults;
  struct timespec start_ts, end_ts;

  FILE *output_file = fopen(argv[1], "a");
  if (!output_file) {
    fprintf(stderr, "Failed to open output file\n");
    free(memory);
    return 1;
  }

  uint64_t *buffer = (uint64_t *)malloc(PF_RECORD_BATCH * 12 * sizeof(uint64_t));
  if (!buffer) {
    fprintf(stderr, "PF record buffer allocation failed\n");
    fclose(output_file);
    free(memory);
    return 1;
  }
  enable_pf_recording();

  for (uint64_t i = 0; i < SIZE; i += STRIDE * PAGE_SIZE) {
    volatile char *address = &memory[i];

    start_counters(&perf_ctrs);
    clock_gettime(CLOCK_MONOTONIC, &start_ts);
    dummy = *address;
    clock_gettime(CLOCK_MONOTONIC, &end_ts);
    stop_counters(&perf_ctrs, &user_cycles, &kernel_cycles, &user_instructions,
                  &kernel_instructions, &major_faults, &minor_faults);

    if ((major_faults > 0 || minor_faults > 0)) {
      long long access_time_ns = (end_ts.tv_sec - start_ts.tv_sec) * 1000000000LL + (end_ts.tv_nsec - start_ts.tv_nsec);
      double access_time_us = access_time_ns / 1000.0;
      fprintf(output_file, "Iteration #%d (page %lu): access_time=%.3f us, user_cycles=%lld, kernel_cycles=%lld, user_instructions=%lld, kernel_instructions=%lld, major_faults=%lld, minor_faults=%lld\n",
              total_iterations, i / PAGE_SIZE, access_time_us, user_cycles, kernel_cycles, user_instructions, kernel_instructions, major_faults, minor_faults);
      fflush(output_file);
    }
  
    sum += dummy;
    total_iterations++;

    if ((i >> 12) % 80 == 0) {
      int nr_pf = get_pf_records(buffer, PF_RECORD_BATCH);
      print_stats(buffer, nr_pf, memory, SIZE);
    }
  }

  int nr_pf = get_pf_records(buffer, PF_RECORD_BATCH);
  print_stats(buffer, nr_pf, memory, SIZE);

  disable_pf_recording();
  
  fclose(output_file);
  free(buffer);
  free(memory);

  printf("Sequential access complete\nSum: %lld\nTotal iterations: %d\n", 
         sum, total_iterations);
  return 0;
}
