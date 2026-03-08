#!/usr/bin/env python3
"""
Parser for /proc/[pid]/stat files.
Compares two snapshots and calculates differences for applicable fields.
"""

import sys


def parse_stat_line(line):
    """Parse a single line from /proc/[pid]/stat file."""
    # Remove trailing whitespace and split
    fields = line.strip().split()
    
    # Handle the special case where comm (process name) might contain spaces
    # The comm field is enclosed in parentheses
    if len(fields) >= 3 and fields[1].startswith('(') and not fields[1].endswith(')'):
        # Find the closing parenthesis
        comm_parts = [fields[1]]
        i = 2
        while i < len(fields) and not fields[i-1].endswith(')'):
            comm_parts.append(fields[i])
            i += 1
        
        # Reconstruct the fields list
        comm = ' '.join(comm_parts)
        fields = [fields[0], comm] + fields[i:]
    
    return fields

def get_field_definitions():
    """Define the fields in /proc/[pid]/stat and whether they are diffable."""
    return [
        ("pid", False, "Process ID"),
        ("comm", False, "Process name (in parentheses)"),
        ("state", False, "Process state"),
        ("ppid", False, "Parent process ID"),
        ("pgrp", False, "Process group ID"),
        ("session", False, "Session ID"),
        ("tty_nr", False, "TTY number"),
        ("tpgid", False, "TTY process group ID"),
        ("flags", False, "Process flags"),
        ("minflt", True, "Minor page faults"),
        ("cminflt", True, "Minor page faults by children"),
        ("majflt", True, "Major page faults"),
        ("cmajflt", True, "Major page faults by children"),
        ("utime", True, "User mode time (clock ticks)"),
        ("stime", True, "System mode time (clock ticks)"),
        ("cutime", True, "User mode time of children"),
        ("cstime", True, "System mode time of children"),
        ("priority", False, "Process priority"),
        ("nice", False, "Nice value"),
        ("num_threads", False, "Number of threads"),
        ("itrealvalue", False, "Interval timer real value"),
        ("starttime", False, "Start time since boot (clock ticks)"),
        ("vsize", False, "Virtual memory size in bytes"),
        ("rss", False, "Resident set size in pages"),
        ("rsslim", False, "RSS limit"),
        ("startcode", False, "Start of code segment"),
        ("endcode", False, "End of code segment"),
        ("startstack", False, "Start of stack"),
        ("kstkesp", False, "Kernel stack pointer"),
        ("kstkeip", False, "Kernel instruction pointer"),
        ("signal", False, "Pending signals bitmap"),
        ("blocked", False, "Blocked signals bitmap"),
        ("sigignore", False, "Ignored signals bitmap"),
        ("sigcatch", False, "Caught signals bitmap"),
        ("wchan", False, "Wait channel"),
        ("nswap", True, "Number of pages swapped"),
        ("cnswap", True, "Number of pages swapped by children"),
        ("exit_signal", False, "Exit signal"),
        ("processor", False, "CPU number"),
        ("rt_priority", False, "Real-time priority"),
        ("policy", False, "Scheduling policy"),
        ("delayacct_blkio_ticks", True, "Block I/O delay time"),
        ("guest_time", True, "Guest time"),
        ("cguest_time", True, "Guest time of children"),
        ("start_data", False, "Start of data segment"),
        ("end_data", False, "End of data segment"),
        ("start_brk", False, "Start of heap"),
        ("arg_start", False, "Start of command line arguments"),
        ("arg_end", False, "End of command line arguments"),
        ("env_start", False, "Start of environment variables"),
        ("env_end", False, "End of environment variables"),
        ("exit_code", False, "Exit code")
    ]

def parse_and_compare(begin_file, end_file):
    """Parse two stat files and compare diffable fields."""
    
    # Read the files
    with open(begin_file, 'r') as f:
        begin_line = f.read().strip()
    
    with open(end_file, 'r') as f:
        end_line = f.read().strip()
    
    # Parse the lines
    begin_fields = parse_stat_line(begin_line)
    end_fields = parse_stat_line(end_line)
    
    # Get field definitions
    field_defs = get_field_definitions()
    
    # Ensure we have enough fields
    max_fields = min(len(begin_fields), len(end_fields), len(field_defs))
  
    field_width, value_width = 25, 25
    print(f"{'Field_Name':<{field_width}} {'Value':>{value_width}}")
    print("-" * (field_width + value_width +1))
    
    for i in range(max_fields):
        field_name, is_diffable, description = field_defs[i]
        if is_diffable:
            try:
                begin_val = int(begin_fields[i])
                end_val = int(end_fields[i])
                diff = end_val - begin_val
                print(f"{field_name:<{field_width}} {str(diff):>{value_width}}")
            except (ValueError, IndexError):
                print(f"{field_name:<{field_width}} {end_fields[i]:>{value_width}}")
        else:
            # For non-diffable fields, just show the current value
            try:
                print(f"{field_name:<{field_width}} {end_fields[i]:>{value_width}}")
            except IndexError:
                print

def main():
    """Main function to run the parser."""
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
