#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TS_KEYS = [f"ts{i}" for i in [2, 3, 4, 5, 6, 7, 8, 9]]


def parse_int(row, key):
    try:
        return int(row[key])
    except (KeyError, ValueError):
        return 0

def read_and_categorize_timestamps(filename):
    """Read CSV file and categorize timestamps by fault type."""
    minor_ts = {k: [] for k in TS_KEYS}
    major_no_reclaim_ts = {k: [] for k in TS_KEYS}
    major_with_reclaim_ts = {k: [] for k in TS_KEYS}

    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            is_major = parse_int(row, "mj_fault") > 0
            is_minor = parse_int(row, "min_fault") > 0 and not is_major
            has_reclaim = parse_int(row, "reclaim") > 0

            if is_minor:
                ts_values = {
                    "ts2": parse_int(row, "ts2") / 1000.0,
                    "ts3": parse_int(row, "ts3") / 1000.0,
                    "ts4": parse_int(row, "ts6") / 1000.0,
                    "ts5": parse_int(row, "ts5") / 1000.0,
                    "ts6": 0.0,
                    "ts7": parse_int(row, "ts7") / 1000.0,
                    "ts8": parse_int(row, "ts8") / 1000.0,
                    "ts9": parse_int(row, "ts9") / 1000.0,
                }
            else:
                ts_values = {k: parse_int(row, k) / 1000.0 for k in TS_KEYS}

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

