#!/bin/bash
RESULT_DIR="results" # "." for current folder

kernels=("tc" "bc" "bfs" "pr" "cc" "sssp")
graphs=("twitter" "kron" "urand" "web" "road")
available_memory=("30")
ocfs=("1")

swap_readahead="ON"                   # "ON" or "OFF"
file_readahead="ON"                   # "ON" or "OFF"
NUM_SWAP_PARTITIONS=1                 # can be 1, 2, 3, and 4 in our system (terra)
SWAP_TYPE="SATA"                      # "SATA" or "NVME"
NUM_CORES=$(lscpu | grep -w "CPU(s):" | grep -v "NUMA" | awk '{print $2}') #8
GRAPH_DIR="/share/graphs"
file_partition="sda1" #might be nvme0n1p2. use lsblk to figure it out

declare -A kernel_args
kernel_args["bc"]="-i3 -n1"
kernel_args["bfs"]="-n5"
kernel_args["cc"]="-n5"
kernel_args["pr"]="-i1000 -t1e-4 -n5"
kernel_args["sssp"]="-n5 -d2"
kernel_args["tc"]="-n1"
kernel_args["tc_road"]="-n1"

########################################  FUNCTIONS  ###############################
# measures the workload size in MB
function measure_workload_size() {
	local kernel=$1
	local graph_path=$2
	local graph
	graph=$(basename "$graph_path" | sed -E 's/(U\.sg|\.sg|\.wsg)//')		# get the graph name and remove extensions 
	local max_rss=0
	# don't measure workload size, since it takes too much time.
	# instead use premeasured sizes
	# Check if kernel is 'tc', or starts with 'tc_' or 'tc-'
	case "$kernel" in
		tc|tc_*|tc-*)
			case "$graph" in
				road)    echo "603"	;;
				kron)    echo "18598" ;;
				twitter) echo "10359" ;;
				urand)   echo "18877" ;;
				web)     echo "14935" ;; # relabeling makes max RSS smaller
			esac
			;;
		bc|bc_*|bc-*)
			case "$graph" in
				road)    echo "1304" 	;;
				kron)    echo "20409" ;;
				twitter) echo "13717" ;;
				urand)   echo "20976" ;;
				web)     echo "17101" ;;
			esac
			;;
		bfs|bfs_*|bfs-*)
			case "$graph" in
				road)    echo "1022" 	;;
				kron)    echo "18599" ;;
				twitter) echo "12919" ;;
				urand)   echo "18879" ;;
				web)     echo "16271" ;;
			esac
			;;
		cc|cc_*|cc-*)
			case "$graph" in
				road)    echo "603" ;;
				kron)    echo "18598" ;;
				twitter) echo "10360" ;;
				urand)   echo "18879" ;;
				web)     echo "14935" ;;
			esac
			;;
		pr|pr_*|pr-*)
			case "$graph" in
				road)    echo "1016" ;;
				kron)    echo "18599" ;;
				twitter) echo "12918" ;;
				urand)   echo "18879" ;;
				web)     echo "16271" ;;
			esac
			;;
		sssp|sssp_*|sssp-*)
			case "$graph" in
				road)    echo "18745" ;;
				kron)    echo "35348" ;;
				twitter) echo "24579" ;;
				urand)   echo "36992" ;;
				web)     echo "31526" ;;
			esac
			;;
		*)
			/usr/bin/time -v -o max_rss.txt ../../"$kernel" -f "$graph_path" -n1 -p >/dev/null
			max_rss=$(grep Maximum max_rss.txt | awk '{print $6}') # max_rss in kB
			max_rss=$((max_rss / 1000))                            # max_rss in MB
			rm max_rss.txt
			echo $max_rss
			;;
	esac
}

# return the proper graph for the specified kernel (sg, wsg, U.sg)
function get_proper_graph() {
	local kernel=$1
	local graph=$2

	case "$kernel" in
		sssp|sssp_*|sssp-*)
			echo "$GRAPH_DIR/$graph.wsg" # sssp uses weighted graphs (.wsg)
			;;
		tc|tc_*|tc-*)
			echo "$GRAPH_DIR/${graph}U.sg" # tc uses undirected graphs (U.sg)
			;;
		cc|cc_*|cc-*)
			echo "$GRAPH_DIR/${graph}.sg" # cc uses undirected graphs (.sg)
			;;
		bc|bc_*|bc-*)
			echo "$GRAPH_DIR/${graph}U.sg" # bc uses undirected graphs (.sg)
			;;
		*)
			echo "$GRAPH_DIR/$graph.sg" # other kernels use non-weighted graphs (.sg)
			;;
	esac
}

