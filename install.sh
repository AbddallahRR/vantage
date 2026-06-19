#!/bin/bash

# Function to detect package manager
detect_package_manager() {
    if command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v apt &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v zypper &> /dev/null; then
        echo "zypper"
    else
        echo "unknown"
    fi
}

# check for the distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    distro=$ID_LIKE

    # Some distros like Fedora doesn't have "ID_LIKE" in their /etc/os-release file, sadly
    if [ -z "$distro" ]; then
        distro=$ID
    fi
fi

case $distro in
  # Now Vantage can be installed on Cachy OS, ArcoLinux... you name it!
  "arch")
    echo "Installing on Arch Linux or derivative"
    pacman -Qi zenity xorg-xinput networkmanager python-gobject &> /dev/null || sudo pacman -S zenity xorg-xinput networkmanager python-gobject
    ;;

  # Now Vantage can not only be installed on Ubuntu or POP OS but also Kubuntu, KDE Neon, Xubuntu...
  "debian")
    echo "Installing on Debian or derivative"
    dpkg -s zenity xinput python3-gobject gir1.2-gtk-3.0 &> /dev/null || sudo apt install zenity xinput python3-gobject gir1.2-gtk-3.0
    ;;
  
  # Entry for Linux Mint 21.3 Edge
  "ubuntu debian")
    echo "Installing on Linux Mint Edge"
    dpkg -s zenity xinput python3-gobject gir1.2-gtk-3.0 &> /dev/null || sudo apt install zenity xinput python3-gobject gir1.2-gtk-3.0
    ;;  

  "fedora")
    echo "Installing on Fedora"
    rpm -q zenity xinput NetworkManager pipewire-pulseaudio python3-gobject &> /dev/null || sudo dnf install zenity xinput NetworkManager pipewire-pulseaudio python3-gobject
    ;;

  "opensuse-tumbleweed")
    echo "Installing on OpenSuse"
    rpm -q zenity xinput NetworkManager pipewire-pulseaudio python3-gobject &> /dev/null || sudo zypper install zenity xinput NetworkManager pipewire-pulseaudio python3-gobject
    ;;

  *)
    echo "Unknown Distro, attempting package manager detection..."
    package_manager=$(detect_package_manager)
    
    case $package_manager in
        "pacman")
            echo "Detected pacman package manager"
            pacman -Qi zenity xorg-xinput networkmanager python-gobject &> /dev/null || sudo pacman -S zenity xorg-xinput networkmanager python-gobject
            ;;
        "apt")
            echo "Detected apt package manager"
            dpkg -s zenity xinput python3-gobject gir1.2-gtk-3.0 &> /dev/null || sudo apt install zenity xinput python3-gobject gir1.2-gtk-3.0
            ;;
        "dnf")
            echo "Detected dnf package manager"
            rpm -q zenity xinput NetworkManager pipewire-pulseaudio python3-gobject &> /dev/null || sudo dnf install zenity xinput NetworkManager pipewire-pulseaudio python3-gobject
            ;;
        "zypper")
            echo "Detected zypper package manager"
            rpm -q zenity xinput NetworkManager pipewire-pulseaudio python3-gobject &> /dev/null || sudo zypper install zenity xinput NetworkManager pipewire-pulseaudio python3-gobject
            ;;
        *)
            echo "Unable to detect compatible package manager, exiting."
            exit 1
            ;;
    esac
    ;;
esac

echo "Requirements are installed"
