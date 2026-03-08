#!/usr/bin/env python3
import csv
import matplotlib.pyplot as plt
import numpy as np
import sys

def read_and_categorize_timestamps(filename):
    """Read CSV file and categorize timestamps by fault type."""
    minor_ts = {f'ts{i}': [] for i in [1, 2, 3, 4, 5, 6, 7, 8, 9]}
    major_no_reclaim_ts = {f'ts{i}': [] for i in [1, 2, 3, 4, 5, 6, 7, 8, 9]}
    major_with_reclaim_ts = {f'ts{i}': [] for i in [1, 2, 3, 4, 5, 6, 7, 8, 9]}
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            is_major = int(row['mj_fault']) == 1
            is_minor = int(row['min_fault']) == 1
            has_reclaim = int(row['reclaim']) == 1
            
            # Get timestamp values (in nanoseconds, convert to microseconds)
            ts_values = {
                'ts1': int(row['ts1']) / 1000.0,
                'ts2': int(row['ts2']) / 1000.0,
                'ts3': int(row['ts3']) / 1000.0,
                'ts4': int(row['ts4']) / 1000.0,
                'ts5': int(row['ts5']) / 1000.0,
                'ts6': int(row['ts6']) / 1000.0,
                'ts7': int(row['ts7']) / 1000.0,
                'ts8': int(row['ts8']) / 1000.0,
                'ts9': int(row['ts9']) / 1000.0,
            }
            
            # Categorize and store non-negative values
            if is_minor:
                for ts_name, val in ts_values.items():
                    if val > 0:
                        minor_ts[ts_name].append(val)
            elif is_major and has_reclaim:
                for ts_name, val in ts_values.items():
                    if val > 0:
                        major_with_reclaim_ts[ts_name].append(val)
            elif is_major:
                for ts_name, val in ts_values.items():
                    if val > 0:
                        major_no_reclaim_ts[ts_name].append(val)
    
    return minor_ts, major_no_reclaim_ts, major_with_reclaim_ts

def compute_stats(ts_dict):
    """Compute min, max, avg for each timestamp."""
    stats = {}
    for ts_name, values in ts_dict.items():
        if values:
            stats[ts_name] = {
                'min': np.min(values),
                'max': np.max(values),
                'avg': np.mean(values),
                'count': len(values)
            }
        else:
            stats[ts_name] = {'min': 0, 'max': 0, 'avg': 0, 'count': 0}
    return stats

def plot_timestamp_stats():
    """
    Plot min/max/avg statistics for timestamps, categorized by fault type.
    """
    
    # Read CSV files
    results_dir = "../results"
    
    # Create figure with 3 subplots (one for each benchmark)
    fig, axes = plt.subplots(3, 1, figsize=(3.5, 7), sharex=True)
    
    benchmarks = [
        ('seq', f"{results_dir}/seq_merged.csv", axes[0]),
        ('rnd', f"{results_dir}/rnd_merged.csv", axes[1]),
        ('seq_8page', f"{results_dir}/seq_8page_merged.csv", axes[2])
    ]
    ts_labels = ['ts2', 'ts3', 'ts4', 'ts5', 'ts6', 'ts7', 'ts8', 'ts9']
    x_pos = np.arange(len(ts_labels))
    width = 0.25  # Width of barsls))
    width = 0.25  # Width of bars
    
    for bench_name, csv_file, ax in benchmarks:
        try:
            minor, major_no_rec, major_with_rec = read_and_categorize_timestamps(csv_file)
            minor_stats = compute_stats(minor)
            major_no_rec_stats = compute_stats(major_no_rec)
            major_with_rec_stats = compute_stats(major_with_rec)
        except FileNotFoundError:
            print(f"Warning: {csv_file} not found, skipping...")
            continue
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue
        
        # Extract avg values for each category
        minor_avg = [minor_stats[ts]['avg'] for ts in ts_labels]
        minor_min = [minor_stats[ts]['min'] for ts in ts_labels]
        minor_max = [minor_stats[ts]['max'] for ts in ts_labels]
        
        major_no_rec_avg = [major_no_rec_stats[ts]['avg'] for ts in ts_labels]
        major_no_rec_min = [major_no_rec_stats[ts]['min'] for ts in ts_labels]
        major_no_rec_max = [major_no_rec_stats[ts]['max'] for ts in ts_labels]
        
        major_with_rec_avg = [major_with_rec_stats[ts]['avg'] for ts in ts_labels]
        major_with_rec_min = [major_with_rec_stats[ts]['min'] for ts in ts_labels]
        major_with_rec_max = [major_with_rec_stats[ts]['max'] for ts in ts_labels]
        
        # Plot bars with error bars showing min/max
        ax.bar(x_pos - width, minor_avg, width, label='Minor',
               color='#2E86AB', edgecolor='none')
        ax.errorbar(x_pos - width, minor_avg, 
                   yerr=[np.array(minor_avg) - np.array(minor_min), 
                         np.array(minor_max) - np.array(minor_avg)],
                   fmt='none', ecolor='black', capsize=3, linewidth=1, alpha=0.5)
        
        ax.bar(x_pos, major_no_rec_avg, width, label='Major (no reclaim)',
               color='#A23B72', edgecolor='none')
        ax.errorbar(x_pos, major_no_rec_avg,
                   yerr=[np.array(major_no_rec_avg) - np.array(major_no_rec_min),
                         np.array(major_no_rec_max) - np.array(major_no_rec_avg)],
                   fmt='none', ecolor='black', capsize=3, linewidth=1, alpha=0.5)
        
        ax.bar(x_pos + width, major_with_rec_avg, width, label='Major (with reclaim)',
               color='#F18F01', edgecolor='none')
        ax.errorbar(x_pos + width, major_with_rec_avg,
                   yerr=[np.array(major_with_rec_avg) - np.array(major_with_rec_min),
                         np.array(major_with_rec_max) - np.array(major_with_rec_avg)],
                   fmt='none', ecolor='black', capsize=3, linewidth=1, alpha=0.5)
        
        ax.set_ylabel('Time (μs)', fontsize=8)
        ax.set_title(f'{bench_name}', fontsize=9, weight='bold')
        ax.legend(fontsize=6, loc='upper left', frameon=True)
        ax.grid(True, alpha=0.3, axis='y')
        ax.tick_params(labelsize=7)
        ax.set_yscale('log')
    
    axes[-1].set_xlabel('Timestamp', fontsize=8)
    axes[-1].set_xticks(x_pos)
    axes[-1].set_xticklabels(ts_labels, fontsize=7)
    
    plt.tight_layout()
    
    # Save the plot
    output_pdf = "../figures/timestamp_stats.pdf"
    plt.savefig(output_pdf, bbox_inches='tight')
    print(f"Plot saved to {output_pdf}")

if __name__ == "__main__":
    plot_timestamp_stats()
