#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <results/normal-dir> <results/improved-dir> [results/sata-dir]"
  exit 1
fi

NORMAL_DIR="$1"
IMPROVED_DIR="$2"
SATA_DIR="${3:-}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for d in "$NORMAL_DIR" "$IMPROVED_DIR"; do
  if [[ ! -d "$d" ]]; then
    echo "Error: Directory not found: $d"
    exit 1
  fi
done

SATA_AVAILABLE=0
if [[ -n "$SATA_DIR" && -d "$SATA_DIR" && -d "$SATA_DIR/bc" ]]; then
  SATA_AVAILABLE=1
else
  echo "SATA input not available; skipping SATA-specific parsing/plot/report."
fi

echo "[1/3] Regenerating parsed CSVs for selected figures"
python3 "$ROOT_DIR/scripts/parsers/generate_all_breakdowns.py" --base-dir "$NORMAL_DIR"
python3 "$ROOT_DIR/scripts/parsers/generate_all_breakdowns_improved.py" --base-dir "$IMPROVED_DIR"
if [[ "$SATA_AVAILABLE" -eq 1 ]]; then
  python3 "$ROOT_DIR/scripts/parsers/generate_all_breakdowns_sata.py" --base-dir "$SATA_DIR"
fi
python3 "$ROOT_DIR/scripts/parsers/generate_all_comparison.py" \
  --normal-dir "$NORMAL_DIR" \
  --improved-dir "$IMPROVED_DIR" \
  --normal-label normal \
  --improved-label improved
python3 "$ROOT_DIR/scripts/parsers/generate_all_pg_allocation.py" --base-dir "$NORMAL_DIR"

echo "[2/3] Generating selected figures"
python3 "$ROOT_DIR/scripts/plotters/plot_system_only_breakdown.py"
python3 "$ROOT_DIR/scripts/plotters/plot_idle_only_breakdown.py"
python3 "$ROOT_DIR/scripts/plotters/plot_complete_breakdown.py"
python3 "$ROOT_DIR/scripts/plotters/plot_basic_breakdown.py"
if [[ "$SATA_AVAILABLE" -eq 1 ]]; then
  python3 "$ROOT_DIR/scripts/plotters/plot_basic_breakdown_improved_vs_sata.py"
fi
python3 "$ROOT_DIR/scripts/plotters/plot_elapsed_time_comparison.py"
python3 "$ROOT_DIR/scripts/plotters/plot_pg_allocation_latency.py"

FIG_DIR="$ROOT_DIR/outputs/figures"
REPORT_PATH="$ROOT_DIR/outputs/reports/nvme-vs-sata.txt"

echo "[3/3] Done. Selected figures summary"
echo "Generated figures:"
for f in fig_6.pdf fig_7.pdf fig_8.pdf fig_9.pdf fig_10.pdf fig_11.pdf breakdown-nvme_vs_sata.pdf; do
  if [[ -f "$FIG_DIR/$f" ]]; then
    echo "  - $f"
  fi
done

if [[ -f "$REPORT_PATH" ]]; then
  echo "SATA-NVMe report: generated (outputs/reports/nvme-vs-sata.txt)"
else
  echo "SATA-NVMe report: not generated (SATA input unavailable or SATA plot skipped)"
fi
