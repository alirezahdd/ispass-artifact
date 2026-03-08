#ifndef KERNEL_UTILS_H_
#define KERNEL_UTILS_H_

#include <stdint.h>
#include <unistd.h>
#include <sched.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/uio.h>
#include <sys/syscall.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint64_t u64;

inline void enable_pf_recording(){
  int ret = syscall(551);
  if(ret){
    printf("enable_pf_recording syscall failed with return code %d\n", ret);
  }
}

inline void disable_pf_recording(){
  int ret = syscall(552);
  if(ret){
    printf("disable_pf_recording syscall failed with return code %d\n", ret);
  }
}

inline int get_pf_records(uint64_t* buffer, int size){
  int ret = syscall(553, buffer, size);
  return ret;
}

inline void print_stats(uint64_t* buffer, int nr_pf) {
  // Placeholder for actual stats printing logic
  for (int i = 0; i < nr_pf; i++) {
    int j = i * 12; // each record has 12 uint64_t entries
    uint64_t ip = buffer[j+1];
    uint64_t addr = buffer[j+2];
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
      ts[0], ts[1], ts[2], ts[3], ts[4],
      ts[5], ts[6], ts[7], ts[8]);
  }
}

#define NR_HIST_BINS 4
#define NR_HIST_BIN_EDGES (NR_HIST_BINS-1)

struct fault_histogram {
  u64 count[NR_HIST_BINS];
  u64 min[NR_HIST_BINS];
  u64 max[NR_HIST_BINS];
  u64 sum[NR_HIST_BINS];
  u64 bin_edges[NR_HIST_BIN_EDGES];
};

struct fault_histograms{
  bool recording;
  u64 prev_exit_timestamp;
  struct fault_histogram total_lh;
  struct fault_histogram entry_to_ra_lh;
  struct fault_histogram readahead_lh;
  struct fault_histogram readahead_nrh;
  struct fault_histogram readahead_pp_lh;
  struct fault_histogram reclaim_lh;
  struct fault_histogram reclaim_nrh;
  struct fault_histogram ra_to_sleep_lh;
  struct fault_histogram sleep_lh;
  struct fault_histogram nvme_ssd_lh;
  struct fault_histogram wakeup_to_return_lh;
  struct fault_histogram pf_to_pf_h;
  struct fault_histogram pg_allocation_lh;
  struct fault_histogram swap_cache_lookup_lh;
  struct fault_histogram pg_allocation_sleep_lh;
  struct fault_histogram bio_submission_lh;
};


inline void enable_fault_hist_recording(){
  int ret = syscall(554);
  if(ret){
    printf("enable_fault_hist_recording syscall failed with return code %d\n", ret);
  }
}

inline void disable_fault_hist_recording(){
  int ret = syscall(555);
  if(ret){
    printf("disable_fault_hist_recording syscall failed with return code %d\n", ret);
  }
}

inline int get_fault_histograms(struct fault_histograms* buffer, int size, int hist_type){
  int ret = syscall(556, buffer, size, hist_type);
  return ret;
}

inline void print_fault_histogram(const char* name, struct fault_histogram* hist){
  printf("%s:\n", name);
  printf("  bin_edges: ");
  for(int i = 0; i < NR_HIST_BINS - 1; i++){
    printf("%lu ", hist->bin_edges[i]);
  }
  printf("\n");
  
  for(int i = 0; i < NR_HIST_BINS; i++){
    printf("  bin_%d: count=%lu min=%lu max=%lu sum=%lu\n", 
           i, hist->count[i], hist->min[i], hist->max[i], hist->sum[i]);
  }
}

inline void print_fault_histograms(struct fault_histograms* hists){
  printf("=== Fault Histograms ===\n");
  printf("recording: %s\n\n", hists->recording ? "true" : "false");
  
  print_fault_histogram("total_lh", &hists->total_lh);
  printf("\n");
  print_fault_histogram("entry_to_ra_lh", &hists->entry_to_ra_lh);
  printf("\n");
  print_fault_histogram("readahead_lh", &hists->readahead_lh);
  printf("\n");
  print_fault_histogram("readahead_nrh", &hists->readahead_nrh);
  printf("\n");
  print_fault_histogram("readahead_pp_lh", &hists->readahead_pp_lh);
  printf("\n");
  print_fault_histogram("reclaim_lh", &hists->reclaim_lh);
  printf("\n");
  print_fault_histogram("reclaim_nrh", &hists->reclaim_nrh);
  printf("\n");
  print_fault_histogram("ra_to_sleep_lh", &hists->ra_to_sleep_lh);
  printf("\n");
  print_fault_histogram("sleep_lh", &hists->sleep_lh);
  printf("\n");
  print_fault_histogram("nvme_ssd_lh", &hists->nvme_ssd_lh);
  printf("\n");
  print_fault_histogram("wakeup_to_return_lh", &hists->wakeup_to_return_lh);
  printf("\n");
  print_fault_histogram("pf_to_pf_h", &hists->pf_to_pf_h);
  printf("\n");
  print_fault_histogram("pg_allocation_lh", &hists->pg_allocation_lh);
  printf("\n");
  print_fault_histogram("swap_cache_lookup_lh", &hists->swap_cache_lookup_lh);
  printf("\n");
  print_fault_histogram("pg_allocation_sleep_lh", &hists->pg_allocation_sleep_lh);
  printf("\n");
  print_fault_histogram("bio_submission_lh", &hists->bio_submission_lh);
  printf("\n");
}

