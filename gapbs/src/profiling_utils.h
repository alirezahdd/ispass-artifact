#ifndef profiling_utils_h
#define profiling_utils_h

extern "C" {
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
#include <linux/perf_event.h>
#include <string.h>
#include <asm/unistd.h>
#include <sys/ioctl.h>
}

#ifndef NUM_CORES // used -DNUM_CORES=$(shell nproc) in Makefile
#define NUM_CORES 16  // fallback default
#endif

/* ===========================================================================
 * RUSAGE-RELATED FUNCTIONS
 * start / stop / meausre rusage counters
 * ========================================================================== */

struct rusage usage_start, usage_end;
struct timeval wall_time_start, wall_time_end;

void start_time_stats(){
	gettimeofday(&wall_time_start, NULL);
	getrusage(RUSAGE_SELF, &usage_start);
}

void stop_time_stats(){
	gettimeofday(&wall_time_end, NULL);
	getrusage(RUSAGE_SELF, &usage_end);
}

void measure_time_stats(){
  struct timeval user_time_diff, sys_time_diff, wall_time_diff;
  double wall_time, user_time, sys_time, idle_time;
	timersub(&usage_end.ru_utime,&usage_start.ru_utime,&user_time_diff);
	timersub(&usage_end.ru_stime,&usage_start.ru_stime,&sys_time_diff);
	timersub(&wall_time_end,&wall_time_start,&wall_time_diff);
	wall_time = (double) wall_time_diff.tv_sec + (0.000001 * (double) wall_time_diff.tv_usec);
	user_time = (double) user_time_diff.tv_sec + (0.000001 * (double) user_time_diff.tv_usec);
	sys_time = (double) sys_time_diff.tv_sec + (0.000001 * (double) sys_time_diff.tv_usec);
	idle_time = (wall_time * NUM_CORES) - (user_time + sys_time);
		
	FILE *f = fopen("time.stats", "w");
  fprintf(f, 
    "%-10s %12.6f\n"
    "%-10s %12.6f\n"
    "%-10s %12.6f\n"
    "%-10s %12.6f\n",
    "User", user_time,
    "System", sys_time,
    "Idle", idle_time,
    "Elapsed", wall_time);
	fclose(f);

  auto major_faults = usage_end.ru_majflt - usage_start.ru_majflt;
  auto minor_faults = usage_end.ru_minflt - usage_start.ru_minflt;
  f = fopen("faults.stats", "w");
  fprintf(f, 
    "%-12s %10ld\n"
    "%-12s %10ld\n", 
    "Major-Faults", major_faults,
    "Minor-Faults", minor_faults);
  fclose(f);
}

/* ===========================================================================
 * TRACE-RELATED FUNCTIONS
 * Writes a trace marker to the kernel tracing system
 * ========================================================================== */

void trace_marker(const char *msg) {
  FILE *f = fopen("/sys/kernel/debug/tracing/tracing_on", "r");
  if (f) {
    int tracing_enabled = 0;
    // Check if tracing is enabled
    if (fscanf(f, "%d", &tracing_enabled) == 1 && tracing_enabled) { 
      fclose(f);
      f = fopen("/sys/kernel/debug/tracing/trace_marker", "w");
      if (f) {
        fprintf(f, "%s\n", msg);
        fclose(f);
      }
    } else {
      fclose(f);
    }
  }
}

/* ===========================================================================
 * PERF-RELATED FUNCTIONS
 * Setup / start / stop / cleanup perf counters
 * ========================================================================== */
struct perf_counters {
    int fd_user_time;
    int fd_kernel_time;
    int fd_user_instr;
    int fd_kernel_instr;
};

struct perf_counters perf_ctrs;

static long perf_event_open(struct perf_event_attr *hw_event,
                            pid_t pid, int cpu,
                            int group_fd, unsigned long flags) {
  return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags);
}

static int open_counter(uint32_t type, uint64_t config,
                        int exclude_user, int exclude_kernel,
                        int group_fd) {
  struct perf_event_attr pe;
  memset(&pe, 0, sizeof(pe));
  pe.type = type;
  pe.size = sizeof(pe);
  pe.config = config;
  pe.disabled = 1;
  pe.exclude_user = exclude_user;
  pe.exclude_kernel = exclude_kernel;
  pe.exclude_hv = 1;  // ignore hypervisor
  pe.inherit = 1;     // allow counting across child threads (open before threads start)
  pe.exclude_idle = 1; // don't count when idle
  

  int fd = perf_event_open(&pe, 0, -1, group_fd, 0);
  if (fd == -1) {
    perror("perf_event_open");
    exit(1);
  }
  return fd;
}

