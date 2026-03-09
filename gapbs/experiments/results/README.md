# Artifact Output Generation

This entrypoint generates the selected artifact outputs.

Default behavior:

- `make` runs the full pipeline: population + parsing + plotting.
- SATA data is optional. If unavailable, SATA-only artifact(s) are skipped.

Figures written to `outputs/figures`:

- `outputs/figures/fig_6.pdf`
- `outputs/figures/fig_7.pdf`
- `outputs/figures/fig_8.pdf`
- `outputs/figures/fig_9.pdf`
- `outputs/figures/fig_10.pdf`
- `outputs/figures/fig_11.pdf`
- `outputs/figures/breakdown-nvme_vs_sata.pdf` (only when SATA input is available)

Report written to `outputs/reports`:

- `outputs/reports/nvme-vs-sata.txt` (only when SATA input is available)

## Usage

From `experiments/results`:

```bash
make
```

This runs `populate-results` and `selected-figures`.

Run with explicit locations:

```bash
make selected-figures \
  NORMAL_DIR=/path/to/results/normal \
  IMPROVED_DIR=/path/to/results/improved \
  SATA_DIR=/path/to/results/sata
```

If SATA is missing, the pipeline still succeeds and skips only SATA-specific outputs.

Or run the script directly:

```bash
bash scripts/generate_selected_figures.sh \
  /path/to/results/normal \
  /path/to/results/improved \
  [/path/to/results/sata]
```

## Cleanup

To remove generated parsed data, figures, reports, and populated local copies under `results/`:

```bash
make clean
```