def plot_timestamp_comparison(results_dir="../results", output_pdf="../figures/timestamp_comparison.pdf"):
    """
    Plot timestamp statistics with two subplots:
    1. Combined ts2,ts3,ts6,ts8,ts9 (similar across benchmarks)
    2. ts5,ts7 comparison (differs across benchmarks)
    """
    
    results_dir = Path(results_dir)
    benchmarks = [
        ("seq", results_dir / "seq_merged.csv"),
        ("rnd", results_dir / "rnd_merged.csv"),
        ("seq_8page", results_dir / "seq_8page_merged.csv"),
    ]

    # Read all data
    all_data = {}
    for bench_name, csv_file in benchmarks:
        try:
            minor, major_no_rec, major_with_rec = read_and_categorize_timestamps(csv_file)
            all_data[bench_name] = {
                'minor': compute_stats(minor),
                'no_reclaim': compute_stats(major_no_rec),
                'with_reclaim': compute_stats(major_with_rec)
            }
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue

    if not all_data:
        raise RuntimeError("No valid input data found for timestamp comparison plot.")
    
    # Create figure with 2 subplots
    _, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.5, 4))
    # Subplot 1: Combined ts2,ts3,ts4,ts6,ts8,ts9 (use averaged data from all benchmarks)
    common_ts = ['ts2', 'ts3', 'ts4', 'ts6', 'ts8', 'ts9']
    x_pos1 = np.arange(len(common_ts))
    width = 0.25
    
    # Average across all benchmarks for common timestamps
    combined_minor = {ts: [] for ts in common_ts}
    combined_no_rec = {ts: [] for ts in common_ts}
    combined_with_rec = {ts: [] for ts in common_ts}
    
    for bench_name in [name for name, _ in benchmarks]:
        if bench_name in all_data:
            for ts in common_ts:
                if all_data[bench_name]['minor'][ts]['avg'] > 0:
                    combined_minor[ts].append(all_data[bench_name]['minor'][ts]['avg'])
                if all_data[bench_name]['no_reclaim'][ts]['avg'] > 0:
                    combined_no_rec[ts].append(all_data[bench_name]['no_reclaim'][ts]['avg'])
                if all_data[bench_name]['with_reclaim'][ts]['avg'] > 0:
                    combined_with_rec[ts].append(all_data[bench_name]['with_reclaim'][ts]['avg'])
    
    minor_avg = [np.mean(combined_minor[ts]) if combined_minor[ts] else 0 for ts in common_ts]
    minor_min = [np.min(combined_minor[ts]) if combined_minor[ts] else 0 for ts in common_ts]
    minor_max = [np.max(combined_minor[ts]) if combined_minor[ts] else 0 for ts in common_ts]
    
    no_rec_avg = [np.mean(combined_no_rec[ts]) if combined_no_rec[ts] else 0 for ts in common_ts]
    no_rec_min = [np.min(combined_no_rec[ts]) if combined_no_rec[ts] else 0 for ts in common_ts]
    no_rec_max = [np.max(combined_no_rec[ts]) if combined_no_rec[ts] else 0 for ts in common_ts]
    
    with_rec_avg = [np.mean(combined_with_rec[ts]) if combined_with_rec[ts] else 0 for ts in common_ts]
    with_rec_min = [np.min(combined_with_rec[ts]) if combined_with_rec[ts] else 0 for ts in common_ts]
    with_rec_max = [np.max(combined_with_rec[ts]) if combined_with_rec[ts] else 0 for ts in common_ts]
    
    ax1.bar(x_pos1 - width, minor_avg, width, label='Minor',
           color='#2E86AB', edgecolor='none')
    ax1.errorbar(x_pos1 - width, minor_avg,
                yerr=[np.array(minor_avg) - np.array(minor_min),
                      np.array(minor_max) - np.array(minor_avg)],
                fmt='none', ecolor='black', capsize=2, linewidth=0.8, alpha=0.5)
    
    ax1.bar(x_pos1, no_rec_avg, width, label='Major (no reclaim)',
           color='#A23B72', edgecolor='none')
    ax1.errorbar(x_pos1, no_rec_avg,
                yerr=[np.array(no_rec_avg) - np.array(no_rec_min),
                      np.array(no_rec_max) - np.array(no_rec_avg)],
                fmt='none', ecolor='black', capsize=2, linewidth=0.8, alpha=0.5)
    
    ax1.bar(x_pos1 + width, with_rec_avg, width, label='Major (with reclaim)',
           color='#F18F01', edgecolor='none')
    ax1.errorbar(x_pos1 + width, with_rec_avg,
                yerr=[np.array(with_rec_avg) - np.array(with_rec_min),
                      np.array(with_rec_max) - np.array(with_rec_avg)],
                fmt='none', ecolor='black', capsize=2, linewidth=0.8, alpha=0.5)
    
    # Add red X marker for empty bars in top plot (ts6/S5 is at index 3)
    ts6_idx = 3  # ts6 is at index 3 in common_ts list ['ts2', 'ts3', 'ts4', 'ts6', 'ts8', 'ts9']
    if minor_avg[ts6_idx] < 0.01:
        ax1.plot(x_pos1[ts6_idx] - width, 0.5, 'rx', markersize=6, 
                markeredgewidth=1.2, zorder=10)
    if no_rec_avg[ts6_idx] < 0.01:
        ax1.plot(x_pos1[ts6_idx], 0.5, 'rx', markersize=6, 
                markeredgewidth=1.2, zorder=10)
    if with_rec_avg[ts6_idx] < 0.01:
        ax1.plot(x_pos1[ts6_idx] + width, 0.5, 'rx', markersize=6, 
                markeredgewidth=1.2, zorder=10)
    
    ax1.set_ylabel('Time (μs)', fontsize=8)
    # ax1.set_xlabel('Timestamp', fontsize=8)
    ax1.set_title('Stage-wise Page Fault Handling \nLatency Across Microbenchmarks', fontsize=9, weight='bold')
    ax1.legend(fontsize=7, loc='best', frameon=True)
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.tick_params(labelsize=7)
    ax1.set_yscale('log')
    ax1.set_xticks(x_pos1)
    common_ts_meanings = ['S1', 'S2', 'S3', 'S5', 'S7', 'S8']
    ax1.set_xticklabels(common_ts_meanings, fontsize=7, fontweight='bold')
    
    # Subplot 2: ts5,ts7 comparison across benchmarks (3 groups)
    diff_ts = ['ts5', 'ts7']
    diff_ts_meanings = ['S4','S6']
    bench_names = ['seq', 'rnd', 'seq_8page']
    fault_types = ['minor', 'no_reclaim', 'with_reclaim']
    fault_colors = {'minor': '#2E86AB', 'no_reclaim': '#A23B72', 'with_reclaim': '#F18F01'}
    fault_labels = {'minor': 'Minor', 'no_reclaim': 'Major (no reclaim)', 'with_reclaim': 'Major (with reclaim)'}
    
    # Create 2 groups (ts5 and ts7), each with 3 benchmarks × 3 fault types
    num_groups = len(diff_ts)
    x_pos2 = np.arange(num_groups) * 2.5  # Closer groups
    width2 = 0.18  # Thicker bars
    bench_spacing = 0.15  # Small gap between benchmarks
    
    for i, bench_name in enumerate(bench_names):
        if bench_name not in all_data:
            continue
            
        for j, fault_type in enumerate(fault_types):
            avg_vals = []
            min_vals = []
            max_vals = []
            
            for ts in diff_ts:
                avg_vals.append(all_data[bench_name][fault_type][ts]['avg'])
                min_vals.append(all_data[bench_name][fault_type][ts]['min'])
                max_vals.append(all_data[bench_name][fault_type][ts]['max'])
            
            # Position: each group (ts5, ts7) has 9 bars (3 benchmarks × 3 fault types)
            # Add spacing between benchmark groups
            offset = (i * (3 + bench_spacing) + j - 4.5) * width2
            
            ax2.bar(x_pos2 + offset, avg_vals, width2,
                   color=fault_colors[fault_type], edgecolor='none', alpha=0.9)
            ax2.errorbar(x_pos2 + offset, avg_vals,
                        yerr=[np.array(avg_vals) - np.array(min_vals),
                              np.array(max_vals) - np.array(avg_vals)],
                        fmt='none', ecolor='black', capsize=2, linewidth=0.8, alpha=0.5)
            
            # Add red X marker for empty bars (zero or very small values)
            for k, val in enumerate(avg_vals):
                if val < 0.01:  # Threshold for "empty" bars
                    ax2.plot(x_pos2[k] + offset, 0.5, 'rx', markersize=6, 
                            markeredgewidth=1.2, zorder=10)
    
    ax2.set_ylabel('Time (μs)', fontsize=8)
    # ax2.set_xlabel('Timestamp', fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.tick_params(labelsize=7, pad=10)
    ax2.set_title('Latency Distributions of Stages S4 and S6', fontsize=9, weight='bold')
    ax2.set_yscale('log')
    ax2.set_xticks(x_pos2)
    ax2.set_xticklabels(diff_ts_meanings, fontsize=7, fontweight='bold')
    
    # Add legend to bottom plot
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2E86AB', edgecolor='none', label='Minor'),
        Patch(facecolor='#A23B72', edgecolor='none', label='Major (no reclaim)'),
        Patch(facecolor='#F18F01', edgecolor='none', label='Major (with reclaim)')
    ]
    ax2.legend(handles=legend_elements, fontsize=7, loc='upper right', frameon=True)
    
    # Add benchmark labels below each group of 3 bars
    # Calculate center position for each benchmark group
    bench_labels = ['seq', 'rnd', 'seq_8page']
    for i, label in enumerate(bench_labels):
        # Center of each benchmark's 3 bars
        center_offset = (i * (3 + bench_spacing) + 1 - 4.5) * width2
        for x_base in x_pos2:
            ax2.text(x_base + center_offset, -0.05, label, ha='center', va='top',
                    fontsize=6, rotation=30, transform=ax2.get_xaxis_transform())
    
    plt.tight_layout()
    
    # Save the plot
    output_path = Path(output_pdf)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight')
    print(f"Plot saved to {output_pdf}")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate timestamp comparison bar charts")
    parser.add_argument("--results-dir", default="../results")
    parser.add_argument("--output", default="../figures/fig_4.pdf")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    plot_timestamp_comparison(args.results_dir, args.output)
