#!/bin/bash

# Setup script for WTfffmpeg development in Codespaces
# This script ensures all dependencies and tools are installed

set -e

echo "🔧 Setting up WTfffmpeg development environment..."
echo "================================================"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --user -r requirements.txt

# Install development tools
echo "🛠️  Installing development tools..."
python3 -m pip install --user -r requirements-dev.txt

# Make scripts executable
echo "🔐 Setting script permissions..."
chmod +x ./*.sh

# Verify installation
echo "✅ Verifying setup..."
python3 -c "import flask, google.cloud.storage; print('✓ Core dependencies installed')"
python3 -c "import flake8, yaml; print('✓ Dev tools installed')"

echo ""
echo "🎉 Setup complete! You can now:"
echo "  • Run verification: ./verify.sh"
echo "  • Test configuration: python3 test_config.py"
echo "  • Build Docker image: docker build -t wtfffmpeg-test ."
echo "  • Lint code: python3 -m flake8 app.py"
echo ""