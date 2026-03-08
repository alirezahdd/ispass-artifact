#!/usr/bin/env python3
"""
Parse performance statistics from benchmark results and generate CSV output.

This script extracts timing and histogram statistics from algorithm/graph benchmark runs
and outputs them to a CSV file for further analysis.
"""

import os
import re
import csv
import argparse
from pathlib import Path


def parse_time_stats(filepath):
    """
    Parse .time.stats file to extract User, System, and Idle times.
    
    Args:
        filepath: Path to the .time.stats file
        
    Returns:
        dict with 'user_time', 'system_time', 'idle_time', 'elapsed_time' in seconds
    """
    stats = {}
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('User'):
                stats['user_time'] = float(line.split()[1])
            elif line.startswith('System'):
                stats['system_time'] = float(line.split()[1])
            elif line.startswith('Idle'):
                stats['idle_time'] = float(line.split()[1])
            elif line.startswith('Elapsed'):
                stats['elapsed_time'] = float(line.split()[1])
    
    return stats


def parse_histogram_sum(log_content, histogram_name):
    """
    Parse a histogram from log file and sum all bin 'sum' values.
    
    Args:
        log_content: Content of the log file
        histogram_name: Name of the histogram (e.g., 'total_lh', 'sleep_lh')
        
    Returns:
        Total sum across all bins in nanoseconds
    """
    # Find the histogram section - use word boundary to match exact name
    pattern = rf'\n{histogram_name}:\s*\n.*?(?=\n\n|\n\w+.*?:|\Z)'
    match = re.search(pattern, log_content, re.DOTALL)
    
    if not match:
        return 0
    
    histogram_text = match.group(0)
    
    # Extract all sum values from bin_N lines
    bin_pattern = r'bin_\d+:.*?sum=(\d+)'
    sums = re.findall(bin_pattern, histogram_text)
    
    total_sum = sum(int(s) for s in sums)
    return total_sum


