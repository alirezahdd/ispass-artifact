#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "u_benchmark.h"

void fill_memory_with_prng(char *memory, size_t size, uint32_t seed) {
  uint32_t prng = seed;
  uint32_t *mem32 = (uint32_t *)memory;
  size_t count32 = size / sizeof(uint32_t);
  for (size_t i = 0; i < count32; ++i) {
    prng = prng * 1664525u + 1013904223u;
    mem32[i] = prng;
  }

  size_t used = count32 * sizeof(uint32_t);
  size_t remaining = size - used;
  if (remaining) {
    uint8_t *tail = (uint8_t *)memory + used;
    for (size_t i = 0; i < remaining; ++i) {
      prng = prng * 1664525u + 1013904223u;
      tail[i] = (uint8_t)prng;
    }
  }
}

void print_stats(uint64_t *buffer, int nr_pf, const char *region_start, size_t region_size) {
  uintptr_t region_begin = (uintptr_t)region_start;
  uintptr_t region_end = region_begin + region_size;

  for (int i = 0; i < nr_pf; i++) {
    int j = i * 12;
    uint64_t ip = buffer[j + 1];
    uint64_t addr = buffer[j + 2];

    if ((uintptr_t)addr < region_begin || (uintptr_t)addr >= region_end) {
      continue;
    }

    char pf_type = buffer[j] & 1;
    int nr_readahead = (int)((buffer[j] >> 1) & 0xF);
    char valid_flag = (char)((buffer[j] >> 5) & 0x1);
    char retry_flag = (char)((buffer[j] >> 6) & 0x1);
    char swapcache_flag = (char)((buffer[j] >> 7) & 0x1);
    char swapdev_flag = (char)((buffer[j] >> 8) & 0x1);
    char ra_cluster_flag = (char)((buffer[j] >> 9) & 0x1);
    char ra_vma_flag = (char)((buffer[j] >> 10) & 0x1);
    int ra_sleep_count = (int)((buffer[j] >> 11) & 0x0F);
    char direct_reclaim_flag = (char)((buffer[j] >> 15) & 0x1);
    int reclaim_count = (int)((buffer[j] >> 16) & 0xFF);
    int timer_duration = (int)(buffer[j] >> 32);

    uint64_t ts[9];
    for (int k = 0; k < 9; k++) {
      ts[k] = buffer[j + 3 + k];
    }

    printf("%d 0x%lx 0x%lx %s %d %d %d %d %d %d %d %d %d %d %d ",
           i, ip, addr,
           (pf_type == 0) ? "minor" : "major",
           nr_readahead,
           valid_flag,
           retry_flag,
           swapcache_flag,
           swapdev_flag,
           ra_cluster_flag,
           ra_vma_flag,
           ra_sleep_count,
           direct_reclaim_flag,
           reclaim_count,
           timer_duration);
    printf("%lu %lu %lu %lu %lu %lu %lu %lu %lu\n",
           ts[0], ts[1], ts[2], ts[3], ts[4], ts[5], ts[6], ts[7], ts[8]);
  }
}
