#!/usr/bin/env python3
import csv
import matplotlib.pyplot as plt
import sys

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

def read_csv_data(filename):
    """Read CSV file and return iterations, access times, major and minor faults count."""
    iterations = []
    access_times = []
    major_faults = 0
    minor_faults = 0
    
    min_minor_time = float('inf')
    max_minor_time = 0
    min_major_time = float('inf')
    max_major_no_reclaim_time = 0
    min_reclaim_time = float('inf')
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            iterations.append(int(row['iter']))
            access_time = float(row['access_time'])
            access_times.append(access_time)
            major_faults += int(row['mj_fault'])
            minor_faults += int(row['min_fault'])
            
            # Track statistics
            if int(row['min_fault']) == 1:
                min_minor_time = min(min_minor_time, access_time)
                max_minor_time = max(max_minor_time, access_time)
            if int(row['mj_fault']) == 1:
                min_major_time = min(min_major_time, access_time)
                if int(row['reclaim']) == 0:
                    max_major_no_reclaim_time = max(max_major_no_reclaim_time, access_time)
            if int(row['reclaim']) == 1:
                min_reclaim_time = min(min_reclaim_time, access_time)
    
    if min_minor_time == float('inf'):
        min_minor_time = None
    if min_major_time == float('inf'):
        min_major_time = None
    if min_reclaim_time == float('inf'):
        min_reclaim_time = None
    
    return iterations, access_times, major_faults, minor_faults, min_minor_time, max_minor_time, min_major_time, max_major_no_reclaim_time, min_reclaim_time

def plot_access_times():
    """
    Plot access times for seq and rnd benchmarks.
    X-axis: iteration number
    Y-axis: access time
    """
    
    # Read CSV files
    results_dir = "../results"
    
    try:
        seq_iter, seq_time, seq_mj, seq_mn, seq_min_min, seq_max_min, seq_min_maj, seq_max_maj_no_rec, seq_min_rec = read_csv_data(f"{results_dir}/seq_merged.csv")
        rnd_iter, rnd_time, rnd_mj, rnd_mn, rnd_min_min, rnd_max_min, rnd_min_maj, rnd_max_maj_no_rec, rnd_min_rec = read_csv_data(f"{results_dir}/rnd_merged.csv")
    except FileNotFoundError as e:
        print(f"Error: Could not find one or more CSV files: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        sys.exit(1)
    
    # Print statistics
    print("\n=== Access Time Statistics ===")
    print(f"\nseq:")
    print(f"  Min minor fault time: {seq_min_min:.2f} μs" if seq_min_min else "  Min minor fault time: N/A")
    print(f"  Max minor fault time: {seq_max_min:.2f} μs")
    print(f"  Min major fault time: {seq_min_maj:.2f} μs" if seq_min_maj else "  Min major fault time: N/A")
    print(f"  Max major fault time (no reclaim): {seq_max_maj_no_rec:.2f} μs")
    print(f"  Min reclaim time: {seq_min_rec:.2f} μs" if seq_min_rec else "  Min reclaim time: N/A")
    
    print(f"\nrnd:")
    print(f"  Min minor fault time: {rnd_min_min:.2f} μs" if rnd_min_min else "  Min minor fault time: N/A")
    print(f"  Max minor fault time: {rnd_max_min:.2f} μs")
    print(f"  Min major fault time: {rnd_min_maj:.2f} μs" if rnd_min_maj else "  Min major fault time: N/A")
    print(f"  Max major fault time (no reclaim): {rnd_max_maj_no_rec:.2f} μs")
    print(f"  Min reclaim time: {rnd_min_rec:.2f} μs" if rnd_min_rec else "  Min reclaim time: N/A")
    print()

    min_minor = min(filter(None, [seq_min_min, rnd_min_min]))
    max_minor = max([seq_max_min, rnd_max_min])
    min_major = min(filter(None, [seq_min_maj, rnd_min_maj]))
    max_major = max([seq_max_maj_no_rec, rnd_max_maj_no_rec])
    min_reclaim = min(filter(None, [seq_min_rec, rnd_min_rec]))
    
    # Create the plot (single column size for two-column paper: 3.5" width)
    plt.figure(figsize=(3.5, 2.8))
    
    # Plot seq
    plt.plot(seq_iter, seq_time, 
             marker='o', linestyle='', markersize=3, 
             label=f'seq', 
             color='#2E86AB', zorder=1, markeredgewidth=0)  # Blue
    
    # Plot rnd
    plt.plot(rnd_iter, rnd_time, 
             marker='^', linestyle='', markersize=3, 
             label=f'rnd', 
             color='#A23B72', zorder=2, markeredgewidth=0)  # Purple
    
    plt.axhspan(min_minor, max_minor, alpha=0.1, color='green', zorder=0, edgecolor='none')
    plt.axhspan(min_major, max_major, alpha=0.1, color='orange', zorder=0, edgecolor='none')
    plt.axhspan(min_reclaim, plt.ylim()[1], alpha=0.1, color='red', zorder=0, edgecolor='none')
    
    # Add text labels for categories (positioned on the right side)
    plt.text(plt.xlim()[1] * 1.02, (min_minor + max_minor) / 2, f'Minor\n({min_minor:.0f}-{max_minor:.0f}μs)', fontsize=6, 
         verticalalignment='center', color='darkgreen', weight='bold')
    plt.text(plt.xlim()[1] * 1.02, ((min_major + max_major) / 2) - 200 , f'Major\n({min_major:.0f}-{max_major:.0f}μs)', fontsize=6, 
        verticalalignment='center', color='darkorange', weight='bold')
    plt.text(plt.xlim()[1] * 1.02, min_reclaim+1000, f'Reclaim\n({min_reclaim:.0f}+μs)', fontsize=6, 
             verticalalignment='center', color='darkred', weight='bold')
    
    # Formatting
    plt.xlabel('Iteration Number', fontsize=9)
    plt.ylabel('Fault Handling Time (μs)', fontsize=9)
    plt.yscale('log')
    plt.legend(fontsize=7, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=True)
    plt.grid(True, alpha=0.3)
    plt.tick_params(labelsize=8)
    plt.tight_layout()
    
    # Save the plot
    output_pdf = "../figures/access_time_comparison_no_seq8.pdf"
    plt.savefig(output_pdf, bbox_inches='tight')
    print(f"Plot saved to {output_pdf}")
    
    # Show the plot
    # plt.show()

if __name__ == "__main__":
    plot_access_times()
