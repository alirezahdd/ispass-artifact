#!/usr/bin/env python3
"""
Parser for /proc/[pid]/sched files.
Compares two snapshots and calculates differences for applicable fields.
Outputs in the simple format: Field_Name \t Value
"""

import re
import sys

def parse_sched_file(file_path):
    """Parse a scheduler statistics file."""
    data = {}
    process_info = {}
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Parse header line to get process info
    header_line = lines[0].strip()
    # Example: cc (1641544, #threads: 16)
    header_match = re.match(r'(.+) \((\d+), #threads: (\d+)\)', header_line)
    if header_match:
        process_info['process_name'] = header_match.group(1)
        process_info['pid'] = header_match.group(2)
        process_info['threads'] = header_match.group(3)
    
    # Parse the statistics lines
    for line in lines[2:]:  # Skip header and separator line
        line = line.strip()
        if not line or line.startswith('---') or '=' in line:
            continue
            
        # Handle lines with key-value pairs separated by ':'
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value_str = parts[1].strip()
                
                # Try to convert to number (int or float)
                try:
                    if '.' in value_str:
                        value = float(value_str)
                    else:
                        value = int(value_str)
                except ValueError:
                    value = value_str
                
                data[key] = value
    
    return process_info, data

def get_diffable_fields():
    """Define which fields should be diffed vs shown as current values."""
    # Fields that represent cumulative counters or runtime values that should be diffed
    diffable_fields = {
        'se.sum_exec_runtime',
        'se.nr_migrations', 
        'sum_sleep_runtime',
        'sum_block_runtime',
        'wait_sum',
        'wait_count',
        'iowait_sum',
        'iowait_count',
        'nr_migrations_cold',
        'nr_failed_migrations_affine',
        'nr_failed_migrations_running',
        'nr_failed_migrations_hot',
        'nr_forced_migrations',
        'nr_wakeups',
        'nr_wakeups_sync',
        'nr_wakeups_migrate',
        'nr_wakeups_local',
        'nr_wakeups_remote',
        'nr_wakeups_affine',
        'nr_wakeups_affine_attempts',
        'nr_wakeups_passive',
        'nr_wakeups_idle',
        'nr_switches',
        'nr_voluntary_switches',
        'nr_involuntary_switches',
        'numa_pages_migrated',
        'total_numa_faults'
    }
    
    return diffable_fields

def parse_and_compare(begin_file, end_file):
    """Parse two scheduler files and compare diffable fields."""
    
    # Parse both files
    begin_info, begin_data = parse_sched_file(begin_file)
    end_info, end_data = parse_sched_file(end_file)
    
    # Get list of diffable fields
    diffable_fields = get_diffable_fields()

    field_width, value_width = 30, 25
    # Print header
    print(f"{'Field_Name':<{field_width}} {'Value':>{value_width}}")
    print("-" * (field_width + value_width +1))
    

    # Process info (non-diffable)
    print(f"{'process name':<{field_width}} {end_info.get('process_name', 'N/A'):>{value_width}}")
    print(f"{'pid':<{field_width}} {end_info.get('pid', 'N/A'):>{value_width}}")
    print(f"{'threads':<{field_width}} {end_info.get('threads', 'N/A'):>{value_width}}")
    
    
    # Get all unique field names from both datasets
    all_fields = sorted(set(begin_data.keys()) | set(end_data.keys()))
    
    # Process each field
    for field in all_fields:
        begin_val = begin_data.get(field, 0)
        end_val = end_data.get(field, 0)
        field_width, value_width = 30, 25

        if field in diffable_fields:
            # Calculate difference for diffable fields
            try:
                if isinstance(begin_val, (int, float)) and isinstance(end_val, (int, float)):
                    diff = end_val - begin_val
                    print(f"{field:<{field_width}} {str(diff):>{value_width}}")
                else:
                    print(f"{field:<{field_width}} {str(end_val):>{value_width}}")
            except (TypeError, ValueError):
                print(f"{field:<{field_width}} {str(end_val):>{value_width}}")
        else:
            # Show current value for non-diffable fields
            print(f"{field:<{field_width}} {str(end_val):>{value_width}}")

def main():
    """Main function to run the scheduler parser."""
    if len(sys.argv) >= 3:
      begin_file = sys.argv[1]
      end_file = sys.argv[2]
    else:
      print("Usage: sched_parser.py <begin_file> <end_file>")
      sys.exit(1)
    
    try:
        parse_and_compare(begin_file, end_file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
