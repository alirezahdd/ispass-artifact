# Artifact Output Generation

This entrypoint generates the selected artifact outputs.

Figures written to `outputs/figures`:

- `outputs/figures/fig_6.pdf`
- `outputs/figures/fig_7.pdf`
- `outputs/figures/fig_8.pdf`
- `outputs/figures/fig_9.pdf`
- `outputs/figures/fig_10.pdf`
- `outputs/figures/fig_11.pdf`
- `outputs/figures/breakdown-nvme_vs_sata.pdf`

Report written to `outputs/reports`:

- `outputs/reports/nvme-vs-sata.txt`

## Usage

From repository root:

```bash
make selected-figures \
  NORMAL_DIR=/path/to/results/normal \
  IMPROVED_DIR=/path/to/results/improved \
  SATA_DIR=/path/to/results/sata
```

Or run the script directly:

```bash
bash scripts/generate_selected_figures.sh \
  /path/to/results/normal \
  /path/to/results/improved \
  /path/to/results/sata
```

## Cleanup

To remove generated parsed data, figures, and reports:

```bash
make clean
```
