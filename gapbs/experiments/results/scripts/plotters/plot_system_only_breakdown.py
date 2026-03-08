#!/usr/bin/env python3

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Professional color scheme for system components
COLORS = {
    'readahead': '#5BA3D0',      # Light blue
    'reclaim': '#4A90E2',        # Professional blue
    'irq_delay': '#3A6FA0',      # Medium blue
    'system_other': "#204467",   # Dark blue
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
                'sleep_pg_allocation': float(row['sleep_pg_allocation']),
                'irq_delay': float(row['irq_delay']),
            }
    
    return data

def calculate_system_breakdown(data):
    """Calculate system time breakdown as percentages of total system time"""
    # System components
    readahead_time = data['readahead'] - data['reclaim'] - data['sleep_pg_allocation']
    reclaim_time = data['reclaim']
    irq_delay_time = data['irq_delay']
    system_time = data['system_time'] + irq_delay_time
    system_other_time = system_time - readahead_time - reclaim_time - irq_delay_time
    
    # Calculate total system time for normalization
    total_system = system_time
    
    # Convert to percentages of system time
    breakdown = {
        'readahead': (readahead_time / total_system) * 100 if total_system > 0 else 0,
        'reclaim': (reclaim_time / total_system) * 100 if total_system > 0 else 0,
        'irq_delay': (irq_delay_time / total_system) * 100 if total_system > 0 else 0,
        'system_other': (system_other_time / total_system) * 100 if total_system > 0 else 0,
    }
    
    return breakdown

def create_system_only_breakdown_plot():
    """Create 100% stacked bar chart showing only system time breakdown"""
    algorithms = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
    graphs = ['road', 'web', 'twitter', 'kron', 'urand']
    
    # Load data for all algorithms
    print("Loading breakdown data...")
    all_data = {}
    for algorithm in algorithms:
        all_data[algorithm] = load_breakdown_data(algorithm)
    print(f"Loaded data for {len(all_data)} algorithms")
    
    # Create figure with 2x3 subplots
    print("Creating system-only breakdown plot...")
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
        
        readahead_pcts = []
        reclaim_pcts = []
        irq_delay_pcts = []
        system_other_pcts = []
        
        for graph in graphs:
            breakdown = calculate_system_breakdown(data[graph])
            readahead_pcts.append(breakdown['readahead'])
            reclaim_pcts.append(breakdown['reclaim'])
            irq_delay_pcts.append(breakdown['irq_delay'])
            system_other_pcts.append(breakdown['system_other'])
        
        # Calculate average readahead percentage
        avg_readahead = np.mean(readahead_pcts)
        # Calculate average reclaim end point (readahead + reclaim)
        avg_reclaim_end = np.mean(np.array(readahead_pcts) + np.array(reclaim_pcts))
        
        # Create stacked bars
        p1 = ax.bar(x_pos, readahead_pcts, width, 
                    color=COLORS['readahead'])
        
        p2 = ax.bar(x_pos, reclaim_pcts, width, bottom=readahead_pcts,
                    color=COLORS['reclaim'])
        
        bottom2 = np.array(readahead_pcts) + np.array(reclaim_pcts)
        p3 = ax.bar(x_pos, irq_delay_pcts, width, bottom=bottom2,
                    color=COLORS['irq_delay'])
        
        bottom3 = bottom2 + np.array(irq_delay_pcts)
        p4 = ax.bar(x_pos, system_other_pcts, width, bottom=bottom3,
                    color=COLORS['system_other'])
        
        # Draw average readahead line
        ax.axhline(y=avg_readahead, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        
        # Annotate average readahead value
        ax.text(len(graphs) - 0.5, avg_readahead, f'{avg_readahead:.1f}%',
                fontsize=8, color='red', fontweight='bold',
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', alpha=0.8))
        
        # Draw average reclaim end point line
        ax.axhline(y=avg_reclaim_end, color='darkblue', linestyle='--', linewidth=1.5, alpha=0.7)
        
        # Annotate average reclaim end value
        ax.text(len(graphs) - 0.5, avg_reclaim_end, f'{avg_reclaim_end:.1f}%',
                fontsize=8, color='darkblue', fontweight='bold',
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='darkblue', alpha=0.8))
        
        # Customize subplot
        # Only show y-axis label for left column (idx 0, 3 in 2x3 layout)
        if idx % 3 == 0:
            ax.set_ylabel('System Time (%)', fontsize=9)
        ax.set_title(ALGORITHM_NAMES[algorithm], fontsize=10, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels([GRAPH_NAMES[g] for g in graphs], rotation=0, fontsize=8)
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis='y', labelsize=8)
    
    # Create legend at the top
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['readahead'], label='Readahead'),
        mpatches.Patch(facecolor=COLORS['reclaim'], label='Reclaim'),
        mpatches.Patch(facecolor=COLORS['irq_delay'], label='IRQ Delay'),
        mpatches.Patch(facecolor=COLORS['system_other'], label='System Other'),
    ]
    
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.99),
               ncol=4, frameon=True, fontsize=9,
               edgecolor='black', fancybox=False)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save figure
    output_path = Path(__file__).resolve().parents[2] / 'outputs' / 'figures' / 'fig_7.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    print("Done!")

if __name__ == '__main__':
    create_system_only_breakdown_plot()
