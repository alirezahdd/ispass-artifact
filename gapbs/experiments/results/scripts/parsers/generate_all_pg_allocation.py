#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

algorithms = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
graphs = ['road', 'web', 'twitter', 'kron', 'urand']


def parse_args():
    root_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description='Generate page allocation latency CSV for all workloads')
    parser.add_argument(
        '--base-dir',
        default=str(root_dir / 'results' / 'normal'),
        help='Path to base results directory containing algorithm subdirectories'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    output_dir = Path(__file__).resolve().parents[2] / 'outputs' / 'parsed' / 'pg_allocation'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'all_pg_allocation.csv'
    if output_file.exists():
        output_file.unlink()

    for algorithm in algorithms:
        for graph in graphs:
            cmd = [
                sys.executable,
                'parse_pg_allocation.py',
                algorithm,
                graph,
                '--base-dir',
                str(args.base_dir),
                '--output',
                str(output_file)
            ]

            print(f"Processing {algorithm}-{graph}...")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)

            if result.returncode != 0:
                print(f"Error processing {algorithm}-{graph}: {result.stderr}")
            else:
                print(result.stdout.strip())

    print(f"\nAll page allocation data written to {output_file}")


if __name__ == '__main__':
    main()