/*
  * Setup counters before any threads are created by omp
  * Must be called at the beginning of the program.
  * PERF_COUNT_SW_CPU_CLOCK does not differentiate user/kernel time,
  * so we use PERF_COUNT_HW_CPU_CYCLES instead.
  * Open each counter as its own leader (no grouping) so exclude_user/exclude_kernel
  * are applied independently.
*/
struct perf_counters setup_counters(void) {
  struct perf_counters c;
  c.fd_user_time = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES,
                                0, 1, -1);
  c.fd_kernel_time = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES,
                                  1, 0, -1);
  c.fd_user_instr = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS,
                                  0, 1, -1);
  c.fd_kernel_instr = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS,
                                    1, 0, -1);
  return c;
}

/* Setup counters before any threads are created by omp
 * Must be called at the begining of the program.
*/
void initialize_perf_measurements(){
  perf_ctrs = setup_counters();
}

void start_counters(struct perf_counters *c) {
  // Reset & enable each counter separately (no group operations)
  ioctl(c->fd_user_time, PERF_EVENT_IOC_RESET, 0);
  ioctl(c->fd_kernel_time, PERF_EVENT_IOC_RESET, 0);
  ioctl(c->fd_user_instr, PERF_EVENT_IOC_RESET, 0);
  ioctl(c->fd_kernel_instr, PERF_EVENT_IOC_RESET, 0);

  ioctl(c->fd_user_time, PERF_EVENT_IOC_ENABLE, 0);
  ioctl(c->fd_kernel_time, PERF_EVENT_IOC_ENABLE, 0);
  ioctl(c->fd_user_instr, PERF_EVENT_IOC_ENABLE, 0);
  ioctl(c->fd_kernel_instr, PERF_EVENT_IOC_ENABLE, 0);
}

double get_cpu_frequency() {
  FILE *fp = fopen("/proc/cpuinfo", "r");
  if (!fp) {
    perror("Failed to open /proc/cpuinfo");
    return 0.0;
  }
  
  char line[256];
  double freq_mhz = 0.0;
  
  while (fgets(line, sizeof(line), fp)) {
    if (strstr(line, "cpu MHz")) {
      if (sscanf(line, "cpu MHz : %lf", &freq_mhz) == 1) {
          break;
      }
    }
  }
  fclose(fp);
  
  return freq_mhz * 1e6; // Convert MHz to Hz
}

void stop_counters(struct perf_counters *c,
                   long long *cycles_user, long long *cycles_kernel,
                   long long *instr_user, long long *instr_kernel) {
  // Disable each counter and read them individually
  ioctl(c->fd_user_time, PERF_EVENT_IOC_DISABLE, 0);
  ioctl(c->fd_kernel_time, PERF_EVENT_IOC_DISABLE, 0);
  ioctl(c->fd_user_instr, PERF_EVENT_IOC_DISABLE, 0);
  ioctl(c->fd_kernel_instr, PERF_EVENT_IOC_DISABLE, 0);

  ssize_t ret;
  ret = read(c->fd_user_time, cycles_user, sizeof(long long));
  if (ret != (ssize_t)sizeof(long long)) {
    perror("read user_time");
    *cycles_user = -1;
  }

  ret = read(c->fd_kernel_time, cycles_kernel, sizeof(long long));
  if (ret != (ssize_t)sizeof(long long)) {
    perror("read kernel_time");
    *cycles_kernel = -1;
  }

  ret = read(c->fd_user_instr, instr_user, sizeof(long long));
  if (ret != (ssize_t)sizeof(long long)) {
    perror("read user_instr");
    *instr_user = -1;
  }

  ret = read(c->fd_kernel_instr, instr_kernel, sizeof(long long));
  if (ret != (ssize_t)sizeof(long long)) {
    perror("read kernel_instr");
    *instr_kernel = -1;
  }

  double time_user_s = 0, time_kernel_s = 0;
  double cpu_freq_hz = get_cpu_frequency(); // in Hz
  if (*cycles_user != -1)
    time_user_s = (*cycles_user) / cpu_freq_hz;
  if (*cycles_kernel != -1)
    time_kernel_s = (*cycles_kernel) / cpu_freq_hz;
  
  printf("cpu_frequency from /proc/cpuinfo = %f\n", cpu_freq_hz);

  FILE *f = fopen("perf.stats", "w");
  if (f) {
    fprintf(f, 
      "%-20s\t%15.6f\t%s\n"
      "%-20s\t%15.6f\t%s\n"
      "%-20s\t%15lld\t%s\n"
      "%-20s\t%15lld\t%s\n"
      "%-20s\t%15lld\t%s\n"
      "%-20s\t%15lld\t%s\n",
      "User-Time:", time_user_s, "cycles:u/cpufreq",
      "Kernel-Time:", time_kernel_s, "cycles:k/cpufreq",
      "User-Cycles:", *cycles_user, "Hardware-event",
      "Kernel-Cycles:", *cycles_kernel, "Hardware-event",
      "User-Instructions:", *instr_user, "Hardware-event",
      "Kernel-Instructions:", *instr_kernel, "Hardware-event");
    fclose(f);
  } else perror("Failed to open perf.stats for writing");
}