# return the proper args for the specified kernel (e.g. -n1)
function get_kernel_args() {
	local kernel=$1
	local graph=$2
	case $kernel in
		bc|bc_*|bc-*)
			echo "${kernel_args["bc"]}" ;;
		bfs|bfs_*|bfs-*)
			echo "${kernel_args["bfs"]}" ;;
		cc|cc_*|cc-*)
			echo "${kernel_args["cc"]}" ;;
		pr|pr_*|pr-*)
			echo "${kernel_args["pr"]}" ;;
		sssp|sssp_*|sssp-*)
			echo "${kernel_args["sssp"]}" ;;
		tc|tc_*|tc-*)
			if [ "$graph" == "road" ]; then
				echo "${kernel_args["tc_road"]}"
			else
				echo "${kernel_args["tc"]}"
			fi
			;;
		*)
			echo ;;
	esac
}

#turns on swap readheads
function turn_on_swap_ra() {
	if ! sudo -n true 2>/dev/null; then
		echo "Warning: This script requires sudo privileges. ⚠️"
		exit 1
	fi
	echo 3 >/proc/sys/vm/page-cluster #swap readahead is turned on with 2^3=8 pages
	# sudo sysctl -w vm.page-cluster=3  #does the same as above
}
#turns off swap readheads
function turn_off_swap_ra() {
	if ! sudo -n true 2>/dev/null; then
		echo "Warning: This script requires sudo privileges. ⚠️"
		exit 1
	fi
	echo 0 >/proc/sys/vm/page-cluster #swap readahead is turned on with 2^3=8 pages
	# sudo sysctl -w vm.page-cluster=0  #does the same as above
}
#turns on file readheads
function turn_on_file_ra() {
	sudo blockdev --setra 256 /dev/$file_partition #file readahead is turned on with 256 sectors = 32 pages
}
#turns off file readheads
function turn_off_file_ra() {
	sudo blockdev --setra 0 /dev/$file_partition #file readahead is turned off
}
# Sets the number of active swap partitions to $1
function set_swap_partition_count() {
	local swap_partitions=$1

	# Find all swap partitions of size 60G, filtered by SWAP_TYPE
	if [ "$SWAP_TYPE" == "SATA" ]; then
		# SATA devices start with 'sd' (e.g. sdb1, sdc1)
		readarray -t blocks < <(lsblk | grep '60G' | awk -F '└─| ' '{print $2}' | grep '^sd')
	else
		# NVME devices start with 'nvme' (e.g. nvme0n1p1)
		readarray -t blocks < <(lsblk | grep '60G' | awk -F '└─| ' '{print $2}' | grep '^nvme')
	fi
	for i in "${!blocks[@]}"; do
		blocks[i]="/dev/${blocks[$i]}"
	done

	# Find all currently active swap devices
	readarray -t swap_devices < <(lsblk | grep '\[SWAP\]' | awk -F '└─| ' '{print $2}')
	for i in "${!swap_devices[@]}"; do
		swap_devices[i]="/dev/${swap_devices[$i]}"
	done

	# Turn off all swap devices
	for device in "${swap_devices[@]}"; do
		sudo swapoff "$device"
	done

	# Turn on only the requested number of swap partitions
	for ((i = 0; i < swap_partitions && i < ${#blocks[@]}; i++)); do
		sudo swapon --priority=0 "${blocks[$i]}"
	done
}

function adjust_the_settings() {
	echo "Number of cores: $NUM_CORES"
	echo -n "Kernels: "
	printf "%s " "${kernels[@]}"
	echo
	echo -n "Graphs: "
	printf "%s " "${graphs[@]}"
	echo
	echo -n "Available memories: "
	printf "%s " "${available_memory[@]}"
	echo
	echo -n "Over Committing Factors: "
	printf "%s " "${ocfs[@]}"
	echo
	echo "Swap Readahead: $swap_readahead"
	if [ "$swap_readahead" == "ON" ]; then
		turn_on_swap_ra
		echo "Swap readahead turned on"
	else
		turn_off_swap_ra
		echo "Swap readahead turned off"
	fi
	echo "File Readahead: $file_readahead"
	if [ "$file_readahead" == "ON" ]; then
		turn_on_file_ra
		echo "File readahead turned on"
	else
		turn_off_file_ra
		echo "File readahead turned off"
	fi
	echo "Number of swap partitions: $NUM_SWAP_PARTITIONS"
	set_swap_partition_count "$NUM_SWAP_PARTITIONS"
	swap_partitions=$(lsblk | awk '/\[SWAP\]/{print $4}')
	echo "Active Swap Partitions: $swap_partitions"
	echo "Graph Directory: $GRAPH_DIR"
	echo
}

# Sets the memory limit for the cgroup 'gapbs_group' in MB
function set_memory_limit() {
	local workload_size=$1
	local memory_percentage=$2

	for cmd in cgcreate cgset; do
		if ! command -v "$cmd" >/dev/null 2>&1; then
			echo "$cmd not found. Installing libcgroup-tools..."
			sudo apt-get update
			sudo apt-get install -y libcgroup-tools
			break
		fi
	done

	local mem_size=$((workload_size * memory_percentage / 100))

	# Set memory limit for the cgroup in bytes
	# Convert memory size from MB to bytes
	local mem_limit_bytes=$((mem_size * 1024 * 1024))
	# Ensure memory cgroup is mounted and gapbs_group exists
	if [ ! -d /sys/fs/cgroup/memory ]; then
		sudo mkdir -p /sys/fs/cgroup/memory
		sudo mount -t cgroup -o memory memory /sys/fs/cgroup/memory
	fi
	if [ ! -d /sys/fs/cgroup/memory/gapbs_group ]; then
		sudo cgcreate -g memory:gapbs_group
	fi
	# echo "$mem_limit_bytes" | sudo tee /sys/fs/cgroup/memory/gapbs_group/memory.limit_in_bytes >/dev/null
	sudo cgset -r memory.limit_in_bytes="$mem_limit_bytes" gapbs_group

  # Set soft limit to 10% less than hard limit
   local soft_limit_bytes=$((mem_limit_bytes * 50 / 100))
  #sudo cgset -r memory.soft_limit_in_bytes="$soft_limit_bytes" gapbs_group
   sudo cgset -r memory.soft_limit_in_bytes=-1 gapbs_group

  # Set swap limit to maximum (effectively unlimited)
  sudo cgset -r memory.memsw.limit_in_bytes=-1 gapbs_group 2>/dev/null || true


	if [ "${MEM_LIMIT_SLEEP:-0}" -eq 1 ]; then
		sleep 1
	fi
	echo "$mem_size"
}

function build_filename() {
	local kernel=$1
	local graph=$2
	local percentage=$3
	local ocf=$4

	local filename="$kernel-$graph-$percentage-$ocf"
	echo "$filename"
}

function clear_pagecache() {
	sync
	sudo sh -c 'echo 1 > /proc/sys/vm/drop_caches'
	sleep 1
	sync
}

function calculate_diffs() {
  python3 ../../get_proc_stat_diffs.py stat_begin.stats stat_end.stats > proc-stat.stats
  python3 ../../get_proc_sched_diffs.py sched_begin.stats sched_end.stats > proc-sched.stats
  python3 ../../get_system_stat_diffs.py proc_stat_begin.stats proc_stat_end.stats > sysproc-stat.stats
}

# Execute a single benchmark run
function execute_benchmark() {
  local kernel=$1
  local graph=$2
  local graph_path=$3
  local args=$4
  local percentage=$5
  local ocf=$6
  local mem_size=$7
  local threads=$8
  local output_dirs=("${@:9}")

  # Create associative array for cleaner stat file mapping
  declare -A stat_dirs
  stat_dirs["disk"]="${output_dirs[0]}"
  stat_dirs["perf"]="${output_dirs[1]}"
  stat_dirs["time"]="${output_dirs[2]}"
  stat_dirs["proc-stat"]="${output_dirs[3]}"
  stat_dirs["proc-sched"]="${output_dirs[4]}"
	stat_dirs["faults"]="${output_dirs[5]}"
	stat_dirs["sysproc-stat"]="${output_dirs[6]}"
	stat_dirs["log"]="${output_dirs[7]}"
  
  local cmd_args="$args"
  local output_file_name
  output_file_name=$(build_filename "$kernel" "$graph" "$percentage" "$ocf")
  output_file_name="$output_file_name-$NUM_SWAP_PARTITIONS-$mem_size"
  
	# Prepare the command with "sudo OMP_NUM_THREADS=$threads" later
  local command="cgexec -g memory:gapbs_group ../../$kernel -f $graph_path $cmd_args"
  command="OMP_NUM_THREADS=$threads $command"
  command="sudo $command >"${stat_dirs["log"]}/$output_file_name.log" 2>&1"

  echo "$command"
  echo "⏳"
  
  # Execute the benchmark
  if ! eval "$command"; then
    echo "ERROR: Benchmark execution failed for $kernel $graph ❌" >&2
    return 1
  fi
  
  sleep 0.2

  echo " Calculating diffs... ⏳"
  calculate_diffs
  echo " Created proc-stat.stats and proc-sched.stats ✅"

  # Clean up intermediate files
  rm -f stat_begin.stats stat_end.stats  
  rm -f sched_begin.stats sched_end.stats
  rm -f proc_stat_begin.stats proc_stat_end.stats
  echo " Removed intermediate files 🧹"
  
  echo " Saving statistics and trace files... 💾"
  # Move statistics files
	for stat_type in disk perf time sysproc-stat proc-stat proc-sched faults; do
    local stat_file="${stat_type}.stats"
    if [[ -f "$stat_file" ]]; then
      if [[ -n "${stat_dirs[$stat_type]}" ]]; then
        mv "$stat_file" "${stat_dirs[$stat_type]}/$output_file_name.$stat_type.stats"
      else
        echo "WARNING: No directory mapping for stat type $stat_type ⚠️" >&2
      fi
    else
      echo "WARNING: $stat_file not found ⚠️" >&2
    fi
  done
  echo "----------------------------------------"
  return 0
}



# Main benchmark execution function
function run_benchmarks() {
  for kernel in "${kernels[@]}"; do
    echo "📌 Processing kernel: $kernel"
    
    # Create directory structure
    local kernel_dir="$RESULT_DIR/$kernel"
    local disk_stats_dir="$kernel_dir/disk"
    local perf_stats_dir="$kernel_dir/perf"
    local time_stats_dir="$kernel_dir/time"
    local proc_stat_stats_dir="$kernel_dir/proc-stat"
    local proc_sched_stats_dir="$kernel_dir/proc-sched"
    local faults_dir="$kernel_dir/faults"
    local systemwide_proc_stat_stats_dir="$kernel_dir/sysproc-stat"
    local log_dir="$kernel_dir/log"
	local output_dirs=("$disk_stats_dir" "$perf_stats_dir" "$time_stats_dir" "$proc_stat_stats_dir" "$proc_sched_stats_dir" "$faults_dir" "$systemwide_proc_stat_stats_dir" "$log_dir")
    
    if [[ ! -d "$kernel_dir" ]]; then
      echo "Creating directory structure for kernel $kernel... ⏳"
      mkdir -p "${output_dirs[@]}"
    fi
    
    for graph in "${graphs[@]}"; do
      echo "Processing graph: $graph ☍"
      
      local graph_path
      graph_path=$(get_proper_graph "$kernel" "$graph")
      local args
      args=$(get_kernel_args "$kernel" "$graph")
      local workload_size
      workload_size=$(measure_workload_size "$kernel" "$graph_path")
      
      echo "($kernel,$graph) workload_size = $workload_size MB 💿"
      
      for percentage in "${available_memory[@]}"; do
        local mem_size
        mem_size=$(set_memory_limit "$workload_size" "$percentage")
        echo "Set memory limit to $mem_size MB ($percentage% of $workload_size MB) 🔻"
        
        for ocf in "${ocfs[@]}"; do
          local threads=$((ocf * NUM_CORES))
          
          execute_benchmark "$kernel" "$graph" "$graph_path" "$args" \
            "$percentage" "$ocf" "$mem_size" "$threads" \
            "${output_dirs[@]}"
          
        done
      done
    done
  done
}

function enable_kernel_delay_accounting() {
  if ! sudo -n true 2>/dev/null; then
    echo "Error: This script requires sudo privileges for kernel delay accountings. ⚠️"
    exit 1
  fi
  sudo sysctl -w kernel.perf_event_paranoid=-1
  sudo sysctl -w kernel.kptr_restrict=0
  sudo sh -c 'echo 1 > /proc/sys/kernel/task_delayacct'
  sudo sh -c 'echo 1 > /proc/sys/kernel/sched_schedstats'
  # sudo sh -c 'echo 1 > /proc/sys/kernel/bpf_stats_enabled'
}

# Main script execution
function main() {
    echo "Starting performance evaluation script... 🚀"
    echo "Ensuring kernel delay accountings are enabled... ⏳"
    enable_kernel_delay_accounting
    
    if [[ ! -d "$RESULT_DIR" ]]; then
        mkdir -p -v "$RESULT_DIR"
    fi
    
    if [[ ! -d "$GRAPH_DIR" ]]; then
        echo "ERROR: Graph directory does not exist: $GRAPH_DIR ❌" >&2
        exit 1
    fi
    
    echo "Creating cgroup 'gapbs_group' if it doesn't exist... ⏳"
    sudo cgcreate -g memory:gapbs_group
    adjust_the_settings
    
    run_benchmarks
    
    echo "All benchmarks completed! 🎉"
    echo "Restoring default system settings... ♻️"
    turn_on_swap_ra
    turn_on_file_ra
}

# Execute main function
main "$@"
