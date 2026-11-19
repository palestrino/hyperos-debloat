#!/bin/bash
# HyperOS 1 Debloat — launcher para Linux e macOS
# Uso: ./iniciar.sh   (ou: python3 hyperos_debloat.py)
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 não encontrado."
    echo "  Debian/Ubuntu: sudo apt install python3 python3-tk adb"
    echo "  Arch:          sudo pacman -S python python-tk android-tools"
    echo "  Fedora:        sudo dnf install python3 python3-tkinter android-tools"
    echo "  macOS:         brew install python android-platform-tools"
    exit 1
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Falta o Tkinter (interface gráfica do Python)."
    echo "  Debian/Ubuntu: sudo apt install python3-tk"
    echo "  Arch:          sudo pacman -S python-tk"
    echo "  Fedora:        sudo dnf install python3-tkinter"
    echo "  macOS:         brew install python-tk@3.12"
    exit 1
fi

if ! command -v adb >/dev/null 2>&1 && [ ! -x ./platform-tools/adb ]; then
    echo "Aviso: 'adb' não encontrado no PATH nem em ./platform-tools/"
    echo "  Debian/Ubuntu: sudo apt install adb"
    echo "  Arch:          sudo pacman -S android-tools"
    echo "  macOS:         brew install android-platform-tools"
    echo "  Ou baixe o platform-tools no site do Google e extraia ao lado do script."
    echo "O programa vai abrir mesmo assim — use o botão 'Baixar ADB' nele."
fi

exec python3 hyperos_debloat.py
