#!/usr/bin/env python3
"""
Plot basic time breakdown showing only User, System, and Idle time.

Creates a 3x2 figure showing 100%-stacked bars for each algorithm and graph,
with three major categories: User, System (adjusted), and Idle (adjusted).
"""

import csv
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuration
ALGORITHMS = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
GRAPHS = ['road', 'web', 'twitter', 'kron', 'urand']
GRAPH_NAMES = {'kron': 'K', 'road': 'R', 'twitter': 'T', 'urand': 'U', 'web': 'W'}

# Professional color scheme - subdued and clear
COLORS = {
    'user': '#D4C5B9',      # Beige/tan (subdued, less important but distinct)
    'system': '#4A90E2',    # Professional blue
    'idle': '#E8E8E8',      # Very light gray
}

# Edge colors for visual separation
EDGE_COLORS = {
    'user': '#A89984',
    'system': '#2E5F8E',
    'idle': '#AAAAAA',
}


def load_breakdown_data(base_dir):
    """Load all breakdown CSV files."""
    data = {}
    for alg in ALGORITHMS:
        csv_file = base_dir / f"{alg}_breakdown.csv"
        if csv_file.exists():
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = []
                for row in reader:
                    for key in row:
                        if key not in ['algorithm', 'graph']:
                            row[key] = float(row[key])
                    rows.append(row)
                data[alg] = rows
        else:
            print(f"Warning: {csv_file} not found")
    return data


def plot_stacked_bar(ax, data_rows, algorithm):
    """
    Plot a 100%-stacked bar chart with User, System, and Idle time.
    
    Args:
        ax: Matplotlib axis
        data_rows: List of dicts with data for this algorithm
        algorithm: Algorithm name
    """
    x_pos = np.arange(len(GRAPHS))
    bar_width = 0.7
    
    # Storage for percentages
    percentages = {'user': [], 'system': [], 'idle': []}
    
    # Calculate percentages for each graph
    for graph in GRAPHS:
        # Find the row for this graph
        row = None
        for r in data_rows:
            if r['graph'] == graph:
                row = r
                break
        
        if row is None:
            # Missing data - fill with zeros
            for comp in percentages:
                percentages[comp].append(0)
            continue
        
        # Normalize by elapsed * 16 cores
        total_time = row['elapsed_time'] * 16
        
        # Calculate components
        user = row['user_time']
        # System time: add irq_delay
        system = row['system_time'] + row['irq_delay']
        # Idle time: subtract irq_delay
        idle = row['idle_time'] - row['irq_delay']
        
        # Calculate percentages
        percentages['user'].append(100 * user / total_time)
        percentages['system'].append(100 * system / total_time)
        percentages['idle'].append(100 * idle / total_time)
    
    # Stack the bars
    bottom = np.zeros(len(GRAPHS))
    
    # Plot User time
    ax.bar(x_pos, percentages['user'], bar_width, bottom=bottom,
           label='User', color=COLORS['user'])
    bottom += np.array(percentages['user'])
    
    # Plot System time
    ax.bar(x_pos, percentages['system'], bar_width, bottom=bottom,
           label='System', color=COLORS['system'])
    bottom += np.array(percentages['system'])
    
    # Plot Idle time
    ax.bar(x_pos, percentages['idle'], bar_width, bottom=bottom,
           label='Idle', color=COLORS['idle'])
    
    # Customize subplot
    # Only show y-axis label for left column (idx 0, 3 in 2x3 layout)
    if hasattr(ax, '_plot_idx') and ax._plot_idx % 3 == 0:
        ax.set_ylabel('Time (%)', fontsize=9)
    ax.set_title(algorithm.upper(), fontsize=10, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([GRAPH_NAMES[g] for g in GRAPHS], rotation=0, fontsize=8)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(axis='y', labelsize=8)
    
    # Add horizontal lines to separate major categories
    # if any(percentages['user']):
    #     user_height = np.array(percentages['user'])
    #     system_height = np.array(percentages['system'])
        
    #     # Line between user and system
    #     for i, (u, s) in enumerate(zip(user_height, system_height)):
    #         if u > 0:
    #             ax.plot([i - bar_width/2, i + bar_width/2], [u, u], 
    #                    'k-', linewidth=1.0, alpha=0.6)
    #         if s > 0:
    #             ax.plot([i - bar_width/2, i + bar_width/2], [u + s, u + s], 
    #                    'k-', linewidth=1.0, alpha=0.6)


def create_breakdown_plot(data, output_file):
    """
    Create the complete figure with all subplots.
    
    Args:
        data: dict mapping algorithm to list of row dicts
        output_file: Path to save the figure
    """
    # Create figure with size appropriate for single column in 2-column layout
    # Single column width is typically ~3.5 inches, we use slightly less
    fig, axes = plt.subplots(2, 3, figsize=(7, 5.5))
    axes = axes.flatten()
    
    for idx, alg in enumerate(ALGORITHMS):
        if alg in data:
            axes[idx]._plot_idx = idx
            plot_stacked_bar(axes[idx], data[alg], alg)
        else:
            axes[idx].text(0.5, 0.5, f'No data for {alg}',
                          ha='center', va='center', transform=axes[idx].transAxes,
                          fontsize=9)
            axes[idx].set_title(alg.upper(), fontsize=10, fontweight='bold')
    
    # Add legend at the top
    handles, labels = axes[0].get_legend_handles_labels()
    labels = ['User', 'System', 'Idle']
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.99),
               ncol=3, frameon=True, fontsize=9, 
               edgecolor='black', fancybox=False)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")
    
    plt.close()


def main():
    # Set up paths
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent
    data_dir = root_dir / 'outputs' / 'parsed' / 'breakdowns'
    output_dir = root_dir / 'outputs' / 'figures'
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Output file
    output_file = output_dir / 'fig_6.pdf'
    
    print("Loading breakdown data...")
    data = load_breakdown_data(data_dir)
    
    if not data:
        print("Error: No data files found!")
        return 1
    
    print(f"Loaded data for {len(data)} algorithms")
    
    print("Creating basic breakdown plot...")
    create_breakdown_plot(data, output_file)
    
    print("Done!")
    return 0


if __name__ == '__main__':
    exit(main())