#ifndef NUM_CORES
#define NUM_CORES 16
#endif

fault_histograms* buffer[NUM_CORES];
fault_histograms* buffer_min[NUM_CORES];
fault_histograms* buffer_rec[NUM_CORES];

inline void init_fault_histogram_buffers(){
  for(int i = 0; i < NUM_CORES; i++){
    buffer[i] = (fault_histograms*)malloc(sizeof(fault_histograms));
    buffer_min[i] = (fault_histograms*)malloc(sizeof(fault_histograms));
    buffer_rec[i] = (fault_histograms*)malloc(sizeof(fault_histograms));
  }
}

inline void merge_single_histogram(struct fault_histogram* dest, struct fault_histogram* src){
  // Merge bin_edges (take from first non-zero source, or keep dest)
  for(int i = 0; i < NR_HIST_BIN_EDGES; i++){
    if(dest->bin_edges[i] == 0 && src->bin_edges[i] != 0){
      dest->bin_edges[i] = src->bin_edges[i];
    }
  }
  
  // Merge each bin
  for(int i = 0; i < NR_HIST_BINS; i++){
    dest->count[i] += src->count[i];
    dest->sum[i] += src->sum[i];
    
    // Update min (only if src has data)
    if(src->count[i] > 0){
      if(dest->min[i] == 0 || src->min[i] < dest->min[i]){
        dest->min[i] = src->min[i];
      }
    }
    
    // Update max
    if(src->max[i] > dest->max[i]){
      dest->max[i] = src->max[i];
    }
  }
}

