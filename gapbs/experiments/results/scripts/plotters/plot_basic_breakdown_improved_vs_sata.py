#!/usr/bin/env python3
"""
Plot basic time breakdown comparing Improved-NVMe (results/improved) vs SATA.

Creates a 2x3 figure showing 100%-stacked bars for each algorithm and graph.
For each graph, two identically-colored bars are placed side by side
(left = Improved NVMe, right = SATA) with a thin gap between them and a
wider gap between graph groups.  Colors are identical so the pair reads as
one visual unit; the caption explains which bar is which.
"""

import csv
import io
from contextlib import redirect_stdout
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuration
ALGORITHMS = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
GRAPHS = ['road', 'web', 'twitter', 'kron', 'urand']
GRAPH_NAMES = {'kron': 'K', 'road': 'R', 'twitter': 'T', 'urand': 'U', 'web': 'W'}

# Color scheme – same as plot_basic_breakdown.py (identical for both datasets)
COLORS = {
    'user':   '#D4C5B9',   # Warm beige
    'system': '#4A90E2',   # Sky blue
    'idle':   '#E8E8E8',   # Very light gray
}

NUM_CORES = 16   # number of CPU cores used to normalise time


def load_breakdown_data(base_dir):
    """Load all breakdown CSV files from base_dir."""
    data = {}
    for alg in ALGORITHMS:
        csv_file = base_dir / f"{alg}_breakdown.csv"
        if csv_file.exists():
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = []
                for row in reader:
                    for key in row:
                        if key not in ('algorithm', 'graph'):
                            row[key] = float(row[key])
                    rows.append(row)
            data[alg] = rows
        else:
            print(f"Warning: {csv_file} not found")
    return data


def percentages_for_graph(rows, graph):
    """
    Return {'user', 'system', 'idle'} as percentages (summing to ~100)
    for the given graph row, or all-zero if data is missing.
    """
    row = None
    for r in rows:
        if r['graph'] == graph:
            row = r
            break

    if row is None:
        return {'user': 0.0, 'system': 0.0, 'idle': 0.0}

    total = row['elapsed_time'] * NUM_CORES
    if total == 0:
        return {'user': 0.0, 'system': 0.0, 'idle': 0.0}

    user   = row['user_time']
    system = row['system_time'] + row['irq_delay']
    idle   = row['idle_time']   - row['irq_delay']

    return {
        'user':   100.0 * user   / total,
        'system': 100.0 * system / total,
        'idle':   100.0 * idle   / total,
    }


def draw_stacked_bar(ax, x, bar_width, pcts):
    """Draw a single 100%-stacked bar at position x."""
    bottom = 0.0
    for category in ('user', 'system', 'idle'):
        height = pcts[category]
        ax.bar(x, height, width=bar_width, bottom=bottom,
               color=COLORS[category], linewidth=0, edgecolor='none')
        bottom += height


def plot_stacked_bar(ax, improved_rows, sata_rows, algorithm, plot_idx):
    """
    Draw 10 stacked bars (5 Improved-NVMe + 5 SATA) for the algorithm on ax.

    Both bars in a pair use identical colors.  A thin intra-pair gap separates
    them; a wider inter-pair gap separates graph groups.  The caption should
    indicate that the left bar of each pair is Improved NVMe and the right is SATA.
    """
    n_graphs  = len(GRAPHS)
    bar_width = 0.35   # width of each individual bar
    intra_gap = 0.04   # tiny gap between the two bars of a pair

    x_centres  = np.arange(n_graphs, dtype=float)
    x_improved = x_centres - (bar_width + intra_gap) / 2
    x_sata     = x_centres + (bar_width + intra_gap) / 2

    for i, graph in enumerate(GRAPHS):
        improved_pcts = percentages_for_graph(improved_rows, graph)
        sata_pcts     = percentages_for_graph(sata_rows, graph)

        draw_stacked_bar(ax, x_improved[i], bar_width, improved_pcts)
        draw_stacked_bar(ax, x_sata[i],     bar_width, sata_pcts)

    # Axes decoration
    ax.set_title(algorithm.upper(), fontsize=10, fontweight='bold')
    ax.set_xticks(x_centres)
    ax.set_xticklabels([GRAPH_NAMES[g] for g in GRAPHS], rotation=0, fontsize=8)
    ax.set_xlim(-0.6, n_graphs - 0.4)
    ax.set_ylim(0, 100)

    if plot_idx % 3 == 0:   # left column only
        ax.set_ylabel('Time (%)', fontsize=9)

    ax.tick_params(axis='y', labelsize=8)
    ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)


