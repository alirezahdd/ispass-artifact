#!/usr/bin/env python3
import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def percentile(values, p):
    if not values:
        return None
    if p <= 0:
        return min(values)
    if p >= 100:
        return max(values)

    ordered = sorted(values)
    k = (len(ordered) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return ordered[int(k)]
    d0 = ordered[f] * (c - k)
    d1 = ordered[c] * (k - f)
    return d0 + d1


def load_rows(csv_file):
    rows = []
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["iter"] = int(row["iter"])
            row["page_index"] = int(row["page_index"])
            row["access_time"] = float(row["access_time"])
            row["mj_fault"] = int(row["mj_fault"])
            row["min_fault"] = int(row["min_fault"])
            row["reclaim"] = int(row["reclaim"])
            row["total_time"] = float(row["total_time"])
            rows.append(row)
    return rows


def extract_series(rows, metric):
    iterations = [r["iter"] for r in rows]
    values = [r[metric] for r in rows]

    minor_vals = [r[metric] for r in rows if r["min_fault"] > 0 and r["mj_fault"] == 0]
    major_no_reclaim_vals = [r[metric] for r in rows if r["mj_fault"] > 0 and r["reclaim"] == 0]
    reclaim_vals = [r[metric] for r in rows if r["reclaim"] > 0]

    return {
        "iterations": iterations,
        "values": values,
        "minor": minor_vals,
        "major_no_reclaim": major_no_reclaim_vals,
        "reclaim": reclaim_vals,
    }


def summarize(name, series, cap_p):
    minor = series["minor"]
    major_no_reclaim = series["major_no_reclaim"]
    reclaim = series["reclaim"]

    print(f"\n{name}:")
    print(f"  Minor count: {len(minor)}")
    print(f"  Major-no-reclaim count: {len(major_no_reclaim)}")
    print(f"  Reclaim count: {len(reclaim)}")

    if minor:
        print(f"  Minor min/max: {min(minor):.2f} / {max(minor):.2f}")
    if major_no_reclaim:
        print(
            f"  Major(no reclaim) min/max/p{cap_p:.0f}: "
            f"{min(major_no_reclaim):.2f} / {max(major_no_reclaim):.2f} / {percentile(major_no_reclaim, cap_p):.2f}"
        )
    if reclaim:
        print(f"  Reclaim min/max: {min(reclaim):.2f} / {max(reclaim):.2f}")


def main():
    parser = argparse.ArgumentParser(description="Access-time plot with percentile-capped bands")
    parser.add_argument("--metric", choices=["access_time", "total_time"], default="access_time")
    parser.add_argument("--cap-percentile", type=float, default=99.0)
    parser.add_argument("--results-dir", default="../results")
    parser.add_argument("--output", default="../figures/fig_3.pdf")
    parser.add_argument("--show-stats", action="store_true", help="Print category statistics")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    seq_rows = load_rows(results_dir / "seq_merged.csv")
    seq8_rows = load_rows(results_dir / "seq_8page_merged.csv")
    rnd_rows = load_rows(results_dir / "rnd_merged.csv")

    seq = extract_series(seq_rows, args.metric)
    seq8 = extract_series(seq8_rows, args.metric)
    rnd = extract_series(rnd_rows, args.metric)

    if args.show_stats:
        print(f"\nAccess Time Statistics ({args.metric})")
        summarize("seq", seq, args.cap_percentile)
        summarize("seq_8page", seq8, args.cap_percentile)
        summarize("rnd", rnd, args.cap_percentile)

    all_minor = seq["minor"] + seq8["minor"] + rnd["minor"]
    all_major_nr = seq["major_no_reclaim"] + seq8["major_no_reclaim"] + rnd["major_no_reclaim"]
    all_reclaim = seq["reclaim"] + seq8["reclaim"] + rnd["reclaim"]

    min_minor = min(all_minor) if all_minor else None
    cap_minor = percentile(all_minor, args.cap_percentile) if all_minor else None
    min_major = min(all_major_nr) if all_major_nr else None
    cap_major = percentile(all_major_nr, args.cap_percentile) if all_major_nr else None
    min_reclaim = min(all_reclaim) if all_reclaim else None

    plt.figure(figsize=(3.5, 2.8))

    plt.plot(
        seq["iterations"],
        seq["values"],
        marker="o",
        linestyle="",
        markersize=3,
        label="seq",
        color="#2E86AB",
        zorder=1,
        markeredgewidth=0,
    )

    plt.plot(
        rnd["iterations"],
        rnd["values"],
        marker="^",
        linestyle="",
        markersize=3,
        label="rnd",
        color="#A23B72",
        zorder=2,
        markeredgewidth=0,
    )

    seq8_iter_scaled = [i * 8 for i in seq8["iterations"]]
    plt.plot(
        seq8_iter_scaled,
        seq8["values"],
        marker="s",
        linestyle="",
        markersize=2,
        label="seq_8page",
        color="#F18F01",
        zorder=3,
        markeredgewidth=0,
    )

    if min_minor is not None and cap_minor is not None:
        plt.axhspan(min_minor, cap_minor, alpha=0.1, color="green", zorder=0)
    if min_major is not None and cap_major is not None:
        plt.axhspan(min_major, cap_major, alpha=0.1, color="orange", zorder=0)
    ymax = max(seq["values"] + seq8["values"] + rnd["values"])
    if min_reclaim is not None:
        plt.axhspan(min_reclaim, ymax, alpha=0.1, color="red", zorder=0)

    # Add area labels on the right side of the plot.
    x_right = max(seq["iterations"] + rnd["iterations"] + seq8_iter_scaled)
    x_label = x_right * 1.07
    if min_minor is not None and cap_minor is not None:
        y_minor = (min_minor + cap_minor) / 2.0
        plt.text(
            x_label,
            y_minor,
            f"Minor\n({min_minor:.0f}-{cap_minor:.0f})",
            fontsize=6,
            verticalalignment="center",
            color="darkgreen",
            weight="bold",
        )
    if min_major is not None and cap_major is not None:
        y_major = (min_major + cap_major) / 2.0
        plt.text(
            x_label,
            y_major,
            f"Major\n({min_major:.0f}-{cap_major:.0f})",
            fontsize=6,
            verticalalignment="center",
            color="darkorange",
            weight="bold",
        )
    if min_reclaim is not None:
        y_reclaim = min_reclaim * 1.15
        plt.text(
            x_label,
            y_reclaim,
            f"Reclaim\n({min_reclaim:.0f}+)",
            fontsize=6,
            verticalalignment="center",
            color="darkred",
            weight="bold",
        )

    plt.xlabel("Iteration Number", fontsize=9)
    plt.ylabel("Fault Handling Time (us)", fontsize=9)
    plt.yscale("log")
    plt.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=3, frameon=True)
    plt.grid(True, alpha=0.3)
    plt.tick_params(labelsize=8)
    plt.tight_layout()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, bbox_inches="tight")
    print(f"Saved plot: {output}")


if __name__ == "__main__":
    main()
