# Artifact Workflow

This is the main workflow document for reproducing the artifact results.

## Overview

The evaluation process consists of:
1. Download Linux kernel `6.7.2`
2. Patch kernel with `1.patch`
3. Build and install the patched kernel
4. Install `perf` from the same kernel source
5. Configure NVMe swap (60G)
6. Run micro-benchmark and generate figures 3-5
7. Build GAPBS graphs and place them in `/share/graphs/`
8. Run baseline GAPBS experiment (`pf-statistics`)
9. Populate results and generate figures 6-11
10. Optional: run an additional NVMe-SATA comparison round (time-consuming; not needed for paper plots)

## Quick Checklist

After Step 5 and before Step 6, go through each checklist item and confirm it passes:

Set your artifact root once per shell session:

```bash
export ARTIFACT_ROOT="$HOME/ispass-artifact"
```

- Kernel: `uname -r` matches the intended patched kernel for the current phase
- Perf: `perf --version` works and points to the installed tool
- Swap device: `swapon --show` lists only the intended active swap disk
- Working directories exist:
	- `$ARTIFACT_ROOT/micro-benchmark`
	- `$ARTIFACT_ROOT/gapbs`

## Prerequisites

- Ubuntu/Linux system with `sudo` access
- Build tools for kernel compilation
- A dedicated NVMe SSD and a dedicated SATA SSD, each with at least 60 GB free space for swap
- Enough disk space and time for GAPBS graph generation (`/share/graphs/`)

Install common dependencies (example):

```bash
sudo apt-get update
sudo apt-get install -y build-essential flex bison libssl-dev libelf-dev bc dwarves \
	libncurses-dev cpio rsync wget curl git python3 python3-pip parted util-linux cgroup-tools
```

---

## Step 1: Download Linux Kernel 6.7.2

```bash
mkdir -p "$ARTIFACT_ROOT/kernel-src"
cd "$ARTIFACT_ROOT/kernel-src"
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.7.2.tar.xz
tar -xf linux-6.7.2.tar.xz
```

## Step 2: Patch Kernel with `1.patch`

```bash
cd "$ARTIFACT_ROOT/kernel-src/linux-6.7.2"
patch --dry-run -p1 < "$ARTIFACT_ROOT/kernel-patches/1.patch"
patch -p1 < "$ARTIFACT_ROOT/kernel-patches/1.patch"
```

After patching, set cgroup v1 mode by editing the GRUB config file:

```bash
if ! grep -q 'systemd.unified_cgroup_hierarchy=0' /etc/default/grub; then
	sudo sed -i 's/^GRUB_CMDLINE_LINUX="\(.*\)"/GRUB_CMDLINE_LINUX="\1 systemd.unified_cgroup_hierarchy=0"/' /etc/default/grub
fi
sudo update-grub
```

## Step 3: Build and Install the Patched Kernel

```bash
cd "$ARTIFACT_ROOT/kernel-src/linux-6.7.2"
[ -f .config ] || make defconfig
make olddefconfig
make -j"$(nproc)"
sudo make modules_install
sudo make install
sudo update-grub
sudo reboot
```

On reboot, if GRUB appears, choose the newly installed `6.7.2` kernel (under `Advanced options for Ubuntu`).
After login, verify:

```bash
uname -r
stat -fc %T /sys/fs/cgroup
# Expected: tmpfs (if you see cgroup2fs, v2 is still active)
```

## Step 4: Install `perf` from the Same Kernel Source

Make sure `perf` is compiled and installed correctly. If you see any build warnings, address them before continuing.

```bash
cd "$ARTIFACT_ROOT/kernel-src/linux-6.7.2/tools/perf"
make -j"$(nproc)"
sudo make install
perf --version
```

## Step 5: Configure Swap Space (60G on NVMe SSD)

Use the provided script and select your NVMe disk (for example `/dev/nvme0n1`) when prompted.

```bash
cd "$ARTIFACT_ROOT"
sudo ./make_swap.sh
swapon --show
```

## Step 6: Run Micro-Benchmark

This step compiles the micro-benchmarks, runs them, and generates their corresponding figures (figures 3-5).