void cleanup_counters(struct perf_counters *c) {
  close(c->fd_user_time);
  close(c->fd_kernel_time);
  close(c->fd_user_instr);
  close(c->fd_kernel_instr);
}

/* ===========================================================================
 * DISKSTAT-RELATED FUNCTIONS
 * start / stop
 * ========================================================================== */
// This is a global variable to store the diskstat process ID
pid_t diskstat_pid = -1;

/*
 * We should move the diskstat process out of the cgroup 
 */ 
void move_to_cgroup(const char *cgroup_path, pid_t pid){
	char path[256];
	snprintf(path, sizeof(path), "%s/cgroup.procs", cgroup_path);
	std::cout << "moving the process " << pid << " to " << path << std::endl;
	FILE *f = fopen(path, "w");
	if (f == NULL) {
		perror("Failed to open cgroup.procs");
		exit(EXIT_FAILURE);
	}
	fprintf(f, "%d", pid);
	fclose(f);
}

inline void start_disk_stats(const char* result_file_name){
  pid_t pid = fork();
  if (pid < 0) {
    perror("fork failed");
    exit(EXIT_FAILURE);
  } else if (pid == 0) { // Child process
    const char *root_cgroup = "/sys/fs/cgroup/memory";
	  move_to_cgroup(root_cgroup, getpid());
    execlp("/home/aliha951/ipdps-gapbs/gather_diskstats.sh", "/home/aliha951/ipdps-gapbs/gather_diskstats.sh", result_file_name, NULL);
    perror("execlp failed");
    exit(EXIT_FAILURE);
  }
  // Parent process continues
  diskstat_pid = pid;
}

inline void stop_disk_stats() {
  if (diskstat_pid > 0) {
    char command[256];
    snprintf(command, sizeof(command), "sudo pkill -f 'gather_diskstats.sh'");
    int ret = system(command);
    if (ret==-1)	std::cout << "could not stop diskstat gathering\n";
  }
}

/* ===========================================================================
 * PROC_PID-RELATED FUNCTIONS
 * snapshot 
 * use snapshot_proc_pid(BEGIN) and snapshot_proc_pid(END) at the beginning and
 * end of the ROI
 * ========================================================================== */
typedef enum {
  BEGIN,
  END
} SnapshotPoint;

static inline int copy_file_c(const char* src_path, const char* dest_path) {
  FILE* src = fopen(src_path, "r");
  if (!src) {
    perror("Failed to open source file for reading");
    return 0; // Failure
  }

  FILE* dest = fopen(dest_path, "w");
  if (!dest) {
    fclose(src);
    perror("Failed to open destination file for writing");
    return 0; // Failure
  }

  char buffer[4096];
  size_t bytes_read;
  while ((bytes_read = fread(buffer, 1, sizeof(buffer), src)) > 0) {
    if (fwrite(buffer, 1, bytes_read, dest) != bytes_read) {
      perror("Failed to write to destination file");
      fclose(src);
      fclose(dest);
      return 0; // Failure
    }
  }

  fclose(src);
  fclose(dest);
  return 1; // Success
}

inline void snapshot_proc_pid(SnapshotPoint point) {
  pid_t pid = getpid();
  const char* suffix = (point == BEGIN) ? "begin" : "end";
  
  char src_path[256];
  char dest_path[256];

  // Snapshot /proc/[pid]/stat
  snprintf(src_path, sizeof(src_path), "/proc/%d/stat", pid);
  snprintf(dest_path, sizeof(dest_path), "stat_%s.stats", suffix);
  if (!copy_file_c(src_path, dest_path)) {
    fprintf(stderr, "Error: Could not snapshot %s\n", src_path);
  }

  // Snapshot /proc/[pid]/sched
  snprintf(src_path, sizeof(src_path), "/proc/%d/sched", pid);
  snprintf(dest_path, sizeof(dest_path), "sched_%s.stats", suffix);
  if (!copy_file_c(src_path, dest_path)) {
    fprintf(stderr, "Error: Could not snapshot %s\n", src_path);
  }
}
/* ===========================================================================
 * PROC_STAT-RELATED FUNCTIONS
 * snapshot 
 * use snapshot_proc_stat(BEGIN) and snapshot_proc_stat(END) at the beginning and end of
 * the ROI
 * ========================================================================== */

inline void snapshot_proc_stat(SnapshotPoint point) {
  const char* suffix = (point == BEGIN) ? "begin" : "end";
  
  char src_path[256];
  char dest_path[256];

  // Snapshot /proc/stat
  snprintf(src_path, sizeof(src_path), "/proc/stat");
  snprintf(dest_path, sizeof(dest_path), "proc_stat_%s.stats", suffix);
  if (!copy_file_c(src_path, dest_path)) {
    fprintf(stderr, "Error: Could not snapshot %s\n", src_path);
  }
}
  

#endif // profiling_utils_h