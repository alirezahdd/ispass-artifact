#!/usr/bin/env python3
import re
import csv
import argparse
from pathlib import Path

def parse_time_stats(time_file):
    """Parse .time.stats file to extract timing information."""
    user_time = 0
    system_time = 0
    elapsed_time = 0
    idle_time = 0
    
    with open(time_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('user') or line.startswith('User'):
                user_time = float(line.split()[1])
            elif line.startswith('sys') or line.startswith('System'):
                system_time = float(line.split()[1])
            elif line.startswith('elapsed') or line.startswith('Elapsed'):
                elapsed_str = line.split()[1]
                parts = elapsed_str.split(':')
                if len(parts) == 2:
                    elapsed_time = float(parts[0]) * 60 + float(parts[1])
                else:
                    elapsed_time = float(parts[0])
            elif line.startswith('Idle'):
                idle_time = float(line.split()[1])
    
    # If idle_time is directly provided, use it; otherwise calculate
    if idle_time == 0:
        idle_time = (elapsed_time * 16) - user_time - system_time
    
    return user_time, system_time, idle_time, elapsed_time

def parse_log_file(log_file):
    """Parse .log file to extract histogram statistics from merged section."""
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Find the merged section
    merged_match = re.search(r'merged:\s*===\s*Fault Histograms\s*===.*?(?=merged min:|merged rec:|$)', content, re.DOTALL)
    
    if not merged_match:
        return 0, 0
    
    merged_section = merged_match.group(0)
    
    # Parse sleep_lh for idle_io
    sleep = 0
    sleep_match = re.search(r'sleep_lh:(.*?)(?=\n\S|\Z)', merged_section, re.DOTALL)
    if sleep_match:
        bin_pattern = r'bin_\d+:\s*count=(\d+)\s+min=(\d+)\s+max=(\d+)\s+sum=(\d+)'
        bins = re.findall(bin_pattern, sleep_match.group(1))
        total_count = sum(int(b[0]) for b in bins if int(b[0]) > 0)
        total_sum = sum(int(b[3]) for b in bins if int(b[0]) > 0)
        if total_count > 0:
            sleep = total_sum / 2.2e9  # Convert to seconds
    
    # Parse pg_allocation_sleep_lh for idle_pg_alloc
    pg_alloc_sleep = 0
    pg_alloc_sleep_match = re.search(r'pg_allocation_sleep_lh:(.*?)(?=\n\S|\Z)', merged_section, re.DOTALL)
    if pg_alloc_sleep_match:
        bin_pattern = r'bin_\d+:\s*count=(\d+)\s+min=(\d+)\s+max=(\d+)\s+sum=(\d+)'
        bins = re.findall(bin_pattern, pg_alloc_sleep_match.group(1))
        total_count = sum(int(b[0]) for b in bins if int(b[0]) > 0)
        total_sum = sum(int(b[3]) for b in bins if int(b[0]) > 0)
        if total_count > 0:
            pg_alloc_sleep = total_sum / 2.2e9  # Convert to seconds
    
    return sleep, pg_alloc_sleep

def parse_taskstats_file(taskstats_file):
    """Parse .taskstats.stats file to extract IRQ delay."""
    irq_delay = 0
    
    with open(taskstats_file, 'r') as f:
        for line in f:
            if 'cpu_delay_total' in line:
                irq_delay = float(line.split()[1]) / 1e9  # Convert to seconds
                break
    
    return irq_delay

def main():
    parser = argparse.ArgumentParser(description='Parse comparison statistics')
    parser.add_argument('algorithm', type=str, help='Algorithm name')
    parser.add_argument('graph', type=str, help='Graph name')
    parser.add_argument('--results-dir', type=str, default='results/normal', help='Results directory path or name')
    parser.add_argument('--results-label', type=str, default=None, help='Label to store in CSV for this dataset')
    parser.add_argument('--output', type=str, default='comparison.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    results_label = args.results_label or Path(args.results_dir).name

    # For baseline dataset, use existing breakdown CSV.
    root_dir = Path(__file__).resolve().parents[2]

    if results_label == 'normal':
        csv_path = root_dir / 'outputs' / 'parsed' / 'breakdowns' / f'{args.algorithm}_breakdown.csv'
        
        if not csv_path.exists():
            print(f"Error: Breakdown CSV not found for {args.algorithm}")
            return
        
        # Read from breakdown CSV
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['graph'] == args.graph:
                    user_time = float(row['user_time'])
                    system_time = float(row['system_time'])
                    idle_time = float(row['idle_time'])
                    elapsed_time = float(row['elapsed_time'])
                    sleep = float(row['sleep'])
                    sleep_pg_allocation = float(row['sleep_pg_allocation'])
                    irq_delay = float(row['irq_delay'])
                    
                    # Calculate components - matching plot_complete_breakdown.py
                    system_time_adj = system_time + irq_delay
                    idle_time_adj = idle_time - irq_delay
                    idle_io = sleep
                    idle_pg_alloc = sleep_pg_allocation
                    idle_other = idle_time_adj - idle_io - idle_pg_alloc
                    break
    else:
        # For other directories, parse from raw files
        candidate = Path(args.results_dir)
        base_results = candidate if candidate.is_absolute() else (root_dir / candidate)
        alg_path = base_results / args.algorithm
        
        # Find files
        time_files = list((alg_path / 'time').glob(f'{args.algorithm}-{args.graph}-*.time.stats'))
        log_files = list((alg_path / 'log').glob(f'{args.algorithm}-{args.graph}-*.log'))
        taskstats_files = list((alg_path / 'taskstats').glob(f'{args.algorithm}-{args.graph}-*.taskstats.stats'))
        
        if not time_files:
            print(f"Error: No files found for {args.algorithm}-{args.graph} in {args.results_dir}")
            return
        
        # Parse files
        user_time, system_time, idle_time, elapsed_time = parse_time_stats(time_files[0])
        sleep, sleep_pg_allocation = parse_log_file(log_files[0]) if log_files else (0, 0)
        irq_delay = parse_taskstats_file(taskstats_files[0]) if taskstats_files else 0
        
        # Calculate components - matching plot_complete_breakdown.py logic
        system_time_adj = system_time + irq_delay
        idle_time_adj = idle_time - irq_delay
        idle_io = sleep
        idle_pg_alloc = sleep_pg_allocation
        idle_other = idle_time_adj - idle_io - idle_pg_alloc
    
    # Write to CSV
    output_path = Path(args.output)
    file_exists = output_path.exists()
    
    with open(output_path, 'a', newline='') as csvfile:
        fieldnames = ['results_dir', 'algorithm', 'graph', 'user_time', 'system_time', 
                     'idle_io', 'idle_pg_alloc', 'idle_other', 'elapsed_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'results_dir': results_label,
            'algorithm': args.algorithm,
            'graph': args.graph,
            'user_time': user_time,
            'system_time': system_time_adj,
            'idle_io': idle_io,
            'idle_pg_alloc': idle_pg_alloc,
            'idle_other': idle_other,
            'elapsed_time': elapsed_time
        })
    
    print(f"Processed {results_label}/{args.algorithm}-{args.graph}")

if __name__ == '__main__':
    main()
