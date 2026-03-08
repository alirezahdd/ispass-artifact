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

  printf("Allocated 4MB, accessing randomly with page (4KB) granularity...\n");

  uint64_t *page_sequence = (uint64_t *)malloc(NUM_PAGES * sizeof(uint64_t));
  if (!page_sequence) {
    fprintf(stderr, "Page sequence allocation failed\n");
    free(memory);
    return 1;
  }
  
  unsigned int prng_state = 123456789u;
  for (uint64_t i = 0; i < NUM_PAGES; i++) {
    prng_state = prng_state * 1664525u + 1013904223u;
    page_sequence[i] = (prng_state % NUM_PAGES) * PAGE_SIZE;
  }

  volatile char dummy;
  int total_iterations = 0;

  long long user_cycles, kernel_cycles, user_instructions, kernel_instructions, major_faults, minor_faults;
  struct timespec start_ts, end_ts;

  FILE *output_file = fopen(argv[1], "a");
  if (!output_file) {
    fprintf(stderr, "Failed to open output file\n");
    free(page_sequence);
    free(memory);
    return 1;
  }
  
  uint64_t *buffer = (uint64_t *)malloc(PF_RECORD_BATCH * 12 * sizeof(uint64_t));
  if (!buffer) {
    fprintf(stderr, "PF record buffer allocation failed\n");
    fclose(output_file);
    free(page_sequence);
    free(memory);
    return 1;
  }
  enable_pf_recording();

  for (uint64_t i = 0; i < NUM_PAGES; i++) {
    uint64_t offset = page_sequence[i];
    volatile char *address = &memory[offset];

    start_counters(&perf_ctrs);
    clock_gettime(CLOCK_MONOTONIC, &start_ts);
    dummy = *address;
    (void)dummy;
    clock_gettime(CLOCK_MONOTONIC, &end_ts);
    stop_counters(&perf_ctrs, &user_cycles, &kernel_cycles, &user_instructions,
                  &kernel_instructions, &major_faults, &minor_faults);

    if ((major_faults > 0 || minor_faults > 0)) {
      long long access_time_ns = (end_ts.tv_sec - start_ts.tv_sec) * 1000000000LL + (end_ts.tv_nsec - start_ts.tv_nsec);
      double access_time_us = access_time_ns / 1000.0;
      fprintf(output_file, "Iteration #%d (page %lu): access_time=%.3f us, user_cycles=%lld, kernel_cycles=%lld, user_instructions=%lld, kernel_instructions=%lld, major_faults=%lld, minor_faults=%lld\n",
              total_iterations, offset / PAGE_SIZE, access_time_us, user_cycles, kernel_cycles, user_instructions, kernel_instructions, major_faults, minor_faults);
      fflush(output_file);
    }
    if (i % 80 == 0) {
      int nr_pf = get_pf_records(buffer, PF_RECORD_BATCH);
      print_stats(buffer, nr_pf, memory, SIZE);
    }

    total_iterations++;
  }

  int nr_pf = get_pf_records(buffer, PF_RECORD_BATCH);
  print_stats(buffer, nr_pf, memory, SIZE);

  disable_pf_recording();
  
  fclose(output_file);
  free(buffer);
  free(page_sequence);
  free(memory);

  printf("Random access complete\n");
  return 0;
}
