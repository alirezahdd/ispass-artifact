#!/usr/bin/env python3
import csv
import matplotlib.pyplot as plt
import numpy as np
import sys

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

def read_and_categorize_timestamps(filename):
    """Read CSV file and categorize timestamps by fault type."""
    minor_ts = {f'ts{i}': [] for i in [2, 3, 4, 5, 6, 7, 8, 9]}
    major_no_reclaim_ts = {f'ts{i}': [] for i in [2, 3, 4, 5, 6, 7, 8, 9]}
    major_with_reclaim_ts = {f'ts{i}': [] for i in [2, 3, 4, 5, 6, 7, 8, 9]}
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            is_major = int(row['mj_fault']) == 1
            is_minor = int(row['min_fault']) == 1
            has_reclaim = int(row['reclaim']) == 1
            
            # Get timestamp values (in nanoseconds, convert to microseconds)
            # For minor faults: use ts6 as ts4, and zero for ts6
            if is_minor:
                ts_values = {
                    'ts2': int(row['ts2']) / 1000.0,
                    'ts3': int(row['ts3']) / 1000.0,
                    'ts4': int(row['ts6']) / 1000.0,  # Use ts6 as ts4 for minor faults
                    'ts5': int(row['ts5']) / 1000.0,
                    'ts6': 0.0,  # Zero for ts6 in minor faults
                    'ts7': int(row['ts7']) / 1000.0,
                    'ts8': int(row['ts8']) / 1000.0,
                    'ts9': int(row['ts9']) / 1000.0,
                }
            else:
                ts_values = {
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

def compute_avg(ts_dict):
    """Compute average for each timestamp."""
    stats = {}
    for ts_name, values in ts_dict.items():
        if values:
            stats[ts_name] = np.mean(values)
        else:
            stats[ts_name] = 0
    return stats

def plot_timestamp_breakdown():
    """
    Plot 100% stacked bar chart showing S1-S8 breakdown for each benchmark and fault type.
    9 groups (3 benchmarks × 3 fault types) with normalized stacked bars.
    """
    
    results_dir = "../results"
    benchmarks = [
        ('seq', f"{results_dir}/seq_merged.csv"),
        ('rnd', f"{results_dir}/rnd_merged.csv"),
        ('seq_8page', f"{results_dir}/seq_8page_merged.csv")
    ]
    
    # Read all data
    all_data = {}
    for bench_name, csv_file in benchmarks:
        try:
            minor, major_no_rec, major_with_rec = read_and_categorize_timestamps(csv_file)
            all_data[bench_name] = {
                'minor': compute_avg(minor),
                'no_reclaim': compute_avg(major_no_rec),
                'with_reclaim': compute_avg(major_with_rec)
            }
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue
    
    # Create figure
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    
    # Define timestamps S1-S8 (ts2-ts9)
    timestamps = ['ts2', 'ts3', 'ts4', 'ts5', 'ts6', 'ts7', 'ts8', 'ts9']
    ts_labels = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8']
    
    # Standard Matplotlib palette with a cooler subset to avoid red-dominant stacks
    tab20 = plt.get_cmap('tab20').colors
    ts_colors = [tab20[i] for i in [0, 2, 4, 8, 14, 16, 18, 1]]
    # Use hatches sparingly for print readability without visual clutter
    ts_hatches = ['', '', '', '', '', '', '', '']
    
    bench_names = ['seq', 'rnd', 'seq_8page']
    fault_types = ['minor', 'no_reclaim', 'with_reclaim']
    fault_labels = ['Minor', 'Major\n(no reclaim)', 'Major\n(with reclaim)']
    
    # Prepare data: 9 bars (3 benchmarks × 3 fault types)
    num_bars = len(bench_names) * len(fault_types)
    x_pos = np.arange(num_bars)
    width = 0.8
    
    # Collect data for all bars
    bar_data = []
    bar_labels = []
    
    for bench_name in bench_names:
        if bench_name not in all_data:
            continue
        for fault_type in fault_types:
            # Get average values for each timestamp
            values = [all_data[bench_name][fault_type][ts] for ts in timestamps]
            total = sum(values)
            
            # Normalize to percentages
            if total > 0:
                percentages = [(v / total) * 100 for v in values]
            else:
                percentages = [0] * len(values)
            
            bar_data.append(percentages)
            bar_labels.append(f"{bench_name}")
    
    # Plot stacked bars
    bottoms = [0] * num_bars
    
    for i, ts in enumerate(timestamps):
        # Get data for this timestamp across all bars
        ts_data = [bar_data[j][i] for j in range(num_bars)]
        
        ax.bar(
            x_pos,
            ts_data,
            width,
            bottom=bottoms,
            label=ts_labels[i],
            color=ts_colors[i],
            edgecolor='black',
            linewidth=0.6,
            hatch=ts_hatches[i]
        )
        
        # Update bottoms for next layer
        bottoms = [bottoms[j] + ts_data[j] for j in range(num_bars)]
    
    # Formatting
    ax.set_ylabel('Percentage (%)', fontsize=8)
    ax.set_ylim(0, 100)
    # ax.set_title('Time Breakdown by Fault Type', fontsize=9, weight='bold')
    
    # X-axis labels: simplified approach
    # Create labels that combine benchmark and fault type
    x_labels = []
    for bench_name in bench_names:
        x_labels.extend([f'min', f'mj', f'mj-rec'])
        # x_labels.extend([f'{bench_name}\nminor', f'{bench_name}\nmajor', f'{bench_name}\nreclaim'])
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=6, rotation=45, ha='right')
    
    # Add vertical lines to separate benchmarks
    for i in range(1, len(bench_names)):
        ax.axvline(x=i*3 - 0.5, color='gray', linestyle='--', linewidth=0.9, alpha=0.9)
    
    # Add benchmark group annotations at the bottom
    for i, bench_name in enumerate(bench_names):
        group_center = i * 3 + 1  # Center of the 3 bars for this benchmark
        ax.text(group_center, 1.1, bench_name, ha='center', va='top', 
                fontsize=7, 
                # weight='bold', 
                transform=ax.get_xaxis_transform())
    
    ax.legend(fontsize=6, loc='upper center', frameon=True, ncol=1, bbox_to_anchor=(1.1, 1))
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(labelsize=7)
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # Add space at bottom and top for labels
    
    # Save the plot
    output_pdf = "../figures/fig_5.pdf"
    plt.savefig(output_pdf, bbox_inches='tight')
    print(f"Plot saved to {output_pdf}")

if __name__ == "__main__":
    plot_timestamp_breakdown()
