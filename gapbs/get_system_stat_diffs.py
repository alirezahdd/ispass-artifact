#!/usr/bin/env python3
"""
Parser for system-wide /proc/stat files.
Compares two snapshots and calculates differences for applicable fields.
Outputs in the simple format: Field_Name \t Value
"""

import sys
import re


def parse_cpu_line(line):
    """Parse a CPU line from /proc/stat."""
    parts = line.strip().split()
    cpu_name = parts[0]
    values = [int(x) for x in parts[1:]]
    
    # CPU fields: user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
    field_names = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice']
    
    cpu_data = {}
    for i, field in enumerate(field_names):
        if i < len(values):
            cpu_data[f"{cpu_name}_{field}"] = values[i]
        else:
            cpu_data[f"{cpu_name}_{field}"] = 0
    
    return cpu_data


def parse_stat_file(file_path):
    """Parse a system-wide /proc/stat file."""
    data = {}
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if not parts:
                continue
            
            key = parts[0]
            
            if key.startswith('cpu'):
                # Handle CPU lines
                cpu_data = parse_cpu_line(line)
                data.update(cpu_data)
            
            elif key == 'intr':
                # Interrupt count - first number is total interrupts
                if len(parts) >= 2:
                    data['interrupts_total'] = int(parts[1])
                    # Store specific interrupt counts for commonly monitored ones
                    for i, val in enumerate(parts[2:50]):  # Limit to first 48 specific interrupts
                        if val != '0':
                            data[f'interrupt_{i}'] = int(val)
            
            elif key == 'ctxt':
                # Context switches
                if len(parts) >= 2:
                    data['context_switches'] = int(parts[1])
            
            elif key == 'btime':
                # Boot time (not diffable)
                if len(parts) >= 2:
                    data['boot_time'] = int(parts[1])
            
            elif key == 'processes':
                # Total processes created since boot
                if len(parts) >= 2:
                    data['processes_total'] = int(parts[1])
            
            elif key == 'procs_running':
                # Currently running processes (not diffable)
                if len(parts) >= 2:
                    data['procs_running'] = int(parts[1])
            
            elif key == 'procs_blocked':
                # Currently blocked processes (not diffable)
                if len(parts) >= 2:
                    data['procs_blocked'] = int(parts[1])
            
            elif key == 'softirq':
                # Software interrupts
                if len(parts) >= 2:
                    data['softirq_total'] = int(parts[1])
                    # Specific softirq types
                    softirq_names = ['hi', 'timer', 'net_tx', 'net_rx', 'block', 'irq_poll', 
                                   'tasklet', 'sched', 'hrtimer', 'rcu']
                    for i, name in enumerate(softirq_names):
                        if i + 2 < len(parts):
                            data[f'softirq_{name}'] = int(parts[i + 2])
    
    return data


def get_diffable_fields():
    """Define which fields should be diffed vs shown as current values."""
    # Fields that represent cumulative counters that should be diffed
    diffable_fields = {
        # CPU time fields (all CPUs)
        'cpu_user', 'cpu_nice', 'cpu_system', 'cpu_idle', 'cpu_iowait', 
        'cpu_irq', 'cpu_softirq', 'cpu_steal', 'cpu_guest', 'cpu_guest_nice',
        
        # Per-CPU fields (will be matched with regex)
        'context_switches',
        'processes_total',
        'interrupts_total',
        'softirq_total'
    }
    
    # Add per-CPU fields dynamically
    for i in range(64):  # Support up to 64 CPUs
        cpu_name = f'cpu{i}'
        for field in ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice']:
            diffable_fields.add(f'{cpu_name}_{field}')
    
    # Add interrupt fields
    for i in range(50):
        diffable_fields.add(f'interrupt_{i}')
    
    # Add softirq fields
    softirq_names = ['hi', 'timer', 'net_tx', 'net_rx', 'block', 'irq_poll', 
                    'tasklet', 'sched', 'hrtimer', 'rcu']
    for name in softirq_names:
        diffable_fields.add(f'softirq_{name}')
    
    return diffable_fields


def parse_and_compare(begin_file, end_file):
    """Parse two stat files and compare diffable fields."""
    
    # Parse both files
    begin_data = parse_stat_file(begin_file)
    end_data = parse_stat_file(end_file)
    
    # Get list of diffable fields
    diffable_fields = get_diffable_fields()
    
    field_width, value_width = 30, 25
    # Print header
    print(f"{'Field_Name':<{field_width}} {'Value':>{value_width}}")
    print("-" * (field_width + value_width + 1))
    
    # Get all unique field names from both datasets, sorted for consistent output
    all_fields = sorted(set(begin_data.keys()) | set(end_data.keys()))
    
    # Process each field
    for field in all_fields:
        begin_val = begin_data.get(field, 0)
        end_val = end_data.get(field, 0)
        
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
    """Main function to run the system stat parser."""
    if len(sys.argv) >= 3:
        begin_file = sys.argv[1]
        end_file = sys.argv[2]
    else:
        print("Usage: get_system_stat_diffs.py <begin_file> <end_file>")
        sys.exit(1)
    
    try:
        parse_and_compare(begin_file, end_file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
