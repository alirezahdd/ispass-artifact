#!/usr/bin/env python3
import sys
from collections import Counter

def parse_and_merge(file_name):
    """
    Parse FILE.txt and FILE-perf.txt from results-raw folder and merge them.
    
    Args:
        file_name: Base name of the files (e.g., 'rnd' or 'seq')
    """
    base_path = "../results-raw"
    txt_file = f"{base_path}/{file_name}.txt"
    perf_file = f"{base_path}/{file_name}-perf.txt"
    intermediate_file = f"{base_path}/{file_name}_filtered.txt"
    output_file = f"../results/{file_name}_merged.csv"
    
    # Step 1: Read FILE.txt and find dominant value in second column
    print(f"Reading {txt_file}...")
    with open(txt_file, 'r') as f:
        lines = f.readlines()
    
    # Extract second column values
    second_column_values = []
    for line in lines:
        fields = line.strip().split()
        if len(fields) >= 2:
            second_column_values.append(fields[1])
    
    # Find dominant value
    counter = Counter(second_column_values)
    dominant_value, dominant_count = counter.most_common(1)[0]
    print(f"Dominant value in second column: '{dominant_value}' (appears {dominant_count} times)")
    
    # Step 2: Filter lines with dominant value in second column
    filtered_lines = []
    for line in lines:
        fields = line.strip().split()
        if len(fields) >= 2 and fields[1] == dominant_value:
            filtered_lines.append(line.strip())
    
    print(f"Filtered {len(filtered_lines)} lines with dominant value")
    
    # Save intermediate file
    with open(intermediate_file, 'w') as f:
        for line in filtered_lines:
            f.write(line + '\n')
    print(f"Saved filtered lines to {intermediate_file}")
    
    # Step 3: Read FILE-perf.txt
    print(f"Reading {perf_file}...")
    with open(perf_file, 'r') as f:
        perf_lines = [line.strip() for line in f.readlines()]
    
    print(f"Read {len(perf_lines)} lines from perf file")
    
    # Step 4: Verify line counts match
    if len(filtered_lines) != len(perf_lines):
        print(f"WARNING: Line count mismatch! Filtered: {len(filtered_lines)}, Perf: {len(perf_lines)}")
        print("Proceeding with minimum of both...")
        min_lines = min(len(filtered_lines), len(perf_lines))
        filtered_lines = filtered_lines[:min_lines]
        perf_lines = perf_lines[:min_lines]
    
    # Step 5: Merge files row-wise (perf fields first, then txt fields)
    print(f"Merging {len(perf_lines)} rows...")
    
    # Read headers from mergfile_headers.txt
    headers_file = "mergfile_headers.txt"
    try:
        with open(headers_file, 'r') as hf:
            headers = hf.read().strip()
            # Convert space-delimited headers to comma-delimited
            headers = headers.replace(' ', ',')
    except FileNotFoundError:
        print(f"Warning: {headers_file} not found, proceeding without headers")
        headers = None
    
    with open(output_file, 'w') as f:
        # Write headers if available
        if headers:
            f.write(headers + '\n')
        
        for perf_line, txt_line in zip(perf_lines, filtered_lines):
            # Extract iteration number and page number from perf_line
            # The format is: "Iteration #N (page M): field1=value1, field2=value2, ..."
            iteration_num = ""
            page_num = ""
            perf_data = perf_line
            
            if ': ' in perf_line:
                prefix, perf_data = perf_line.split(': ', 1)
                # Extract iteration number
                if 'Iteration #' in prefix:
                    iter_part = prefix.split('Iteration #')[1]
                    iteration_num = iter_part.split()[0]
                # Extract page number
                if '(page ' in prefix:
                    page_part = prefix.split('(page ')[1]
                    page_num = page_part.rstrip('):')
            
            # Replace commas with spaces in perf_data and txt_line, then replace spaces with commas
            perf_data = perf_data.replace(',', '')
            txt_line = txt_line.replace(',', '')
            
            # Remove 'us' from perf_data and extract values from field=value pairs
            perf_fields = perf_data.split()
            cleaned_perf_fields = []
            for field in perf_fields:
                if field == 'us':
                    continue
                # Extract value from field=value format
                if '=' in field:
                    cleaned_perf_fields.append(field.split('=')[1])
                else:
                    cleaned_perf_fields.append(field)
            perf_data = ' '.join(cleaned_perf_fields)
            
            # Split txt_line into fields (last 9 fields from the raw data)
            txt_fields = txt_line.split()
            
            # Convert last 9 fields to relative values
            if len(txt_fields) >= 9:
                # Get the last 9 fields as integers (store original values)
                last_9_original = [int(f) for f in txt_fields[-9:]]
                last_9 = last_9_original.copy()
                relative_values = []
                last_valid = None
                
                for i, val in enumerate(last_9):
                    if i == 0:
                        # First field: set to 0
                        relative_values.append('0')
                        if val != 0:
                            last_valid = val
                    else:
                        if val == 0:
                            # Zero value: mark as invalid (-1)
                            relative_values.append('-1')
                        else:
                            if last_valid is None:
                                # No valid previous value, use absolute
                                relative_values.append(str(val))
                            else:
                                # Calculate relative to last valid non-zero
                                relative_values.append(str(val - last_valid))
                            last_valid = val
                
                # Replace last 9 fields with relative values
                txt_fields[-9:] = relative_values
                
                # Add difference between last field and 9th from last (using original values)
                diff = last_9_original[-1] - last_9_original[0]
                txt_fields.append(str(diff))
                
                txt_line = ' '.join(txt_fields)
            
            # Merge: iteration, page, perf data, then txt data (all comma-delimited)
            merged_line = f"{iteration_num},{page_num},{perf_data.replace(' ', ',')},{txt_line.replace(' ', ',')}"
            f.write(merged_line + '\n')
    
    print(f"Merged file saved to {output_file}")
    
    # Remove intermediate file
    import os
    if os.path.exists(intermediate_file):
        os.remove(intermediate_file)
        print(f"Removed intermediate file {intermediate_file}")
    
    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_and_merge.py <file_name>")
        print("Example: python parse_and_merge.py rnd")
        sys.exit(1)
    
    file_name = sys.argv[1]
    parse_and_merge(file_name)
