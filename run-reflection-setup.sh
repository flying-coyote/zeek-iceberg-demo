#!/bin/bash
# Wrapper script to run Playwright reflection setup
# This ensures environment variables are passed correctly

echo "========================================================================"
echo "Dremio Reflection Setup - Wrapper Script"
echo "========================================================================"
echo ""

# Check if variables are set
if [ -z "$DREMIO_USERNAME" ]; then
    echo "❌ DREMIO_USERNAME not set"
    echo ""
    echo "Please set it:"
    echo '  export DREMIO_USERNAME="admin"'
    echo '  export DREMIO_PASSWORD="your_password"'
    echo '  bash run-reflection-setup.sh'
    exit 1
fi

if [ -z "$DREMIO_PASSWORD" ]; then
    echo "❌ DREMIO_PASSWORD not set"
    echo ""
    echo "Please set it:"
    echo '  export DREMIO_USERNAME="admin"'
    echo '  export DREMIO_PASSWORD="your_password"'
    echo '  bash run-reflection-setup.sh'
    exit 1
fi

echo "✓ DREMIO_USERNAME: $DREMIO_USERNAME"
echo "✓ DREMIO_PASSWORD: (set - ${#DREMIO_PASSWORD} characters)"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Run the Playwright script
echo "Starting Playwright automation..."
echo ""
python3 scripts/create_reflections_playwright_auto.py

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "========================================================================"
    echo "✅ Script completed successfully!"
    echo "========================================================================"
else
    echo "========================================================================"
    echo "⚠️  Script exited with code: $EXIT_CODE"
    echo "========================================================================"
    echo ""
    echo "If you manually created reflections, that's fine!"
    echo "Check Dremio UI to verify reflections were created."
fi

exit $EXIT_CODE
