#!/usr/bin/env python3
"""
Generate breakdown CSV files for all algorithms and graphs from the results/sata directory.

Same logic as generate_all_breakdowns.py but points at results/sata/ as the
base data directory and writes to outputs/parsed/breakdowns_sata/.
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
        description='Generate breakdown CSVs from SATA results dataset'
    )
    parser.add_argument(
        '--base-dir',
        default=str(root_dir / 'results' / 'sata'),
        help='Path to SATA results directory'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    script_dir = Path(__file__).parent
    parse_script = script_dir / 'parse_stats.py'

    sata_base_dir = Path(args.base_dir)
    root_dir = Path(__file__).resolve().parents[2]
    output_dir = root_dir / 'outputs' / 'parsed' / 'breakdowns_sata'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating SATA breakdown CSV files for all algorithms...")
    print(f"Base directory : {sata_base_dir}")
    print(f"Algorithms     : {', '.join(ALGORITHMS)}")
    print(f"Graphs         : {', '.join(GRAPHS)}")
    print()

    # Process each algorithm
    for algorithm in ALGORITHMS:
        output_file = output_dir / f"{algorithm}_breakdown.csv"
        print(f"Processing {algorithm}...")

        # Process each graph for this algorithm
        for i, graph in enumerate(GRAPHS):
            append_flag = '--append' if i > 0 else ''

            try:
                cmd = [
                    sys.executable,
                    str(parse_script),
                    algorithm,
                    graph,
                    '--base-dir', str(sata_base_dir),
                    '--output', str(output_file),
                ]

                if append_flag:
                    cmd.append(append_flag)

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                print(f"  ✓ {algorithm}-{graph}")

            except subprocess.CalledProcessError as e:
                print(f"  ✗ {algorithm}-{graph}: {e.stderr.strip()}")
            except FileNotFoundError as e:
                print(f"  ✗ {algorithm}-{graph}: Files not found")

        print(f"  → {output_file}")
        print()

    print("Done! Generated SATA breakdown files:")
    for algorithm in ALGORITHMS:
        output_file = output_dir / f"{algorithm}_breakdown.csv"
        if output_file.exists():
            print(f"  - {output_file}")

if __name__ == '__main__':
    main()
