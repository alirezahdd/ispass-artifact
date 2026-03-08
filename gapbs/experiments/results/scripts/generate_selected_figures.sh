#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <results/normal-dir> <results/improved-dir> <results/sata-dir>"
  exit 1
fi

NORMAL_DIR="$1"
IMPROVED_DIR="$2"
SATA_DIR="$3"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for d in "$NORMAL_DIR" "$IMPROVED_DIR" "$SATA_DIR"; do
  if [[ ! -d "$d" ]]; then
    echo "Error: Directory not found: $d"
    exit 1
  fi
done

echo "[1/3] Regenerating parsed CSVs for selected figures"
python3 "$ROOT_DIR/scripts/parsers/generate_all_breakdowns.py" --base-dir "$NORMAL_DIR"
python3 "$ROOT_DIR/scripts/parsers/generate_all_breakdowns_improved.py" --base-dir "$IMPROVED_DIR"
python3 "$ROOT_DIR/scripts/parsers/generate_all_breakdowns_sata.py" --base-dir "$SATA_DIR"
python3 "$ROOT_DIR/scripts/parsers/generate_all_comparison.py" \
  --normal-dir "$NORMAL_DIR" \
  --improved-dir "$IMPROVED_DIR" \
  --normal-label normal \
  --improved-label improved
python3 "$ROOT_DIR/scripts/parsers/generate_all_pg_allocation.py" --base-dir "$NORMAL_DIR"

echo "[2/3] Generating selected figures"
pushd "$ROOT_DIR/scripts/plotters" >/dev/null
python3 plot_system_only_breakdown.py
python3 plot_idle_only_breakdown.py
python3 plot_complete_breakdown.py
python3 plot_basic_breakdown.py
python3 plot_basic_breakdown_improved_vs_sata.py
python3 plot_elapsed_time_comparison.py
python3 plot_pg_allocation_latency.py
popd >/dev/null

echo "[3/3] Done. Selected figures are available under $ROOT_DIR/outputs/figures"
