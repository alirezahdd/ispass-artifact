#!/usr/bin/env python3

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Professional color scheme - combining all components
COLORS = {
    'user': '#D4C5B9',           # Beige/tan
    'readahead': '#5BA3D0',      # Light blue
    'reclaim': '#4A90E2',        # Professional blue
    'irq_delay': '#3A6FA0',      # Medium blue
    'system_other': '#2E5F8E',   # Dark blue
    'idle_io': '#B85C3A',        # Brown/rust (darkest)
    'idle_pg_alloc': '#D4704A',  # Burnt orange (normal)
    'idle_other': '#E8927C',     # Light coral/orange (lightest)
}

# Edge colors for visual separation
EDGE_COLORS = {
    'user': '#A89984',
    'readahead': '#3D7FA8',
    'reclaim': '#2E5F8E',
    'irq_delay': '#254A6F',
    'system_other': '#1A3A5C',
    'idle_io': '#8A4428',
    'idle_pg_alloc': '#A85838',
    'idle_other': '#C5705A',
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
                'user_time': float(row['user_time']),
                'system_time': float(row['system_time']),
                'idle_time': float(row['idle_time']),
                'elapsed_time': float(row['elapsed_time']),
                'readahead': float(row['readahead']),
                'reclaim': float(row['reclaim']),
                'sleep': float(row['sleep']),
                'sleep_pg_allocation': float(row['sleep_pg_allocation']),
                'irq_delay': float(row['irq_delay']),
            }
    
    return data

def calculate_breakdown(data):
    """Calculate complete time breakdown percentages"""
    elapsed_normalized = data['elapsed_time'] * 16  # 16 cores
    
    # User
    user_time = data['user_time']
    
    # System components
    readahead_time = data['readahead'] - data['reclaim'] - data['sleep_pg_allocation']
    reclaim_time = data['reclaim']
    irq_delay_time = data['irq_delay']
    system_time = data['system_time'] + irq_delay_time
    system_other_time = system_time - readahead_time - reclaim_time - irq_delay_time
    
    # Idle components
    idle_io_time = data['sleep']
    idle_pg_alloc_time = data['sleep_pg_allocation']
    idle_other_time = data['idle_time'] - data['irq_delay'] - data['sleep'] - data['sleep_pg_allocation']
    
    # Convert to percentages
    breakdown = {
        'user': (user_time / elapsed_normalized) * 100,
        'readahead': (readahead_time / elapsed_normalized) * 100,
        'reclaim': (reclaim_time / elapsed_normalized) * 100,
        'irq_delay': (irq_delay_time / elapsed_normalized) * 100,
        'system_other': (system_other_time / elapsed_normalized) * 100,
        'idle_io': (idle_io_time / elapsed_normalized) * 100,
        'idle_pg_alloc': (idle_pg_alloc_time / elapsed_normalized) * 100,
        'idle_other': (idle_other_time / elapsed_normalized) * 100,
    }
    
    return breakdown

def create_complete_breakdown_plot():
    """Create complete breakdown plot with 3x2 layout"""
    algorithms = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
    graphs = ['road', 'web', 'twitter', 'kron', 'urand']
    
    # Load data for all algorithms
    print("Loading breakdown data...")
    all_data = {}
    for algorithm in algorithms:
        all_data[algorithm] = load_breakdown_data(algorithm)
    print(f"Loaded data for {len(all_data)} algorithms")
    
    # Create figure with 2x3 subplots
    print("Creating complete breakdown plot...")
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
        
        user_pcts = []
        readahead_pcts = []
        reclaim_pcts = []
        irq_delay_pcts = []
        system_other_pcts = []
        idle_io_pcts = []
        idle_pg_alloc_pcts = []
        idle_other_pcts = []
        
        for graph in graphs:
            breakdown = calculate_breakdown(data[graph])
            user_pcts.append(breakdown['user'])
            readahead_pcts.append(breakdown['readahead'])
            reclaim_pcts.append(breakdown['reclaim'])
            irq_delay_pcts.append(breakdown['irq_delay'])
            system_other_pcts.append(breakdown['system_other'])
            idle_io_pcts.append(breakdown['idle_io'])
            idle_pg_alloc_pcts.append(breakdown['idle_pg_alloc'])
            idle_other_pcts.append(breakdown['idle_other'])
        
        # Create stacked bars
        p1 = ax.bar(x_pos, user_pcts, width, 
                    color=COLORS['user'])
        
        bottom1 = np.array(user_pcts)
        p2 = ax.bar(x_pos, readahead_pcts, width, bottom=bottom1,
                    color=COLORS['readahead'])
        
        bottom2 = bottom1 + np.array(readahead_pcts)
        p3 = ax.bar(x_pos, reclaim_pcts, width, bottom=bottom2,
                    color=COLORS['reclaim'])
        
        bottom3 = bottom2 + np.array(reclaim_pcts)
        p4 = ax.bar(x_pos, irq_delay_pcts, width, bottom=bottom3,
                    color=COLORS['irq_delay'])
        
        bottom4 = bottom3 + np.array(irq_delay_pcts)
        p5 = ax.bar(x_pos, system_other_pcts, width, bottom=bottom4,
                    color=COLORS['system_other'])
        
        bottom5 = bottom4 + np.array(system_other_pcts)
        p6 = ax.bar(x_pos, idle_io_pcts, width, bottom=bottom5,
                    color=COLORS['idle_io'])
        
        bottom6 = bottom5 + np.array(idle_io_pcts)
        p7 = ax.bar(x_pos, idle_pg_alloc_pcts, width, bottom=bottom6,
                    color=COLORS['idle_pg_alloc'], hatch='///')
        
        bottom7 = bottom6 + np.array(idle_pg_alloc_pcts)
        p8 = ax.bar(x_pos, idle_other_pcts, width, bottom=bottom7,
                    color=COLORS['idle_other'])
        
        # Customize subplot
        # Only show y-axis label for left column (idx 0, 3 in 2x3 layout)
        if idx % 3 == 0:
            ax.set_ylabel('Time (%)', fontsize=9)
        ax.set_title(ALGORITHM_NAMES[algorithm], fontsize=10, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels([GRAPH_NAMES[g] for g in graphs], rotation=0, fontsize=8)
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis='y', labelsize=8)
    
    # Create legend at the top - split into two rows if needed
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['user'], label='User'),
        mpatches.Patch(facecolor=COLORS['readahead'], label='Readahead (S4)'),
        mpatches.Patch(facecolor=COLORS['reclaim'], label='Reclaim (S4)'),
        mpatches.Patch(facecolor=COLORS['irq_delay'], label='IRQ Delay'),
        mpatches.Patch(facecolor=COLORS['system_other'], label='System Other'),
        mpatches.Patch(facecolor=COLORS['idle_io'], label='Idle: IO (S6)'),
        mpatches.Patch(facecolor=COLORS['idle_pg_alloc'], hatch='///', label='Idle: Swap-race (S4)'),
        mpatches.Patch(facecolor=COLORS['idle_other'], label='Idle: Other'),
    ]
    
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.00),
               ncol=4, frameon=True, fontsize=8,
               edgecolor='black', fancybox=False)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save figure
    output_path = Path(__file__).resolve().parents[2] / 'outputs' / 'figures' / 'fig_9.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    print("Done!")

if __name__ == '__main__':
    create_complete_breakdown_plot()
