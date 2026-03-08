SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

CXX := g++
PYTHON := python3
PIP := $(PYTHON) -m pip
PLOT_SCRIPT := plot_access_time.py
TIMESTAMP_BREAKDOWN_SCRIPT := plot_timestamp_breakdown.py
TIMESTAMP_COMPARISON_SCRIPT := plot_timestamp_comparison.py
PYTHON_REQUIREMENTS := requirements.txt

BIN_DIR := bin
SRC_DIR := src
RESULTS_RAW_DIR := results-raw
RESULTS_DIR := results
FIGURES_DIR := figures

CGROUP_NAME := u_bench_group
CGROUP_MEM_PATH := /sys/fs/cgroup/memory
MEM_LIMIT_MB ?= 2
SLEEP_SECONDS ?= 2
PLOT_METRIC ?= access_time
PLOT_CAP_PERCENTILE ?= 99
PLOT_OUTPUT ?= ../figures/fig_3.pdf

CXXFLAGS := -g -no-pie -std=c++11 -O1 -Wall

COMMON_SRCS := $(SRC_DIR)/u_benchmark.cc
BENCHMARKS := seq rnd seq_8page
BINARIES := $(addprefix $(BIN_DIR)/,$(BENCHMARKS))
MEM_LIMIT_BYTES := $(shell echo $$(( $(MEM_LIMIT_MB) * 1024 * 1024 )))

.PHONY: all deps run setup-cgroup run-benchmarks parse plot clean dirs

all: $(BINARIES)

deps:
	@echo "Checking system and Python dependencies..."
	@if ! command -v $(CXX) >/dev/null 2>&1; then \
		echo "Installing g++ and build tools..."; \
		sudo apt-get update; \
		sudo apt-get install -y build-essential; \
	fi
	@if ! command -v $(PYTHON) >/dev/null 2>&1; then \
		echo "Installing python3 and python3-pip..."; \
		sudo apt-get update; \
		sudo apt-get install -y python3 python3-pip; \
	fi
	@if ! $(PIP) --version >/dev/null 2>&1; then \
		echo "Installing python3-pip..."; \
		sudo apt-get update; \
		sudo apt-get install -y python3-pip; \
	fi
	@$(PIP) install --user -r "$(PYTHON_REQUIREMENTS)"
	@if ! command -v cgcreate >/dev/null 2>&1 || ! command -v cgset >/dev/null 2>&1 || ! command -v cgexec >/dev/null 2>&1; then \
		echo "Installing libcgroup-tools..."; \
		sudo apt-get update; \
		sudo apt-get install -y libcgroup-tools; \
	fi
	@echo "Dependency setup complete."

run: deps all run-benchmarks parse plot

dirs:
	@mkdir -p "$(BIN_DIR)"

$(BIN_DIR)/seq: $(SRC_DIR)/seq.cc $(COMMON_SRCS) | dirs
	$(CXX) $^ -o $@ $(CXXFLAGS)

$(BIN_DIR)/rnd: $(SRC_DIR)/rnd.cc $(COMMON_SRCS) | dirs
	$(CXX) $^ -o $@ $(CXXFLAGS)

$(BIN_DIR)/seq_8page: $(SRC_DIR)/seq_8page.cc $(COMMON_SRCS) | dirs
	$(CXX) $^ -o $@ $(CXXFLAGS)

setup-cgroup:
	@if ! command -v cgcreate >/dev/null 2>&1 || ! command -v cgset >/dev/null 2>&1; then \
		echo "Installing libcgroup-tools..."; \
		sudo apt-get update; \
		sudo apt-get install -y libcgroup-tools; \
	fi
	@if [[ ! -d "$(CGROUP_MEM_PATH)" ]]; then \
		sudo mkdir -p "$(CGROUP_MEM_PATH)"; \
		sudo mount -t cgroup -o memory memory "$(CGROUP_MEM_PATH)"; \
	fi
	@if [[ ! -d "$(CGROUP_MEM_PATH)/$(CGROUP_NAME)" ]]; then \
		sudo cgcreate -g "memory:$(CGROUP_NAME)"; \
	fi
	sudo cgset -r "memory.limit_in_bytes=$(MEM_LIMIT_BYTES)" "$(CGROUP_NAME)"
	@echo "Configured cgroup '$(CGROUP_NAME)' memory limit to $(MEM_LIMIT_MB)MB ($(MEM_LIMIT_BYTES) bytes)."

run-benchmarks: setup-cgroup
	@mkdir -p "$(RESULTS_RAW_DIR)"
	rm -f "$(RESULTS_RAW_DIR)"/*.txt
	sleep "$(SLEEP_SECONDS)"
	sudo cgexec -g "memory:$(CGROUP_NAME)" "$(BIN_DIR)/seq" "$(RESULTS_RAW_DIR)/seq-perf.txt" > "$(RESULTS_RAW_DIR)/seq.txt"
	sleep "$(SLEEP_SECONDS)"
	sudo cgexec -g "memory:$(CGROUP_NAME)" "$(BIN_DIR)/rnd" "$(RESULTS_RAW_DIR)/rnd-perf.txt" > "$(RESULTS_RAW_DIR)/rnd.txt"
	sleep "$(SLEEP_SECONDS)"
	sudo cgexec -g "memory:$(CGROUP_NAME)" "$(BIN_DIR)/seq_8page" "$(RESULTS_RAW_DIR)/seq_8page-perf.txt" > "$(RESULTS_RAW_DIR)/seq_8page.txt"
	sleep "$(SLEEP_SECONDS)"
	@echo "Benchmark runs finished."

parse:
	@mkdir -p "$(RESULTS_DIR)"
	@echo "Parsing and merging results..."
	cd parsers && $(PYTHON) parse_and_merge.py seq
	cd parsers && $(PYTHON) parse_and_merge.py rnd
	cd parsers && $(PYTHON) parse_and_merge.py seq_8page

plot:
	@mkdir -p "$(FIGURES_DIR)"
	@echo "Generating plots..."
	cd plotters && $(PYTHON) "$(PLOT_SCRIPT)" \
		--metric "$(PLOT_METRIC)" \
		--cap-percentile "$(PLOT_CAP_PERCENTILE)" \
		--output "$(PLOT_OUTPUT)"
	cd plotters && $(PYTHON) "$(TIMESTAMP_BREAKDOWN_SCRIPT)"
	cd plotters && $(PYTHON) "$(TIMESTAMP_COMPARISON_SCRIPT)"
	@echo "All done!"

clean:
	rm -rf "$(BIN_DIR)"
	rm -rf "$(RESULTS_RAW_DIR)"
	rm -rf "$(RESULTS_DIR)"
	rm -rf "$(FIGURES_DIR)"
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
