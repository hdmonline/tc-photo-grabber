#!/bin/bash
# Installation and verification script for tc-photos-grabber-py

set -e

echo "=========================================="
echo "TC Photos Grabber - Installation Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version OK: $python_version"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check for exiftool
echo "Checking for exiftool..."
if command -v exiftool &> /dev/null; then
    exiftool_version=$(exiftool -ver)
    echo "✅ exiftool found: version $exiftool_version"
else
    echo "⚠️  exiftool not found (optional but recommended)"
    echo "   Install with: brew install exiftool (macOS) or apt-get install libimage-exiftool-perl (Linux)"
fi
echo ""

# Check if .env file exists
echo "Checking configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "   Copy .env.example to .env and configure your credentials:"
    echo "   cp .env.example .env"
    echo "   nano .env"
else
    echo "✅ .env file found"
fi
echo ""

# Check if Docker is available
echo "Checking Docker availability..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo "✅ Docker found: $docker_version"
else
    echo "⚠️  Docker not found (required for containerized deployment)"
fi
echo ""

# Check if kubectl is available
echo "Checking Kubernetes tools..."
if command -v kubectl &> /dev/null; then
    kubectl_version=$(kubectl version --client --short 2>/dev/null | head -n1)
    echo "✅ kubectl found: $kubectl_version"
else
    echo "⚠️  kubectl not found (required for Kubernetes deployment)"
fi
echo ""

echo "=========================================="
echo "Installation Summary"
echo "=========================================="
echo ""
echo "✅ Python environment ready"
echo "✅ Dependencies installed"
echo ""
echo "Next steps:"
echo "1. Configure credentials in .env file"
echo "2. Test with: python -m src --dry-run"
echo "3. Run once: python -m src"
echo "4. Run scheduled: python -m src --cron --schedule daily"
echo ""
echo "For more information, see:"
echo "  - README.md for full documentation"
echo "  - QUICKSTART.md for quick start guide"
echo "  - make help for available commands"
echo ""
echo "=========================================="