def create_comparison_plot(improved_data, sata_data, output_file):
    """
    Create and save the full 2x3 Improved-NVMe-vs-SATA comparison figure.

    Args:
        improved_data: dict mapping algorithm to list of row dicts (Improved NVMe)
        sata_data:     dict mapping algorithm to list of row dicts (SATA)
        output_file:   Path to save the figure
    """
    fig, axes = plt.subplots(2, 3, figsize=(7, 5.5))
    axes = axes.flatten()

    for idx, alg in enumerate(ALGORITHMS):
        improved_rows = improved_data.get(alg, [])
        sata_rows     = sata_data.get(alg, [])

        if improved_rows or sata_rows:
            plot_stacked_bar(axes[idx], improved_rows, sata_rows, alg, idx)
        else:
            axes[idx].text(0.5, 0.5, f'No data for {alg}',
                           ha='center', va='center',
                           transform=axes[idx].transAxes, fontsize=9)
            axes[idx].set_title(alg.upper(), fontsize=10, fontweight='bold')

    # Legend: categories only (Improved vs SATA explained in caption)
    handles, labels = axes[0].get_legend_handles_labels()
    labels = ['User', 'Kernel', 'Idle']
    fig.legend(handles[:3], labels, loc='upper center', bbox_to_anchor=(0.5, 0.99),
               ncol=3, frameon=True, fontsize=9,
               edgecolor='black', fancybox=False)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")
    plt.close()


def print_averages(improved_data, sata_data):
    """
    Print average User, System, and Idle percentages for Improved-NVMe and SATA,
    broken down per algorithm and then as a grand average across all algorithms.
    """
    all_improved = {'user': [], 'system': [], 'idle': []}
    all_sata     = {'user': [], 'system': [], 'idle': []}

    header = (f"{'':8s} {'Dataset':8s}  {'User%':>7s}  {'System%':>8s}  {'Idle%':>7s}")
    print()
    print("=" * len(header))
    print("Average time breakdown: Improved-NVMe vs SATA")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for alg in ALGORITHMS:
        improved_rows = improved_data.get(alg, [])
        sata_rows     = sata_data.get(alg, [])

        for tag, rows, bucket in (('Improved', improved_rows, all_improved),
                                   ('SATA',     sata_rows,     all_sata)):
            pcts_list = [percentages_for_graph(rows, g) for g in GRAPHS
                         if any(r['graph'] == g for r in rows)]
            if not pcts_list:
                print(f"  {alg.upper():6s}  {tag:8s}   (no data)")
                continue
            avg_user   = sum(p['user']   for p in pcts_list) / len(pcts_list)
            avg_system = sum(p['system'] for p in pcts_list) / len(pcts_list)
            avg_idle   = sum(p['idle']   for p in pcts_list) / len(pcts_list)
            bucket['user'].append(avg_user)
            bucket['system'].append(avg_system)
            bucket['idle'].append(avg_idle)
            print(f"  {alg.upper():6s}  {tag:8s}  {avg_user:7.2f}%  {avg_system:8.2f}%  {avg_idle:7.2f}%")

        print()

    def gavg(lst):
        return sum(lst) / len(lst) if lst else 0.0

    print("-" * len(header))
    print(f"  {'GRAND':6s}  {'Improved':8s}  {gavg(all_improved['user']):7.2f}%  "
          f"{gavg(all_improved['system']):8.2f}%  {gavg(all_improved['idle']):7.2f}%")
    print(f"  {'GRAND':6s}  {'SATA':8s}  {gavg(all_sata['user']):7.2f}%  "
          f"{gavg(all_sata['system']):8.2f}%  {gavg(all_sata['idle']):7.2f}%")
    print("=" * len(header))
    print()


def main():
    script_dir = Path(__file__).parent
    root_dir   = script_dir.parent.parent

    improved_dir = root_dir / 'outputs' / 'parsed' / 'breakdowns_improved'
    sata_dir     = root_dir / 'outputs' / 'parsed' / 'breakdowns_sata'
    out_dir      = root_dir / 'outputs' / 'figures'
    report_dir   = root_dir / 'outputs' / 'reports'
    out_file     = out_dir  / 'breakdown-nvme_vs_sata.pdf'
    report_file  = report_dir / 'nvme-vs-sata.txt'

    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    print("Loading Improved-NVMe breakdown data...")
    improved_data = load_breakdown_data(improved_dir)
    print(f"  Loaded {len(improved_data)} algorithms from results/improved dataset")

    print("Loading SATA breakdown data...")
    sata_data = load_breakdown_data(sata_dir)
    print(f"  Loaded {len(sata_data)} algorithms from SATA dataset")

    if not improved_data and not sata_data:
        print("Error: No data files found!")
        return 1

    # Capture the formatted table produced by print_averages into a report file.
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_averages(improved_data, sata_data)
    averages_output = buffer.getvalue()

    # Keep current console behavior while also writing a text artifact.
    print(averages_output, end='')
    report_file.write_text(averages_output)
    print(f"Saved summary report to: {report_file}")

    print("Creating Improved-NVMe vs SATA comparison plot...")
    create_comparison_plot(improved_data, sata_data, out_file)

    print("Done!")
    return 0


if __name__ == '__main__':
    exit(main())