def parse_log_file(filepath):
    """
    Parse .log file to extract histogram statistics from three sections:
    merged (major without reclaim), merged min (minor), merged rec (major with reclaim)
    
    Args:
        filepath: Path to the .log file
        
    Returns:
        dict with histogram sums in nanoseconds
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Split content into three sections
    sections = {}
    
    # Extract merged section (major faults without reclaim)
    merged_match = re.search(r'merged:\s*\n(.*?)(?=merged min:|merged rec:|$)', content, re.DOTALL)
    if merged_match:
        sections['merged'] = merged_match.group(1)
    else:
        sections['merged'] = ''
    
    # Extract merged min section (minor faults)
    merged_min_match = re.search(r'merged min:\s*\n(.*?)(?=merged rec:|$)', content, re.DOTALL)
    if merged_min_match:
        sections['merged_min'] = merged_min_match.group(1)
    else:
        sections['merged_min'] = ''
    
    # Extract merged rec section (major faults with reclaim)
    merged_rec_match = re.search(r'merged rec:\s*\n(.*?)$', content, re.DOTALL)
    if merged_rec_match:
        sections['merged_rec'] = merged_rec_match.group(1)
    else:
        sections['merged_rec'] = ''
    
    # Parse histograms from each section
    stats = {
        # Total latencies from each section
        'total_maj': parse_histogram_sum(sections['merged'], 'total_lh'),
        'total_maj_rec': parse_histogram_sum(sections['merged_rec'], 'total_lh'),
        'total_min': parse_histogram_sum(sections['merged_min'], 'total_lh'),
        
        # Sleep: sum from merged + merged_rec
        'sleep': (parse_histogram_sum(sections['merged'], 'sleep_lh') + 
                 parse_histogram_sum(sections['merged_rec'], 'sleep_lh')),
        
        # Reclaim: from merged_rec only
        'reclaim': parse_histogram_sum(sections['merged_rec'], 'reclaim_lh'),
        
        # Readahead: sum from merged + merged_rec
        'readahead': (parse_histogram_sum(sections['merged'], 'readahead_lh') + 
                     parse_histogram_sum(sections['merged_rec'], 'readahead_lh')),
        
        # Sleep_pg_allocation: sum from merged + merged_rec
        'sleep_pg_allocation': (parse_histogram_sum(sections['merged'], 'pg_allocation_sleep_lh') + 
                               parse_histogram_sum(sections['merged_rec'], 'pg_allocation_sleep_lh')),
    }
    
    return stats


def parse_taskstats_file(filepath):
    """
    Parse .taskstats.stats file to extract IRQ_Delay.
    
    Args:
        filepath: Path to the .taskstats.stats file
        
    Returns:
        dict with 'irq_delay' in nanoseconds
    """
    stats = {}
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('IRQ_Delay:'):
                stats['irq_delay'] = int(line.split(':')[1].strip())
                break
    
    return stats


def find_result_files(base_dir, algorithm, graph):
    """
    Find all result files matching the algorithm and graph pattern.
    
    Args:
        base_dir: Base directory containing results
        algorithm: Algorithm name (e.g., 'bc', 'bfs')
        graph: Graph name (e.g., 'kron', 'twitter')
        
    Returns:
        dict with paths to time, log, and taskstats files
    """
    alg_dir = Path(base_dir) / algorithm
    
    # Pattern: alg-graph-*.ext
    pattern = f"{algorithm}-{graph}-*.*.stats"
    log_pattern = f"{algorithm}-{graph}-*.log"
    
    # Find files
    time_files = list((alg_dir / 'time').glob(f"{algorithm}-{graph}-*.time.stats"))
    log_files = list((alg_dir / 'log').glob(f"{algorithm}-{graph}-*.log"))
    taskstats_files = list((alg_dir / 'taskstats').glob(f"{algorithm}-{graph}-*.taskstats.stats"))
    
    if not time_files or not log_files or not taskstats_files:
        raise FileNotFoundError(
            f"Could not find all required files for {algorithm}-{graph}. "
            f"Found: {len(time_files)} time files, {len(log_files)} log files, "
            f"{len(taskstats_files)} taskstats files"
        )
    
    # Assuming one file per algorithm-graph combination
    return {
        'time': time_files[0],
        'log': log_files[0],
        'taskstats': taskstats_files[0]
    }


def gather_statistics(base_dir, algorithm, graph):
    """
    Gather all statistics for a given algorithm and graph.
    
    Args:
        base_dir: Base directory containing results
        algorithm: Algorithm name
        graph: Graph name
        
    Returns:
        dict with all gathered statistics (all times in seconds with 2 decimal places)
    """
    files = find_result_files(base_dir, algorithm, graph)
    
    stats = {
        'algorithm': algorithm,
        'graph': graph,
    }
    
    # Parse time stats (already in seconds)
    time_stats = parse_time_stats(files['time'])
    stats.update(time_stats)
    
    # Parse log file histograms (in nanoseconds, convert to seconds)
    log_stats = parse_log_file(files['log'])
    stats['total_maj'] = round(log_stats['total_maj'] / 1e9, 2)
    stats['total_maj_rec'] = round(log_stats['total_maj_rec'] / 1e9, 2)
    stats['total_min'] = round(log_stats['total_min'] / 1e9, 2)
    stats['sleep'] = round(log_stats['sleep'] / 1e9, 2)
    stats['reclaim'] = round(log_stats['reclaim'] / 1e9, 2)
    stats['readahead'] = round(log_stats['readahead'] / 1e9, 2)
    stats['sleep_pg_allocation'] = round(log_stats['sleep_pg_allocation'] / 1e9, 2)
    
    # Parse taskstats (in nanoseconds, convert to seconds)
    taskstats = parse_taskstats_file(files['taskstats'])
    irq_delay_seconds = taskstats['irq_delay'] / 1e9
    stats['irq_delay'] = round(irq_delay_seconds, 2)
    
    return stats


def write_to_csv(stats, output_file, append=False):
    """
    Write statistics to CSV file.
    
    Args:
        stats: Dictionary of statistics
        output_file: Path to output CSV file
        append: If True, append to existing file; if False, create new file
    """
    fieldnames = [
        'algorithm', 'graph',
        'user_time', 'system_time', 'idle_time', 'elapsed_time',
        'total_maj', 'total_maj_rec', 'total_min', 'sleep', 'reclaim', 'readahead',
        'sleep_pg_allocation', 'irq_delay'
    ]
    
    mode = 'a' if append and os.path.exists(output_file) else 'w'
    file_exists = os.path.exists(output_file) and append
    
    with open(output_file, mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(stats)


def main():
    parser = argparse.ArgumentParser(
        description='Parse benchmark statistics and generate CSV output'
    )
    parser.add_argument(
        'algorithm',
        help='Algorithm name (e.g., bc, bfs, cc, pr, sssp, tc)'
    )
    parser.add_argument(
        'graph',
        help='Graph name (e.g., kron, twitter, web, urand, road)'
    )
    parser.add_argument(
        '--base-dir',
        default=None,
        help='Base directory containing results (default: root/results/normal)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output CSV file (default: parsed_data/stats.csv)'
    )
    parser.add_argument(
        '--append',
        action='store_true',
        help='Append to existing CSV file instead of overwriting'
    )
    
    args = parser.parse_args()
    
    # Determine base directory
    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        # Default to normal dataset under root/results.
        base_dir = Path(__file__).resolve().parents[2] / 'results' / 'normal'
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path(__file__).resolve().parents[2] / 'outputs' / 'parsed' / 'breakdowns' / 'stats.csv'
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing {args.algorithm}-{args.graph}...")
    print(f"Base directory: {base_dir}")
    
    try:
        # Gather statistics
        stats = gather_statistics(base_dir, args.algorithm, args.graph)
        
        # Write to CSV
        write_to_csv(stats, output_file, append=args.append)
        
        print(f"Statistics written to: {output_file}")
        print("\nSummary:")
        print(f"  User time: {stats['user_time']:.2f} s")
        print(f"  System time: {stats['system_time']:.2f} s")
        print(f"  Total major: {stats['total_maj']:.2f} s")
        print(f"  Total major rec: {stats['total_maj_rec']:.2f} s")
        print(f"  Total minor: {stats['total_min']:.2f} s")
        print(f"  Sleep: {stats['sleep']:.2f} s")
        print(f"  Reclaim: {stats['reclaim']:.2f} s")
        print(f"  Readahead: {stats['readahead']:.2f} s")
        print(f"  Sleep pg allocation: {stats['sleep_pg_allocation']:.2f} s")
        print(f"  IRQ Delay: {stats['irq_delay']:.2f} s")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
