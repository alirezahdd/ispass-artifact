#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TS_KEYS = [f"ts{i}" for i in [2, 3, 4, 5, 6, 7, 8, 9]]
TS_LABELS = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]


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

def compute_avg(ts_dict):
    """Compute average for each timestamp."""
    stats = {}
    for ts_name, values in ts_dict.items():
        if values:
            stats[ts_name] = np.mean(values)
        else:
            stats[ts_name] = 0
    return stats

def plot_timestamp_breakdown(results_dir="../results", output_pdf="../figures/timestamp_breakdown.pdf"):
    """
    Plot 100% stacked bar chart showing S1-S8 breakdown for each benchmark and fault type.
    9 groups (3 benchmarks × 3 fault types) with normalized stacked bars.
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
                "minor": compute_avg(minor),
                "no_reclaim": compute_avg(major_no_rec),
                "with_reclaim": compute_avg(major_with_rec),
            }
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue

    if not all_data:
        raise RuntimeError("No valid input data found for timestamp breakdown plot.")
    
    # Create figure
    _, ax = plt.subplots(figsize=(3.5, 2.5))

    # Professional color scheme for timestamps (ColorBrewer Set2/Set3 mix)
    ts_colors = [
        "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3",
        "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3",
    ]

    bench_names = [name for name, _ in benchmarks if name in all_data]
    fault_types = ["minor", "no_reclaim", "with_reclaim"]

    num_bars = len(bench_names) * len(fault_types)
    x_pos = np.arange(num_bars)
    width = 0.8

    # Collect data for all bars
    bar_data = []

    for bench_name in bench_names:
        for fault_type in fault_types:
            values = [all_data[bench_name][fault_type][ts] for ts in TS_KEYS]
            total = sum(values)

            if total > 0:
                percentages = [(v / total) * 100 for v in values]
            else:
                percentages = [0] * len(values)

            bar_data.append(percentages)

    # Plot stacked bars
    bottoms = [0] * num_bars

    for i, _ in enumerate(TS_KEYS):
        ts_data = [bar_data[j][i] for j in range(num_bars)]

        ax.bar(
            x_pos,
            ts_data,
            width,
            bottom=bottoms,
            label=TS_LABELS[i],
            color=ts_colors[i],
            edgecolor="white",
            linewidth=0.5,
        )

        bottoms = [bottoms[j] + ts_data[j] for j in range(num_bars)]

    # Formatting
    ax.set_ylabel("Percentage (%)", fontsize=8)
    ax.set_ylim(0, 100)

    x_labels = []
    for _ in bench_names:
        x_labels.extend(["min", "mj", "mj-rec"])

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=6, rotation=45, ha="right")

    # Add vertical lines to separate benchmarks
    for i in range(1, len(bench_names)):
        ax.axvline(x=i * 3 - 0.5, color="gray", linestyle="--", linewidth=0.9, alpha=0.9)

    # Add benchmark group annotations at the bottom
    for i, bench_name in enumerate(bench_names):
        group_center = i * 3 + 1
        ax.text(
            group_center,
            1.1,
            bench_name,
            ha="center",
            va="top",
            fontsize=7,
            weight="bold",
            transform=ax.get_xaxis_transform(),
        )

    ax.legend(fontsize=6, loc="upper center", frameon=True, ncol=1, bbox_to_anchor=(1.1, 1))
    ax.grid(True, alpha=0.3, axis="y")
    ax.tick_params(labelsize=7)

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])

    output_path = Path(output_pdf)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Plot saved to {output_pdf}")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate timestamp breakdown stacked bars")
    parser.add_argument("--results-dir", default="../results")
    parser.add_argument("--output", default="../figures/fig_5.pdf")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    plot_timestamp_breakdown(args.results_dir, args.output)