```bash
cd "$ARTIFACT_ROOT/micro-benchmark"
make
make run
```

## Step 7: Build GAPBS Graphs and Place Them in `/share/graphs/`

This is a one-time prerequisite and may take hours plus significant disk space.
In this step, compile the GAPBS benchmark suite, build the required input graphs, and place them under `/share/graphs/` for the experiment scripts.

```bash
cd "$ARTIFACT_ROOT/gapbs"
make
make bench-graphs
sudo mkdir -p /share/graphs
sudo cp benchmark/graphs/*.sg benchmark/graphs/*.wsg /share/graphs/
ls -lh /share/graphs
```

At minimum, confirm these graph files exist in `/share/graphs/` before moving on:

- `twitter.sg`, `twitter.wsg`, `twitterU.sg`
- `kron.sg`, `kron.wsg`, `kronU.sg`
- `urand.sg`, `urand.wsg`, `urandU.sg`
- `web.sg`, `web.wsg`, `webU.sg`
- `road.sg`, `road.wsg`, `roadU.sg`

## Step 8: Run Baseline GAPBS Experiment (`pf-statistics`)

The run script enforces memory pressure by using cgroups to limit each
algorithm-graph pair to 30\% of its measured memory footprint, which induces
page faults and swap activity during execution.

```bash
cd "$ARTIFACT_ROOT/gapbs/experiments/pf-statistics"
./run.sh
```

## Step 9: Populate Results and Generate Plots

This step is mandatory to generate all final paper plots and reports.

```bash
cd "$ARTIFACT_ROOT/gapbs/experiments/results"
make
```

This will:
- Populate the local `results/` directory from experiment outputs
- Generate the plots/figures from the populated data (figures 6-11)

---

## Optional Extended Evaluation: NVMe-SATA Comparison Round

Run this section only if you want extra NVMe-SATA comparison data.

Warning: this is another full round of runs, is time-consuming, and does not contribute to the plots in the paper.

### Optional Step A: Patch Kernel Source with `2.patch` and Install It

`2.patch` must be applied on top of `1.patch` (cumulative patching).
Use a clean `linux-6.7.2` source tree and apply both patches in order.

```bash
cd "$ARTIFACT_ROOT/kernel-src"
rm -rf linux-6.7.2
tar -xf linux-6.7.2.tar.xz
cd linux-6.7.2
patch -p1 < "$ARTIFACT_ROOT/kernel-patches/1.patch"
patch -p1 < "$ARTIFACT_ROOT/kernel-patches/2.patch"
[ -f .config ] || make defconfig
make olddefconfig
make -j"$(nproc)"
sudo make modules_install
sudo make install
sudo update-grub
sudo reboot
```

On reboot, if GRUB appears, choose the updated kernel entry.
After login, verify the new kernel is active:

```bash
uname -r
```

### Optional Step B: Run Improved GAPBS Experiment (`pf-statistics-improved`)

As in Step 8, the run script uses cgroups to cap each algorithm-graph pair at
30\% of its memory footprint to enforce page faults and swapping while running
the improved-kernel configuration.

```bash
cd "$ARTIFACT_ROOT/gapbs/experiments/pf-statistics-improved"
./run.sh
```

### Optional Step C: Configure Swap Space (60G on SATA SSD) and Disable NVMe Swap

First disable currently active NVMe swap:

```bash
sudo swapoff -a
swapon --show
```

Then run the swap setup script again and select the SATA disk (for example `/dev/sdX`) when prompted:

```bash
cd "$ARTIFACT_ROOT"
sudo ./make_swap.sh
swapon --show
```

### Optional Step D: Run SATA GAPBS Experiment (`pf-statistics-SATA`)

```bash
cd "$ARTIFACT_ROOT/gapbs/experiments/pf-statistics-SATA"
./run.sh
```

Now the experiment results are ready.

After completing Optional Steps A-D, rerun Step 9 to regenerate outputs including NVMe-SATA comparison artifacts.
---

## Notes

- Kernel build/install steps can take substantial time depending on hardware.
- Ensure you boot into the intended kernel before each experiment phase.
- Ensure only the intended swap device is active (`swapon --show`) before running each workload set.
