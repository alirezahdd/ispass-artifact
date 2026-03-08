#!/usr/bin/env python3
"""
Generate breakdown CSV files for all algorithms and graphs
using the results/improved dataset as the NVMe source.

Outputs to outputs/parsed/breakdowns_improved/.
"""

import subprocess
import sys
import argparse
from pathlib import Path

# Configuration
ALGORITHMS = ['bc', 'bfs', 'cc', 'pr', 'sssp', 'tc']
GRAPHS = ['kron', 'road', 'twitter', 'urand', 'web']


def parse_args():
    root_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description='Generate breakdown CSVs from improved results dataset'
    )
    parser.add_argument(
        '--base-dir',
        default=str(root_dir / 'results' / 'improved'),
        help='Path to improved results directory'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    script_dir = Path(__file__).parent
    root_dir   = Path(__file__).resolve().parents[2]

    parse_script = script_dir / 'parse_stats.py'
    base_dir     = Path(args.base_dir)
    output_dir   = root_dir   / 'outputs' / 'parsed' / 'breakdowns_improved'

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating breakdown CSV files from results/improved...")
    print(f"Source : {base_dir}")
    print(f"Output : {output_dir}")
    print(f"Algorithms: {', '.join(ALGORITHMS)}")
    print(f"Graphs    : {', '.join(GRAPHS)}")
    print()

    for algorithm in ALGORITHMS:
        output_file = output_dir / f"{algorithm}_breakdown.csv"
        print(f"Processing {algorithm}...")

        for i, graph in enumerate(GRAPHS):
            cmd = [
                sys.executable,
                str(parse_script),
                algorithm,
                graph,
                '--base-dir', str(base_dir),
                '--output',   str(output_file),
            ]
            if i > 0:
                cmd.append('--append')

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(f"  ✓ {algorithm}-{graph}")
            except subprocess.CalledProcessError as e:
                print(f"  ✗ {algorithm}-{graph}: {e.stderr.strip()}")
            except FileNotFoundError:
                print(f"  ✗ {algorithm}-{graph}: files not found")

        print(f"  → {output_file}")
        print()

    print("Done! Generated breakdown files:")
    for algorithm in ALGORITHMS:
        output_file = output_dir / f"{algorithm}_breakdown.csv"
        if output_file.exists():
            print(f"  - {output_file}")


if __name__ == '__main__':
    main()
