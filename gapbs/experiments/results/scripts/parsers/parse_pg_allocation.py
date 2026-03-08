#!/usr/bin/env python3
import re
import csv
import argparse
from pathlib import Path

def parse_pg_allocation_lh(log_file):
    """Parse pg_allocation_lh histogram from log file to calculate average latency."""
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Find the merged section
    merged_match = re.search(r'merged:\s*===\s*Fault Histograms\s*===.*?(?=merged min:|merged rec:|$)', content, re.DOTALL)
    
    if not merged_match:
        print(f"Error: Could not find merged section in {log_file}")
        return 0, 0
    
    merged_section = merged_match.group(0)
    
    # Find pg_allocation_lh histogram
    pg_alloc_match = re.search(r'pg_allocation_lh:(.*?)(?=\n\S|\Z)', merged_section, re.DOTALL)
    
    if not pg_alloc_match:
        print(f"Error: Could not find pg_allocation_lh in {log_file}")
        return 0, 0
    
    pg_alloc_section = pg_alloc_match.group(1)
    
    # Extract all bins
    bin_pattern = r'bin_\d+:\s*count=(\d+)\s+min=(\d+)\s+max=(\d+)\s+sum=(\d+)'
    bins = re.findall(bin_pattern, pg_alloc_section)
    
    total_count = 0
    total_sum = 0
    
    for count, min_val, max_val, sum_val in bins:
        count = int(count)
        sum_val = int(sum_val)
        
        # Only include bins with actual data
        if count > 0:
            total_count += count
            total_sum += sum_val
    
    return total_count, total_sum

def main():
    parser = argparse.ArgumentParser(description='Parse page allocation latency histogram')
    parser.add_argument('algorithm', type=str, help='Algorithm name (e.g., bc, bfs, cc, pr, sssp, tc)')
    parser.add_argument('graph', type=str, help='Graph name (e.g., kron, road, twitter, urand, web)')
    parser.add_argument('--base-dir', type=str, default=None, help='Base results directory containing algorithm subdirectories')
    parser.add_argument('--output', type=str, default='pg_allocation.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    # Construct path to log file
    if args.base_dir:
        base_root = Path(args.base_dir)
    else:
        base_root = Path(__file__).resolve().parents[2] / 'results' / 'normal'
    base_path = base_root / args.algorithm / 'log'
    
    # Find the .log file for this algorithm-graph pair
    log_files = list(base_path.glob(f'{args.algorithm}-{args.graph}-*.log'))
    
    if not log_files:
        print(f"Error: No log file found for {args.algorithm}-{args.graph}")
        return
    
    log_file = log_files[0]  # Take the first matching file
    
    # Parse the log file
    total_count, total_sum = parse_pg_allocation_lh(log_file)
    
    # Calculate average (in nanoseconds)
    if total_count > 0:
        avg_latency = total_sum / total_count
    else:
        avg_latency = 0
    
    # Write to CSV
    output_path = Path(args.output)
    file_exists = output_path.exists()
    
    with open(output_path, 'a', newline='') as csvfile:
        fieldnames = ['algorithm', 'graph', 'total_count', 'total_sum', 'avg_latency_ns']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'algorithm': args.algorithm,
            'graph': args.graph,
            'total_count': total_count,
            'total_sum': total_sum,
            'avg_latency_ns': avg_latency
        })
    
    print(f"Processed {args.algorithm}-{args.graph}: Count={total_count}, Avg Latency={avg_latency:.2f} ns")

if __name__ == '__main__':
    main()
