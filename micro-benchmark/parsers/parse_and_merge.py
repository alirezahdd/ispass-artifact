#!/usr/bin/env python3
import os
import re
import sys


PF_LINE_RE = re.compile(
    r"^\d+\s+0x[0-9a-fA-F]+\s+0x[0-9a-fA-F]+\s+(minor|major)\b"
)
MJ_RE = re.compile(r"major_faults=(\d+)")
MN_RE = re.compile(r"minor_faults=(\d+)")


def extract_pf_lines(lines):
    """Return only structured kernel PF lines from stdout capture."""
    filtered = []
    for line in lines:
        stripped = line.strip()
        if PF_LINE_RE.match(stripped):
            filtered.append(stripped)
    return filtered


def expected_fault_type(perf_line):
    mj_match = MJ_RE.search(perf_line)
    mn_match = MN_RE.search(perf_line)
    mj = int(mj_match.group(1)) if mj_match else 0
    mn = int(mn_match.group(1)) if mn_match else 0
    if mj > 0:
        return "major"
    if mn > 0:
        return "minor"
    return None


def trace_fault_type(trace_line):
    fields = trace_line.split()
    if len(fields) < 4:
        return None
    return fields[3]


def align_perf_and_trace(perf_lines, trace_lines):
    """Greedy alignment to avoid global drift when one side has an occasional extra row."""
    i = 0
    j = 0
    aligned_perf = []
    aligned_trace = []
    dropped_perf = 0
    dropped_trace = 0

    while i < len(perf_lines) and j < len(trace_lines):
        perf_type = expected_fault_type(perf_lines[i])
        trace_type = trace_fault_type(trace_lines[j])

        if perf_type == trace_type:
            aligned_perf.append(perf_lines[i])
            aligned_trace.append(trace_lines[j])
            i += 1
            j += 1
            continue

        if j + 1 < len(trace_lines) and perf_type == trace_fault_type(trace_lines[j + 1]):
            dropped_trace += 1
            j += 1
            continue

        if i + 1 < len(perf_lines) and expected_fault_type(perf_lines[i + 1]) == trace_type:
            dropped_perf += 1
            i += 1
            continue

        aligned_perf.append(perf_lines[i])
        aligned_trace.append(trace_lines[j])
        i += 1
        j += 1

    dropped_perf += len(perf_lines) - i
    dropped_trace += len(trace_lines) - j

    return aligned_perf, aligned_trace, dropped_perf, dropped_trace

def parse_and_merge(file_name):
    """
    Parse FILE.txt and FILE-perf.txt from results-raw folder and merge them.
    
    Args:
        file_name: Base name of the files (e.g., 'rnd' or 'seq')
    """
    base_path = "../results-raw"
    txt_file = f"{base_path}/{file_name}.txt"
    perf_file = f"{base_path}/{file_name}-perf.txt"
    output_file = f"../results/{file_name}_merged.csv"
    
    # Step 1: Read FILE.txt and keep only PF records.
    print(f"Reading {txt_file}...")
    with open(txt_file, "r") as f:
        lines = f.readlines()

    filtered_lines = extract_pf_lines(lines)
    print(f"Filtered {len(filtered_lines)} structured PF lines")

    # Step 2: Read FILE-perf.txt
    print(f"Reading {perf_file}...")
    with open(perf_file, "r") as f:
        perf_lines = [line.strip() for line in f.readlines()]
    
    print(f"Read {len(perf_lines)} lines from perf file")
    
    aligned_perf, aligned_trace, dropped_perf, dropped_trace = align_perf_and_trace(perf_lines, filtered_lines)
    if dropped_perf or dropped_trace:
        print(
            "Alignment warning: "
            f"dropped_perf={dropped_perf}, dropped_trace={dropped_trace}, "
            f"aligned_rows={len(aligned_perf)}"
        )
    
    # Step 4: Merge files row-wise (perf fields first, then txt fields).
    print(f"Merging {len(aligned_perf)} rows...")
    
    # Read headers from mergfile_headers.txt
    headers_file = "mergfile_headers.txt"
    try:
        with open(headers_file, "r") as hf:
            headers = hf.read().strip()
            headers = headers.replace(" ", ",")
    except FileNotFoundError:
        print(f"Warning: {headers_file} not found, proceeding without headers")
        headers = None

    with open(output_file, "w") as f:
        if headers:
            f.write(headers + "\n")

        for perf_line, txt_line in zip(aligned_perf, aligned_trace):
            iteration_num = ""
            page_num = ""
            perf_data = perf_line

            if ": " in perf_line:
                prefix, perf_data = perf_line.split(": ", 1)
                if "Iteration #" in prefix:
                    iter_part = prefix.split("Iteration #")[1]
                    iteration_num = iter_part.split()[0]
                if "(page " in prefix:
                    page_part = prefix.split("(page ")[1]
                    page_num = page_part.rstrip("):")

            perf_data = perf_data.replace(",", "")
            txt_line = txt_line.replace(",", "")

            perf_fields = perf_data.split()
            cleaned_perf_fields = []
            for field in perf_fields:
                if field == "us":
                    continue
                if "=" in field:
                    cleaned_perf_fields.append(field.split("=")[1])
                else:
                    cleaned_perf_fields.append(field)
            perf_data = " ".join(cleaned_perf_fields)

            txt_fields = txt_line.split()

            if len(txt_fields) >= 9:
                last_9_original = [int(f) for f in txt_fields[-9:]]
                last_9 = last_9_original.copy()
                relative_values = []
                last_valid = None

                for i, val in enumerate(last_9):
                    if i == 0:
                        relative_values.append("0")
                        if val != 0:
                            last_valid = val
                    else:
                        if val == 0:
                            relative_values.append("-1")
                        else:
                            if last_valid is None:
                                relative_values.append(str(val))
                            else:
                                relative_values.append(str(val - last_valid))
                            last_valid = val

                txt_fields[-9:] = relative_values

                diff = last_9_original[-1] - last_9_original[0]
                txt_fields.append(str(diff))

                txt_line = " ".join(txt_fields)

            merged_line = f"{iteration_num},{page_num},{perf_data.replace(' ', ',')},{txt_line.replace(' ', ',')}"
            f.write(merged_line + "\n")

    print(f"Merged file saved to {output_file}")

    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_and_merge.py <file_name>")
        print("Example: python parse_and_merge.py rnd")
        sys.exit(1)
    
    file_name = sys.argv[1]
    parse_and_merge(file_name)
