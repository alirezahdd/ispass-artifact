#!/usr/bin/env python3
import csv
import matplotlib.pyplot as plt
import sys

def read_csv_data(filename):
    """Read CSV file and return iterations, kernel instructions, major and minor faults count."""
    iterations = []
    kernel_instr = []
    major_faults = 0
    minor_faults = 0
    
    min_minor_instr = float('inf')
    max_minor_instr = 0
    min_major_instr = float('inf')
    max_major_no_reclaim_instr = 0
    min_reclaim_instr = float('inf')
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            iterations.append(int(row['iter']))
            k_instr = int(row['k_intsr'])
            kernel_instr.append(k_instr)
            major_faults += int(row['mj_fault'])
            minor_faults += int(row['min_fault'])
            
            # Track statistics
            if int(row['min_fault']) == 1:
                min_minor_instr = min(min_minor_instr, k_instr)
                max_minor_instr = max(max_minor_instr, k_instr)
            if int(row['mj_fault']) == 1:
                min_major_instr = min(min_major_instr, k_instr)
                if int(row['reclaim']) == 0:
                    max_major_no_reclaim_instr = max(max_major_no_reclaim_instr, k_instr)
            if int(row['reclaim']) == 1:
                min_reclaim_instr = min(min_reclaim_instr, k_instr)
    
    if min_minor_instr == float('inf'):
        min_minor_instr = None
    if min_major_instr == float('inf'):
        min_major_instr = None
    if min_reclaim_instr == float('inf'):
        min_reclaim_instr = None
    
    return iterations, kernel_instr, major_faults, minor_faults, min_minor_instr, max_minor_instr, min_major_instr, max_major_no_reclaim_instr, min_reclaim_instr

