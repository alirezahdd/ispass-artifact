PYTHON ?= python3
NORMAL_DIR ?= $(CURDIR)/results/normal
IMPROVED_DIR ?= $(CURDIR)/results/improved
SATA_DIR ?= $(CURDIR)/results/sata

.DEFAULT_GOAL := all

PF_STATS_SRC ?= $(CURDIR)/../pf-statistics/results
PF_STATS_IMPROVED_SRC ?= $(CURDIR)/../pf-statistics-improved/results
PF_STATS_SATA_SRC ?= $(CURDIR)/../pf-statistics-SATA/results

.PHONY: all populate-results selected-figures clean clean-outputs

all: selected-figures

populate-results:
	@mkdir -p "$(NORMAL_DIR)" "$(IMPROVED_DIR)"
	@cp -a "$(PF_STATS_SRC)"/. "$(NORMAL_DIR)"/
	@cp -a "$(PF_STATS_IMPROVED_SRC)"/. "$(IMPROVED_DIR)"/
	@if [ -d "$(PF_STATS_SATA_SRC)" ]; then \
		mkdir -p "$(SATA_DIR)"; \
		cp -a "$(PF_STATS_SATA_SRC)"/. "$(SATA_DIR)"/; \
		echo "SATA results copied from $(PF_STATS_SATA_SRC)"; \
	else \
		echo "SATA results not found at $(PF_STATS_SATA_SRC); skipping SATA artifacts."; \
	fi

selected-figures: populate-results
	bash scripts/generate_selected_figures.sh "$(NORMAL_DIR)" "$(IMPROVED_DIR)" "$(SATA_DIR)"

.PHONY: selected-figures-help
selected-figures-help:
	@echo "Usage: make selected-figures [NORMAL_DIR=/path] [IMPROVED_DIR=/path] [SATA_DIR=/path]"
	@echo "       SATA inputs are optional; SATA-only report/figure is skipped when unavailable"
	@echo "       make populate-results [PF_STATS_SRC=/path] [PF_STATS_IMPROVED_SRC=/path] [PF_STATS_SATA_SRC=/path]"

clean-outputs:
	@if [ -d outputs/parsed ]; then find outputs/parsed -mindepth 1 -delete; fi
	@if [ -d outputs/figures ]; then find outputs/figures -mindepth 1 -delete; fi
	@if [ -d outputs/reports ]; then find outputs/reports -mindepth 1 -delete; fi
	@if [ -d "$(NORMAL_DIR)" ]; then find "$(NORMAL_DIR)" -mindepth 1 -delete; fi
	@if [ -d "$(IMPROVED_DIR)" ]; then find "$(IMPROVED_DIR)" -mindepth 1 -delete; fi
	@if [ -d "$(SATA_DIR)" ]; then find "$(SATA_DIR)" -mindepth 1 -delete; fi

clean: clean-outputs
	@find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	@find . -maxdepth 1 -name '*-histograms.png' -type f -delete
