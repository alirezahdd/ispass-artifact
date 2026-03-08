#!/usr/bin/env python3
"""
Generate breakdown CSV files for all algorithms and graphs.

This script runs parse_stats.py for each algorithm across all graphs
and generates a separate CSV file for each algorithm.
Reads from the results/normal dataset directory.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Configuration
ALGORITHMS = ['bc', 'bfs', 'cc', 'pr', 'sssp', 'tc']
GRAPHS = ['kron', 'road', 'twitter', 'urand', 'web']

def parse_args():
    root_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description='Generate baseline breakdown CSV files for all algorithms/graphs'
    )
    parser.add_argument(
        '--base-dir',
        default=str(root_dir / 'results' / 'normal'),
        help='Path to baseline (normal) results directory'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    script_dir = Path(__file__).parent
    parse_script = script_dir / 'parse_stats.py'
    root_dir = Path(__file__).resolve().parents[2]
    base_dir = Path(args.base_dir)
    output_dir = root_dir / 'outputs' / 'parsed' / 'breakdowns'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating breakdown CSV files for all algorithms...")
    print(f"Source: {base_dir}")
    print(f"Algorithms: {', '.join(ALGORITHMS)}")
    print(f"Graphs: {', '.join(GRAPHS)}")
    print()
    
    # Process each algorithm
    for algorithm in ALGORITHMS:
        output_file = output_dir / f"{algorithm}_breakdown.csv"
        print(f"Processing {algorithm}...")
        
        # Process each graph for this algorithm
        for i, graph in enumerate(GRAPHS):
            append_flag = '--append' if i > 0 else ''
            
            try:
                # Run parse_stats.py
                cmd = [
                    sys.executable,
                    str(parse_script),
                    algorithm,
                    graph,
                    '--base-dir', str(base_dir),
                    '--output', str(output_file)
                ]
                
                if append_flag:
                    cmd.append(append_flag)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                print(f"  ✓ {algorithm}-{graph}")
                
            except subprocess.CalledProcessError as e:
                print(f"  ✗ {algorithm}-{graph}: {e.stderr.strip()}")
            except FileNotFoundError as e:
                print(f"  ✗ {algorithm}-{graph}: Files not found")
        
        print(f"  → {output_file}")
        print()
    
    print("Done! Generated breakdown files:")
    for algorithm in ALGORITHMS:
        output_file = output_dir / f"{algorithm}_breakdown.csv"
        if output_file.exists():
            print(f"  - {output_file}")

if __name__ == '__main__':
    main()
