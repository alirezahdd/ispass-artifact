#!/usr/bin/env python3

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Professional color scheme
COLORS = {
    'baseline': "#81CAFF",      # Professional blue
    'improved': "#28A64C",      # Sea green
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

def load_comparison_data():
    """Load comparison data for both results directories"""
    csv_path = Path(__file__).resolve().parents[2] / 'outputs' / 'parsed' / 'comparison' / 'all_comparison.csv'
    
    data = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results_dir = row['results_dir']
            algorithm = row['algorithm']
            graph = row['graph']
            
            if algorithm not in data:
                data[algorithm] = {}
            if graph not in data[algorithm]:
                data[algorithm][graph] = {}
            
            data[algorithm][graph][results_dir] = {
                'elapsed_time': float(row['elapsed_time'])
            }
    
    return data

def create_elapsed_time_comparison_plot():
    """Create elapsed time comparison plot with 2x3 layout"""
    algorithms = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
    graphs = ['road', 'web', 'twitter', 'kron', 'urand']
    
    # Load data
    print("Loading comparison data...")
    all_data = load_comparison_data()
    print(f"Loaded data for {len(all_data)} algorithms")
    
    # Create figure with 2x3 subplots
    print("Creating elapsed time comparison plot...")
    fig, axes = plt.subplots(2, 3, figsize=(7, 5.5))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.94, bottom=0.08, hspace=0.35, wspace=0.30)
    
    # Flatten axes
    axes_flat = axes.flatten()
    
    for idx, algorithm in enumerate(algorithms):
        ax = axes_flat[idx]
        
        # Prepare data for plotting
        num_graphs = len(graphs)
        x = np.arange(num_graphs)
        width = 0.35  # Width of bars
        
        baseline_times = []
        improved_times = []
        
        for graph in graphs:
            baseline = all_data[algorithm][graph]['normal']['elapsed_time']
            improved = all_data[algorithm][graph]['improved']['elapsed_time']
            baseline_times.append(100.0)  # Baseline normalized to 100%
            improved_times.append((improved / baseline) * 100.0)  # Relative to baseline
        
        # Create side-by-side bars
        ax.bar(x - width/2, baseline_times, width, color=COLORS['baseline'], 
               label='Baseline', edgecolor='black', linewidth=0.5)
        ax.bar(x + width/2, improved_times, width, color=COLORS['improved'], 
               label='Improved', edgecolor='black', linewidth=0.5)
        
        # Add 100% reference line
        ax.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        
        # Customize subplot
        if idx % 3 == 0:
            ax.set_ylabel('Normalized Time (%)', fontsize=9)
        ax.set_title(ALGORITHM_NAMES[algorithm], fontsize=10, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([GRAPH_NAMES[g] for g in graphs], rotation=0, fontsize=8)
        ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis='y', labelsize=8)
        
        # Set y-axis to start at 0
        ax.set_ylim(bottom=0)
    
    # Create legend
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['baseline'], edgecolor='black', label='1 jiffy sleep'),
        mpatches.Patch(facecolor=COLORS['improved'], edgecolor='black', label='20-30 us sleep'),
    ]
    
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.99),
               ncol=2, frameon=True, fontsize=9,
               edgecolor='black', fancybox=False)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save figure
    output_path = Path(__file__).resolve().parents[2] / 'outputs' / 'figures' / 'fig_11.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    print("Done!")

if __name__ == '__main__':
    create_elapsed_time_comparison_plot()
