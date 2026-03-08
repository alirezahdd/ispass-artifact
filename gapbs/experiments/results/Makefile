PYTHON ?= python3
NORMAL_DIR ?= $(CURDIR)/results/normal
IMPROVED_DIR ?= $(CURDIR)/results/improved
SATA_DIR ?= $(CURDIR)/results/sata

PF_STATS_SRC ?= $(CURDIR)/../pf-statistics/results
PF_STATS_IMPROVED_SRC ?= $(CURDIR)/../pf-statistics-improved/results
PF_STATS_SATA_SRC ?= $(CURDIR)/../pf-statistics-SATA/results

.PHONY: populate-results selected-figures clean clean-outputs

populate-results:
	@mkdir -p "$(NORMAL_DIR)" "$(IMPROVED_DIR)" "$(SATA_DIR)"
	@cp -a "$(PF_STATS_SRC)"/. "$(NORMAL_DIR)"/
	@cp -a "$(PF_STATS_IMPROVED_SRC)"/. "$(IMPROVED_DIR)"/
	@cp -a "$(PF_STATS_SATA_SRC)"/. "$(SATA_DIR)"/

selected-figures: populate-results
	bash scripts/generate_selected_figures.sh "$(NORMAL_DIR)" "$(IMPROVED_DIR)" "$(SATA_DIR)"

.PHONY: selected-figures-help
selected-figures-help:
	@echo "Usage: make selected-figures [NORMAL_DIR=/path] [IMPROVED_DIR=/path] [SATA_DIR=/path]"
	@echo "       make populate-results [PF_STATS_SRC=/path] [PF_STATS_IMPROVED_SRC=/path] [PF_STATS_SATA_SRC=/path]"

clean-outputs:
	@if [ -d outputs/parsed ]; then find outputs/parsed -mindepth 1 -delete; fi
	@if [ -d outputs/figures ]; then find outputs/figures -mindepth 1 -delete; fi
	@if [ -d outputs/reports ]; then find outputs/reports -mindepth 1 -delete; fi

clean: clean-outputs
	@find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	@find . -maxdepth 1 -name '*-histograms.png' -type f -delete
