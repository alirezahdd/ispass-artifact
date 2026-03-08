#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

algorithms = ['bc', 'sssp', 'tc', 'bfs', 'cc', 'pr']
graphs = ['road', 'web', 'twitter', 'kron', 'urand']


def parse_args():
    root_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description='Generate all comparison CSV rows')
    parser.add_argument('--normal-dir', default=str(root_dir / 'results' / 'normal'),
                        help='Path to normal baseline results directory')
    parser.add_argument('--improved-dir', default=str(root_dir / 'results' / 'improved'),
                        help='Path to improved results directory')
    parser.add_argument('--normal-label', default='normal',
                        help='CSV label for normal baseline dataset')
    parser.add_argument('--improved-label', default='improved',
                        help='CSV label for improved dataset')
    return parser.parse_args()


def main():
    args = parse_args()

    dataset_configs = [
        (args.normal_label, args.normal_dir),
        (args.improved_label, args.improved_dir),
    ]

    root_dir = Path(__file__).resolve().parents[2]
    output_dir = root_dir / 'outputs' / 'parsed' / 'comparison'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'all_comparison.csv'
    if output_file.exists():
        output_file.unlink()

    for label, results_dir in dataset_configs:
        for algorithm in algorithms:
            for graph in graphs:
                cmd = [
                    sys.executable,
                    'parse_comparison.py',
                    algorithm,
                    graph,
                    '--results-dir',
                    str(results_dir),
                    '--results-label',
                    label,
                    '--output',
                    str(output_file)
                ]

                print(f"Processing {label}/{algorithm}-{graph}...")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)

                if result.returncode != 0:
                    print(f"Error: {result.stderr}")
                else:
                    print(result.stdout.strip())

    print(f"\nAll comparison data written to {output_file}")


if __name__ == '__main__':
    main()
