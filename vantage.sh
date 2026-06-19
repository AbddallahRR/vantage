#!/bin/bash

#Requirement: zenity, xinput, networkmanager, pulseaudio or pipewire-pulse
#Authors: Nizam (nizam@europe.com), Lanchon (https://github.com/Lanchon)
#Patched for IdeaPad Gaming 3 (lenovo_wmi_gamezone): fan control now uses
#/sys/firmware/acpi/platform_profile instead of the legacy VPC2004/fan_mode node.

ENABLE_FAN_MODE=1

VPC="/sys/bus/platform/devices/VPC2004\:*"
PLATFORM_PROFILE="/sys/firmware/acpi/platform_profile"

touchpad_id="$(xinput list | grep "Touchpad" | cut -d '=' -f2 | awk '{print $1}')"

get_conservation_mode_status() {
    cat $VPC/conservation_mode | awk '{print ($1 == "1") ? "On" : "Off"}'
}

get_usb_charging_status() {
    cat $VPC/usb_charging | awk '{print ($1 == "1") ? "On" : "Off"}'
}

get_fan_mode_status() {
    # On gaming models (lenovo_wmi_gamezone) fan behavior is controlled via
    # the standard ACPI platform_profile interface, not VPC2004/fan_mode.
    cat "$PLATFORM_PROFILE" | awk '{
        if ($1 == "low-power") print "Low Power";
        else if ($1 == "balanced") print "Balanced";
        else if ($1 == "performance") print "Performance";
        else if ($1 == "custom") print "Custom";
        else print $1;
    }'
}

get_fn_lock_status() {
    cat $VPC/fn_lock | awk '{print ($1 == "1") ? "Off" : "On"}'
}

get_camera_status() {
    lsmod | grep -q 'uvcvideo' && echo "On" || echo "Off"
}

get_microphone_status() {
    pactl get-source-mute @DEFAULT_SOURCE@ | awk '{print ($2 == "yes") ? "Muted" : "Active"}'
}

get_touchpad_status() {
    xinput --list-props "$touchpad_id" | grep "Device Enabled" | cut -d ':' -f2 | awk '{print ($1 == "1") ? "On" : "Off"}'
}

get_wifi_status() {
    nmcli radio wifi | awk '{print ($1 == "enabled") ? "On" : "Off"}'
}

SUBMENU_ON="Activate"
SUBMENU_OFF="Deactivate"

show_submenu() {
    local title="$1"
    local status="$2"
    zenity --list --title "$title" --text "Status: $status" --column "Menu" "${@:3}"
}

show_submenu_on_off() {
    show_submenu "$@" "$SUBMENU_ON" "$SUBMENU_OFF"
}

main() {
    while :; do
        local options=()
        test -f $VPC/conservation_mode && options+=("Conservation Mode" "$(get_conservation_mode_status)")
        test -f $VPC/usb_charging && options+=("Always-On USB" "$(get_usb_charging_status)")
        test -f "$PLATFORM_PROFILE" && test "$ENABLE_FAN_MODE" = 1 && options+=("Fan Mode" "$(get_fan_mode_status)")
        test -f $VPC/fn_lock && options+=("FN Lock" "$(get_fn_lock_status)")
        modinfo -n uvcvideo >/dev/null && options+=("Camera" "$(get_camera_status)")
        which pactl >/dev/null && options+=("Microphone" "$(get_microphone_status)")
        test -n "$touchpad_id" && options+=("Touchpad" "$(get_touchpad_status)")
        which nmcli >/dev/null && options+=("WiFi" "$(get_wifi_status)")

        local menu="$(zenity --list --title "Lenovo Vantage" --text "Select function:" --column "Function" --column "Status" "${options[@]}" --height 340 --width 350)"
        case "$menu" in
            "Conservation Mode")
                local submenu="$(show_submenu_on_off "Conservation Mode" "$(get_conservation_mode_status)")"
                case "$submenu" in
                    "$SUBMENU_ON") echo "1" | pkexec tee $VPC/conservation_mode ;;
                    "$SUBMENU_OFF") echo "0" | pkexec tee $VPC/conservation_mode ;;
                esac
                ;;
            "Always-On USB")
                local submenu="$(show_submenu_on_off "Always-On USB" "$(get_usb_charging_status)")"
                case "$submenu" in
                    "$SUBMENU_ON") echo "1" | pkexec tee $VPC/usb_charging ;;
                    "$SUBMENU_OFF") echo "0" | pkexec tee $VPC/usb_charging ;;
                esac
                ;;
            "Fan Mode")
                local submenu="$(show_submenu "Fan Mode" "$(get_fan_mode_status)" --height 250 --width 300 \
                    "Low Power" \
                    "Balanced" \
                    "Performance" \
                )"
                case "$submenu" in
                    "Low Power") echo "low-power" | pkexec tee "$PLATFORM_PROFILE" ;;
                    "Balanced") echo "balanced" | pkexec tee "$PLATFORM_PROFILE" ;;
                    "Performance") echo "performance" | pkexec tee "$PLATFORM_PROFILE" ;;
                esac
                ;;
            "FN Lock")
                local submenu="$(show_submenu_on_off "FN Lock" "$(get_fn_lock_status)")"
                case "$submenu" in
                    "$SUBMENU_ON") echo "0" | pkexec tee $VPC/fn_lock ;;
                    "$SUBMENU_OFF") echo "1" | pkexec tee $VPC/fn_lock ;;
                esac
                ;;
            "Camera")
                local submenu="$(show_submenu_on_off "Camera" "$(get_camera_status)")"
                case "$submenu" in
                    "$SUBMENU_ON") pkexec modprobe uvcvideo ;;
                    "$SUBMENU_OFF") pkexec modprobe -r uvcvideo ;;
                esac
                ;;
            "Microphone")
                local submenu="$(show_submenu "Microphone" "$(get_microphone_status)" \
                    "Mute" \
                    "Unmute" \
                )"
                case "$submenu" in
                    "Mute") pactl set-source-mute @DEFAULT_SOURCE@ 1 ;;
                    "Unmute") pactl set-source-mute @DEFAULT_SOURCE@ 0 ;;
                esac
                ;;
            "Touchpad")
                local submenu="$(show_submenu_on_off "Touchpad" "$(get_touchpad_status)")"
                case "$submenu" in
                    "$SUBMENU_ON") xinput enable "$touchpad_id" ;;
                    "$SUBMENU_OFF") xinput disable "$touchpad_id" ;;
                esac
                ;;
            "WiFi")
                local submenu="$(show_submenu_on_off "WiFi" "$(get_wifi_status)")"
                case "$submenu" in
                    "$SUBMENU_ON") nmcli radio wifi on ;;
                    "$SUBMENU_OFF") nmcli radio wifi off ;;
                esac
                ;;
            *)
                break
                ;;
        esac
    done
}

main "$@"
