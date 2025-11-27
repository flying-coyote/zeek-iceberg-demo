#!/bin/bash
# Install Python dependencies for Zeek → OCSF → Iceberg loader

echo "Installing Python dependencies in virtual environment..."
echo ""

# Check Python version
python3 --version

echo ""
echo "Creating virtual environment..."
cd ~/zeek-iceberg-demo
python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo ""
echo "Installing PyIceberg and dependencies..."
pip install pyiceberg[s3fs,hive] pyarrow pandas

echo ""
echo "✓ Dependencies installed in virtual environment!"
echo ""
echo "To use the loader script:"
echo "  1. Activate virtual environment:"
echo "     source ~/zeek-iceberg-demo/.venv/bin/activate"
echo ""
echo "  2. Run the loader:"
echo "     python3 scripts/load_zeek_to_iceberg.py"
echo ""
echo "  3. When done, deactivate:"
echo "     deactivate"
echo ""
echo "Or use the automated script:"
echo "  ./run-loader.sh"