def plot_kernel_instructions():
    """
    Plot kernel instructions for seq, seq_8page, and rnd benchmarks.
    X-axis: iteration number
    Y-axis: kernel instructions
    """
    
    # Read CSV files
    results_dir = "../results"
    
    try:
        seq_iter, seq_kinstr, seq_mj, seq_mn, seq_min_min, seq_max_min, seq_min_maj, seq_max_maj_no_rec, seq_min_rec = read_csv_data(f"{results_dir}/seq_merged.csv")
        seq8_iter, seq8_kinstr, seq8_mj, seq8_mn, seq8_min_min, seq8_max_min, seq8_min_maj, seq8_max_maj_no_rec, seq8_min_rec = read_csv_data(f"{results_dir}/seq_8page_merged.csv")
        rnd_iter, rnd_kinstr, rnd_mj, rnd_mn, rnd_min_min, rnd_max_min, rnd_min_maj, rnd_max_maj_no_rec, rnd_min_rec = read_csv_data(f"{results_dir}/rnd_merged.csv")
    except FileNotFoundError as e:
        print(f"Error: Could not find one or more CSV files: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        sys.exit(1)
    
    # Print statistics
    print("\n=== Kernel Instructions Statistics ===")
    print(f"\nseq:")
    print(f"  Min minor fault instructions: {seq_min_min}" if seq_min_min else "  Min minor fault instructions: N/A")
    print(f"  Max minor fault instructions: {seq_max_min}")
    print(f"  Min major fault instructions: {seq_min_maj}" if seq_min_maj else "  Min major fault instructions: N/A")
    print(f"  Max major fault instructions (no reclaim): {seq_max_maj_no_rec}")
    print(f"  Min reclaim instructions: {seq_min_rec}" if seq_min_rec else "  Min reclaim instructions: N/A")
    
    print(f"\nseq_8page:")
    print(f"  Min minor fault instructions: {seq8_min_min}" if seq8_min_min else "  Min minor fault instructions: N/A")
    print(f"  Max minor fault instructions: {seq8_max_min}")
    print(f"  Min major fault instructions: {seq8_min_maj}" if seq8_min_maj else "  Min major fault instructions: N/A")
    print(f"  Max major fault instructions (no reclaim): {seq8_max_maj_no_rec}")
    print(f"  Min reclaim instructions: {seq8_min_rec}" if seq8_min_rec else "  Min reclaim instructions: N/A")
    
    print(f"\nrnd:")
    print(f"  Min minor fault instructions: {rnd_min_min}" if rnd_min_min else "  Min minor fault instructions: N/A")
    print(f"  Max minor fault instructions: {rnd_max_min}")
    print(f"  Min major fault instructions: {rnd_min_maj}" if rnd_min_maj else "  Min major fault instructions: N/A")
    print(f"  Max major fault instructions (no reclaim): {rnd_max_maj_no_rec}")
    print(f"  Min reclaim instructions: {rnd_min_rec}" if rnd_min_rec else "  Min reclaim instructions: N/A")
    print()
    
    min_minor = min(filter(None, [seq_min_min, seq8_min_min, rnd_min_min]))
    max_minor = max([seq_max_min, seq8_max_min, rnd_max_min])
    min_major = min(filter(None, [seq_min_maj, seq8_min_maj, rnd_min_maj]))
    max_major = max([seq_max_maj_no_rec, seq8_max_maj_no_rec, rnd_max_maj_no_rec])
    min_reclaim = min(filter(None, [seq_min_rec, seq8_min_rec, rnd_min_rec]))
    
    # Create the plot (single column size for two-column paper: 3.5" width)
    plt.figure(figsize=(3.5, 2.8))
    
    # Plot seq
    plt.plot(seq_iter, seq_kinstr, 
             marker='o', linestyle='', markersize=2, 
             label='seq', 
             color='#2E86AB', zorder=1, markeredgewidth=0)  # Blue
    
    # Plot rnd
    plt.plot(rnd_iter, rnd_kinstr, 
             marker='^', linestyle='', markersize=2, 
             label='rnd', 
             color='#A23B72', zorder=2, markeredgewidth=0)  # Purple
    
    # Plot seq_8page with iteration multiplied by 8 (in front with more visible color)
    seq8_iter_scaled = [i * 8 for i in seq8_iter]
    plt.plot(seq8_iter_scaled, seq8_kinstr, 
             marker='s', linestyle='', markersize=2, 
             label='seq_8page', 
             color='#F18F01', zorder=3, markeredgewidth=0)  # Orange
    
    # Add horizontal bands for fault categories based on actual data
    plt.axhspan(min_minor, max_minor, alpha=0.1, color='green', zorder=0, edgecolor='none')
    plt.axhspan(min_major, max_major, alpha=0.1, color='orange', zorder=0, edgecolor='none')
    plt.axhspan(min_reclaim, plt.ylim()[1], alpha=0.1, color='red', zorder=0, edgecolor='none')
    
    # Add text labels for categories (positioned on the right side)
    plt.text(plt.xlim()[1] * 1.02, 20e4, 'Minor', fontsize=6, 
             verticalalignment='center', color='darkgreen', weight='bold')
    plt.text(plt.xlim()[1] * 1.02, 4e5, 'Major', fontsize=6, 
             verticalalignment='center', color='darkorange', weight='bold')
    plt.text(plt.xlim()[1] * 1.02, 3e6, 'Reclaim', fontsize=6, 
             verticalalignment='center', color='darkred', weight='bold')
    
    # Formatting
    plt.xlabel('Iteration Number', fontsize=9)
    plt.ylabel('Kernel Instructions', fontsize=9)
    plt.yscale('log')
    plt.legend(fontsize=7, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3, frameon=True)
    plt.grid(True, alpha=0.3)
    plt.tick_params(labelsize=8)
    plt.tight_layout()
    
    # Save the plot
    output_pdf = "../figures/kernel_instructions_comparison.pdf"
    plt.savefig(output_pdf, bbox_inches='tight')
    print(f"Plot saved to {output_pdf}")
    
    # Show the plot
    # plt.show()

if __name__ == "__main__":
    plot_kernel_instructions()
