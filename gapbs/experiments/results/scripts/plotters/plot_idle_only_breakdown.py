#!/usr/bin/env python3

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Professional color scheme for idle components
COLORS = {
    'idle_io': '#B85C3A',        # Brown/rust (darkest)
    'idle_pg_alloc': '#D4704A',  # Burnt orange (normal)
    'idle_other': '#E8927C',     # Light coral/orange (lightest)
}

# Graph names for display
GRAPH_NAMES = {
    'kron': 'K',
    'road': 'R',
    'twitter': 'T',
    'urand': 'U',
    'web': 'W'
}

# Algorithm names for display
ALGORITHM_NAMES = {
    'bc': 'BC',
    'bfs': 'BFS',
    'cc': 'CC',
    'pr': 'PR',
    'sssp': 'SSSP',
    'tc': 'TC'
}

def load_breakdown_data(algorithm):
    """Load breakdown data for a specific algorithm"""
    root_dir = Path(__file__).resolve().parents[2]
    csv_path = root_dir / 'outputs' / 'parsed' / 'breakdowns' / f'{algorithm}_breakdown.csv'
    
    data = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            graph = row['graph']
            data[graph] = {
                'idle_time': float(row['idle_time']),
                'sleep': float(row['sleep']),
                'sleep_pg_allocation': float(row['sleep_pg_allocation']),
                'irq_delay': float(row['irq_delay']),
            }
    
    return data

def calculate_idle_breakdown(data):
    """Calculate idle time breakdown as percentages of total idle time"""
    # Idle components
    idle_io_time = data['sleep']
    idle_pg_alloc_time = data['sleep_pg_allocation']
    idle_other_time = data['idle_time'] - data['irq_delay'] - data['sleep'] - data['sleep_pg_allocation']
    
    # Calculate total idle time for normalization
    total_idle = data['idle_time'] - data['irq_delay']
    
    # Convert to percentages of idle time
    breakdown = {
        'idle_io': (idle_io_time / total_idle) * 100 if total_idle > 0 else 0,
        'idle_pg_alloc': (idle_pg_alloc_time / total_idle) * 100 if total_idle > 0 else 0,
        'idle_other': (idle_other_time / total_idle) * 100 if total_idle > 0 else 0,
    }
    
    return breakdown

def create_idle_only_breakdown_plot():
    """Create 100% stacked bar chart showing only idle time breakdown"""
    algorithms = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
    graphs = ['road', 'web', 'twitter', 'kron', 'urand']
    
    # Load data for all algorithms
    print("Loading breakdown data...")
    all_data = {}
    for algorithm in algorithms:
        all_data[algorithm] = load_breakdown_data(algorithm)
    print(f"Loaded data for {len(all_data)} algorithms")
    
    # Create figure with 2x3 subplots
    print("Creating idle-only breakdown plot...")
    fig, axes = plt.subplots(2, 3, figsize=(7, 5.5))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.94, bottom=0.08, hspace=0.30, wspace=0.25)
    
    # Flatten axes for easier iteration
    axes_flat = axes.flatten()
    
    for idx, algorithm in enumerate(algorithms):
        ax = axes_flat[idx]
        data = all_data[algorithm]
        
        # Calculate breakdowns for each graph
        x_pos = np.arange(len(graphs))
        width = 0.6
        
        idle_io_pcts = []
        idle_pg_alloc_pcts = []
        idle_other_pcts = []
        
        for graph in graphs:
            breakdown = calculate_idle_breakdown(data[graph])
            idle_io_pcts.append(breakdown['idle_io'])
            idle_pg_alloc_pcts.append(breakdown['idle_pg_alloc'])
            idle_other_pcts.append(breakdown['idle_other'])
        
        # Create stacked bars
        p1 = ax.bar(x_pos, idle_io_pcts, width, 
                    color=COLORS['idle_io'])
        
        p2 = ax.bar(x_pos, idle_pg_alloc_pcts, width, bottom=idle_io_pcts,
                    color=COLORS['idle_pg_alloc'], hatch='///')
        
        bottom2 = np.array(idle_io_pcts) + np.array(idle_pg_alloc_pcts)
        p3 = ax.bar(x_pos, idle_other_pcts, width, bottom=bottom2,
                    color=COLORS['idle_other'])
        
        # Customize subplot
        # Only show y-axis label for left column (idx 0, 3 in 2x3 layout)
        if idx % 3 == 0:
            ax.set_ylabel('Idle Time (%)', fontsize=9)
        ax.set_title(ALGORITHM_NAMES[algorithm], fontsize=10, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels([GRAPH_NAMES[g] for g in graphs], rotation=0, fontsize=8)
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis='y', labelsize=8)
    
    # Create legend at the top
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['idle_io'], label='Idle: IO (S6)'),
        mpatches.Patch(facecolor=COLORS['idle_pg_alloc'], hatch='///', label='Idle: Swap-race (S4)'),
        mpatches.Patch(facecolor=COLORS['idle_other'], label='Idle: Other'),
    ]
    
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.99),
               ncol=3, frameon=True, fontsize=9,
               edgecolor='black', fancybox=False)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save figure
    output_path = Path(__file__).resolve().parents[2] / 'outputs' / 'figures' / 'fig_8.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    print("Done!")

if __name__ == '__main__':
    create_idle_only_breakdown_plot()
