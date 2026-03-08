#!/bin/bash

set -e

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

echo "=========================================="
echo "Available Disks and Partitions:"
echo "=========================================="
lsblk -o NAME,SIZE,TYPE,FSTYPE | grep -v loop

echo ""
echo "=========================================="
read -p "Enter the disk name (e.g., sda, sdb): " DISK

# Validate disk input
if [[ ! -b "/dev/$DISK" ]]; then
   echo "Error: /dev/$DISK is not a valid block device"
   exit 1
fi

echo ""
echo "Checking for existing 60G partitions on /dev/$DISK..."

# Check if there's already a 60G partition
EXISTING_60G=$(lsblk -n -o NAME,SIZE "/dev/$DISK" | grep -i "60G" || echo "")

if [[ -n "$EXISTING_60G" ]]; then
   echo "Found existing 60G partition(s):"
   echo "$EXISTING_60G"
   read -p "A 60G partition already exists. Continue anyway? (yes/no): " CONTINUE
   if [[ "$CONTINUE" != "yes" ]]; then
      echo "Aborted."
      exit 0
   fi
fi

echo ""
echo "Current partitions on /dev/$DISK:"
lsblk "/dev/$DISK"

echo ""
read -p "Do you want to create a 60G swap partition on /dev/$DISK? (yes/no): " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
   echo "Aborted."
   exit 0
fi

# Create partition using parted (assuming unpartitioned space is available)
echo ""
echo "Creating 60G partition on /dev/$DISK..."

# Find the next available partition number
LAST_PARTITION=$(lsblk -n -o NAME "/dev/$DISK" | tail -1 | sed "s/[^0-9]*//g")
if [[ -z "$LAST_PARTITION" ]]; then
   NEXT_PARTITION=1
else
   NEXT_PARTITION=$((LAST_PARTITION + 1))
fi

PARTITION_NAME="${DISK}${NEXT_PARTITION}"

# Get the start position for the new partition (in MB)
START_POSITION=$(parted -s "/dev/$DISK" unit MB print free | grep "Free Space" | tail -1 | awk '{print $1}' | sed 's/MB//')

if [[ -z "$START_POSITION" || "$START_POSITION" == "0" ]]; then
   echo "Error: No free space available on /dev/$DISK"
   exit 1
fi

# Create the partition
parted -s "/dev/$DISK" mkpart primary linux-swap ${START_POSITION}MB $((START_POSITION + 60000))MB

echo "Partition created: /dev/$PARTITION_NAME"
echo ""
echo "Formatting partition as swap..."
mkswap "/dev/$PARTITION_NAME"

echo ""
echo "=========================================="
echo "Success! Swap partition created:"
echo "Device: /dev/$PARTITION_NAME"
echo "Size: 60G"
echo "=========================================="
echo ""
echo "To enable the swap space, run:"
echo "  swapon /dev/$PARTITION_NAME"
echo ""
echo "To make it permanent, add the following line to /etc/fstab:"
echo "  /dev/$PARTITION_NAME none swap sw 0 0"
