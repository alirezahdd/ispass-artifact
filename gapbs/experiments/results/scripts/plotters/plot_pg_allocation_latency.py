#!/usr/bin/env python3
import csv
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Read the data
data_file = Path(__file__).resolve().parents[2] / 'outputs' / 'parsed' / 'pg_allocation' / 'all_pg_allocation.csv'

# Load data into dictionary
data = {}
with open(data_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        alg = row['algorithm']
        graph = row['graph']
        # Convert from nanoseconds to microseconds for better readability
        latency_us = float(row['avg_latency_ns']) / 1000.0
        
        if alg not in data:
            data[alg] = {}
        data[alg][graph] = latency_us

# Define order
algorithm_order = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
graph_order = ['road', 'web', 'twitter', 'kron', 'urand']
graph_labels = ['R', 'W', 'T', 'K', 'U']

# Create figure with 2x3 subplots
fig, axes = plt.subplots(2, 3, figsize=(7, 5.5))
axes = axes.flatten()

# Plot each algorithm
for idx, alg in enumerate(algorithm_order):
    ax = axes[idx]
    
    # Get latencies for this algorithm in graph order
    latencies = [data[alg][graph] for graph in graph_order]
    
    # Create bar positions
    x_pos = np.arange(len(graph_order))
    
    # Plot bars
    bars = ax.bar(x_pos, latencies, color='#4A90E2', edgecolor='none', width=0.6)
    
    # Formatting
    ax.set_xticks(x_pos)
    ax.set_xticklabels(graph_labels)
    ax.set_title(alg.upper(), fontsize=11, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Y-axis label only on left column
    if idx % 3 == 0:
        ax.set_ylabel('Avg Latency (μs)', fontsize=10)
    
    # X-axis label only on bottom row
    if idx >= 3:
        ax.set_xlabel('Graph', fontsize=10)

# Adjust layout
plt.tight_layout()

# Save figure
output_dir = Path(__file__).resolve().parents[2] / 'outputs' / 'figures'
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / 'fig_10.pdf'

plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
print(f"Saved page allocation latency plot to {output_file}")

plt.close()
