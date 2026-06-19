#!/bin/bash
# Privileged helper for Lenovo Vantage
# Called by vantage.py via sudo (NOPASSWD configured in sudoers.d/vantage)

VPC=$(ls -d /sys/bus/platform/devices/VPC2004:* 2>/dev/null | head -1)
PLATFORM_PROFILE="/sys/firmware/acpi/platform_profile"

case "$1" in
    conservation-on)  echo 1 | tee "$VPC/conservation_mode" ;;
    conservation-off) echo 0 | tee "$VPC/conservation_mode" ;;
    usb-on)           echo 1 | tee "$VPC/usb_charging" ;;
    usb-off)          echo 0 | tee "$VPC/usb_charging" ;;
    fn-on)            echo 0 | tee "$VPC/fn_lock" ;;
    fn-off)           echo 1 | tee "$VPC/fn_lock" ;;
    fan)              echo "$2" | tee "$PLATFORM_PROFILE" ;;
    camera-on)        modprobe uvcvideo ;;
    camera-off)       modprobe -r uvcvideo ;;
    *)
        echo "Usage: $0 {conservation-on|off|usb-on|off|fn-on|off|fan <mode>|camera-on|off}" >&2
        exit 1 ;;
esac
