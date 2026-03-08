#!/bin/bash

# Get swap partitions and extract device names
SWAP_DEVICES=$(swapon --show=NAME --noheadings | sed 's|/dev/||' | tr '\n' '|' | sed 's/|$//')

if [ -z "$SWAP_DEVICES" ]; then
  echo "No swap partitions found. Exiting."
  exit 1
fi

while true; do
  grep -E "$SWAP_DEVICES" /proc/diskstats >> "$1"
  grep -E "swap_ra|pgmajfault" /proc/vmstat >> "$1"
  sleep 0.5
done
