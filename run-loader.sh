#!/bin/bash
# Run Zeek → OCSF → Iceberg loader with virtual environment

cd ~/zeek-iceberg-demo

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Installing dependencies..."
    ./install-dependencies.sh
fi

# Activate virtual environment and run loader
source .venv/bin/activate
python3 scripts/load_zeek_to_iceberg.py
deactivate