inline void merge_fault_histograms(struct fault_histograms* result, struct fault_histograms* result_min, struct fault_histograms* result_rec){
  // Initialize result to zeros
  memset(result, 0, sizeof(struct fault_histograms));
  memset(result_min, 0, sizeof(struct fault_histograms));
  memset(result_rec, 0, sizeof(struct fault_histograms));

  // Merge all histograms from all cores
  for(int core = 0; core < NUM_CORES; core++){
    if(buffer[core] == NULL) continue;
    
    struct fault_histograms* src = buffer[core];
    
    // Set recording flag if any core was recording
    if(src->recording){
      result->recording = true;
    }
    
    // Keep the latest exit timestamp
    if(src->prev_exit_timestamp > result->prev_exit_timestamp){
      result->prev_exit_timestamp = src->prev_exit_timestamp;
    }
    
    // Merge each histogram type
    merge_single_histogram(&result->total_lh, &src->total_lh);
    merge_single_histogram(&result->entry_to_ra_lh, &src->entry_to_ra_lh);
    merge_single_histogram(&result->readahead_lh, &src->readahead_lh);
    merge_single_histogram(&result->readahead_nrh, &src->readahead_nrh);
    merge_single_histogram(&result->readahead_pp_lh, &src->readahead_pp_lh);
    merge_single_histogram(&result->reclaim_lh, &src->reclaim_lh);
    merge_single_histogram(&result->reclaim_nrh, &src->reclaim_nrh);
    merge_single_histogram(&result->ra_to_sleep_lh, &src->ra_to_sleep_lh);
    merge_single_histogram(&result->sleep_lh, &src->sleep_lh);
    merge_single_histogram(&result->nvme_ssd_lh, &src->nvme_ssd_lh);
    merge_single_histogram(&result->wakeup_to_return_lh, &src->wakeup_to_return_lh);
    merge_single_histogram(&result->pf_to_pf_h, &src->pf_to_pf_h);
    merge_single_histogram(&result->pg_allocation_lh, &src->pg_allocation_lh);
    merge_single_histogram(&result->swap_cache_lookup_lh, &src->swap_cache_lookup_lh);
    merge_single_histogram(&result->pg_allocation_sleep_lh, &src->pg_allocation_sleep_lh);
    merge_single_histogram(&result->bio_submission_lh, &src->bio_submission_lh);
  }

  // Merge all histograms from all cores
  for(int core = 0; core < NUM_CORES; core++){
    if(buffer_min[core] == NULL) continue;
    
    struct fault_histograms* src = buffer_min[core];
    
    // Set recording flag if any core was recording
    if(src->recording){
      result_min->recording = true;
    }
    
    // Keep the latest exit timestamp
    if(src->prev_exit_timestamp > result_min->prev_exit_timestamp){
      result_min->prev_exit_timestamp = src->prev_exit_timestamp;
    }
    
    // Merge each histogram type
    merge_single_histogram(&result_min->total_lh, &src->total_lh);
    merge_single_histogram(&result_min->entry_to_ra_lh, &src->entry_to_ra_lh);
    merge_single_histogram(&result_min->readahead_lh, &src->readahead_lh);
    merge_single_histogram(&result_min->readahead_nrh, &src->readahead_nrh);
    merge_single_histogram(&result_min->readahead_pp_lh, &src->readahead_pp_lh);
    merge_single_histogram(&result_min->reclaim_lh, &src->reclaim_lh);
    merge_single_histogram(&result_min->reclaim_nrh, &src->reclaim_nrh);
    merge_single_histogram(&result_min->ra_to_sleep_lh, &src->ra_to_sleep_lh);
    merge_single_histogram(&result_min->sleep_lh, &src->sleep_lh);
    merge_single_histogram(&result_min->nvme_ssd_lh, &src->nvme_ssd_lh);
    merge_single_histogram(&result_min->wakeup_to_return_lh, &src->wakeup_to_return_lh);
    merge_single_histogram(&result_min->pf_to_pf_h, &src->pf_to_pf_h);
    merge_single_histogram(&result_min->pg_allocation_lh, &src->pg_allocation_lh);
    merge_single_histogram(&result_min->swap_cache_lookup_lh, &src->swap_cache_lookup_lh);
    merge_single_histogram(&result_min->pg_allocation_sleep_lh, &src->pg_allocation_sleep_lh);
    merge_single_histogram(&result_min->bio_submission_lh, &src->bio_submission_lh);
  }

  // Merge all histograms from all cores
  for(int core = 0; core < NUM_CORES; core++){
    if(buffer_rec[core] == NULL) continue;
    
    struct fault_histograms* src = buffer_rec[core];
    
    // Set recording flag if any core was recording
    if(src->recording){
      result_rec->recording = true;
    }
    
    // Keep the latest exit timestamp
    if(src->prev_exit_timestamp > result_rec->prev_exit_timestamp){
      result_rec->prev_exit_timestamp = src->prev_exit_timestamp;
    }
    
    // Merge each histogram type
    merge_single_histogram(&result_rec->total_lh, &src->total_lh);
    merge_single_histogram(&result_rec->entry_to_ra_lh, &src->entry_to_ra_lh);
    merge_single_histogram(&result_rec->readahead_lh, &src->readahead_lh);
    merge_single_histogram(&result_rec->readahead_nrh, &src->readahead_nrh);
    merge_single_histogram(&result_rec->readahead_pp_lh, &src->readahead_pp_lh);
    merge_single_histogram(&result_rec->reclaim_lh, &src->reclaim_lh);
    merge_single_histogram(&result_rec->reclaim_nrh, &src->reclaim_nrh);
    merge_single_histogram(&result_rec->ra_to_sleep_lh, &src->ra_to_sleep_lh);
    merge_single_histogram(&result_rec->sleep_lh, &src->sleep_lh);
    merge_single_histogram(&result_rec->nvme_ssd_lh, &src->nvme_ssd_lh);
    merge_single_histogram(&result_rec->wakeup_to_return_lh, &src->wakeup_to_return_lh);
    merge_single_histogram(&result_rec->pf_to_pf_h, &src->pf_to_pf_h);
    merge_single_histogram(&result_rec->pg_allocation_lh, &src->pg_allocation_lh);
    merge_single_histogram(&result_rec->swap_cache_lookup_lh, &src->swap_cache_lookup_lh);
    merge_single_histogram(&result_rec->pg_allocation_sleep_lh, &src->pg_allocation_sleep_lh);
    merge_single_histogram(&result_rec->bio_submission_lh, &src->bio_submission_lh);
  }
}

inline void start_hist_recording(){
  init_fault_histogram_buffers();
  #pragma omp parallel
  {
    enable_pf_recording();
    enable_fault_hist_recording();
  }
}

inline void stop_hist_recording(struct fault_histograms* merged, struct fault_histograms* merged_min, struct fault_histograms* merged_rec){
  #pragma omp parallel
  {
    int ret = 0;

    ret = get_fault_histograms(buffer_min[omp_get_thread_num()], sizeof(fault_histograms),0);
    if(ret){
      printf("get_fault_histograms 0 syscall failed with return code %d\n", ret);
    }

    ret = get_fault_histograms(buffer[omp_get_thread_num()], sizeof(fault_histograms),1);
    if(ret){
      printf("get_fault_histograms 1 syscall failed with return code %d\n", ret);
    }

    ret = get_fault_histograms(buffer_rec[omp_get_thread_num()], sizeof(fault_histograms),2);
    if(ret){
      printf("get_fault_histograms 2 syscall failed with return code %d\n", ret);
    }

    // printf("Thread %d retrieved fault histograms\n", omp_get_thread_num());
    disable_pf_recording();
    disable_fault_hist_recording();
  }
  merge_fault_histograms(merged,merged_min,merged_rec);
}

#endif  // KERNEL_UTILS_H_
