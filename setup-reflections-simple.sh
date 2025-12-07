#!/bin/bash
# Simple one-step reflection setup with better error handling

set -e  # Exit on error

echo "========================================================================"
echo "Dremio Reflection Setup - Simple Version"
echo "========================================================================"
echo ""

# Step 1: Check credentials
DREMIO_USERNAME="${DREMIO_USERNAME:-admin}"

if [ -z "$DREMIO_PASSWORD" ]; then
    echo "❌ Error: DREMIO_PASSWORD not set"
    echo ""
    echo "Please run:"
    echo '  export DREMIO_USERNAME="admin"  # Or your username'
    echo '  export DREMIO_PASSWORD="your_password"'
    echo "  bash setup-reflections-simple.sh"
    echo ""
    exit 1
fi

echo "✓ Username: $DREMIO_USERNAME"
echo "✓ Password is set (${#DREMIO_PASSWORD} characters)"
echo ""

# Step 2: Check Dremio
echo "Checking Dremio..."
if ! docker ps | grep -q zeek-demo-dremio; then
    echo "❌ Error: Dremio container not running"
    echo ""
    echo "Start it with:"
    echo "  docker-compose up -d dremio"
    exit 1
fi

echo "✓ Dremio is running"
echo ""

# Step 3: Check connectivity
echo "Testing Dremio connectivity..."
if ! curl -s -f http://localhost:9047 > /dev/null; then
    echo "❌ Error: Cannot connect to Dremio"
    echo ""
    echo "Check logs:"
    echo "  docker logs zeek-demo-dremio --tail 50"
    exit 1
fi

echo "✓ Dremio is accessible"
echo ""

# Step 4: Test authentication
echo "Testing authentication with username: $DREMIO_USERNAME"
AUTH_RESPONSE=$(curl -s -X POST http://localhost:9047/apiv2/login \
  -H "Content-Type: application/json" \
  -d "{\"userName\":\"$DREMIO_USERNAME\",\"password\":\"$DREMIO_PASSWORD\"}")

if ! echo "$AUTH_RESPONSE" | grep -q "token"; then
    echo "❌ Authentication failed"
    echo ""
    echo "Response:"
    echo "$AUTH_RESPONSE"
    echo ""
    echo "Please check your password by logging in at:"
    echo "  http://localhost:9047"
    echo ""
    exit 1
fi

echo "✓ Authentication successful"
echo ""

# Step 5: Activate venv and run Python script
echo "Activating virtual environment..."
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo ""
    echo "Create it with:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install requests pandas pyarrow boto3"
    exit 1
fi

source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Check dependencies
echo "Checking Python dependencies..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing requests..."
    pip install requests --quiet
fi

echo "✓ Dependencies ready"
echo ""

# Step 6: Run reflection setup
echo "========================================================================"
echo "Running reflection setup script..."
echo "========================================================================"
echo ""

python3 scripts/create_reflections_auto.py

EXIT_CODE=$?

echo ""
echo "========================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ SUCCESS!"
    echo "========================================================================"
    echo ""
    echo "Reflections have been created."
    echo ""
    echo "Next steps:"
    echo "1. Wait 2-5 minutes for reflections to build"
    echo "2. Check status:"
    echo "   python3 scripts/check_reflections_auto.py"
    echo "3. Test queries in Dremio to see 10-100x speedup!"
else
    echo "❌ FAILED"
    echo "========================================================================"
    echo ""
    echo "The script encountered an error."
    echo "See FIX-REFLECTION-ERRORS.md for troubleshooting."
    echo ""
    echo "Or try manual setup in Dremio UI (5 minutes):"
    echo "  http://localhost:9047"
fi
echo ""

exit $EXIT_CODE
