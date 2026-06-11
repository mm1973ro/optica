#!/bin/bash
# Optica Installation Script

set -e

echo "======================================"
echo "  Optica - Instalare Sistem"
echo "======================================"
echo ""

# Check Python version
echo "[1/4] Verificare Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nu este instalat!"
    echo "   Instalează Python 3.8+ de la python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "   ✓ Python $PYTHON_VERSION găsit"

# Check pip
echo ""
echo "[2/4] Verificare pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 nu este instalat!"
    exit 1
fi
echo "   ✓ pip3 găsit"

# Create virtual environment (optional but recommended)
echo ""
echo "[3/4] Creare mediu virtual (opțional)..."
read -p "   Dorești să creezi un mediu virtual? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "   ✓ Mediu virtual creeat"
    else
        echo "   ℹ Mediu virtual există deja"
    fi

    echo "   Activare mediu virtual..."
    source venv/bin/activate
    echo "   ✓ Mediu virtual activat"
fi

# Install dependencies
echo ""
echo "[4/4] Instalare dependențe..."
pip3 install -r requirements.txt

echo ""
echo "======================================"
echo "  ✓ Instalare completă!"
echo "======================================"
echo ""
echo "Pentru a rula aplicația:"
echo "  python3 optica.py"
echo ""
echo "Pentru a rula testele (fără cameră):"
echo "  python3 test_detector.py"
echo ""
echo "Pentru ajutor:"
echo "  python3 optica.py --help"
echo ""
echo "Consultă QUICK_START.md pentru ghid rapid!"
echo ""
