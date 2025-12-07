#!/bin/bash
# Test Dremio authentication and diagnose issues

echo "========================================================================"
echo "Dremio Authentication Diagnostic"
echo "========================================================================"
echo ""

# Set default username
DREMIO_USERNAME="${DREMIO_USERNAME:-admin}"

# Check if password is set
if [ -z "$DREMIO_PASSWORD" ]; then
    echo "❌ DREMIO_PASSWORD is not set"
    echo ""
    echo "Please set it:"
    echo '  export DREMIO_USERNAME="admin"  # Or your username'
    echo '  export DREMIO_PASSWORD="your_actual_password"'
    echo ""
    exit 1
fi

echo "✓ DREMIO_USERNAME: $DREMIO_USERNAME"
echo "✓ DREMIO_PASSWORD is set (length: ${#DREMIO_PASSWORD} characters)"
echo ""

# Check Dremio is accessible
echo "Checking Dremio connectivity..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9047)

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Dremio is not accessible (HTTP $HTTP_CODE)"
    echo ""
    echo "Check if Dremio is running:"
    echo "  docker ps | grep dremio"
    exit 1
fi

echo "✓ Dremio is accessible at http://localhost:9047"
echo ""

# Test authentication
echo "Testing authentication with username: $DREMIO_USERNAME"
RESPONSE=$(curl -s -X POST http://localhost:9047/apiv2/login \
  -H "Content-Type: application/json" \
  -d "{\"userName\":\"$DREMIO_USERNAME\",\"password\":\"$DREMIO_PASSWORD\"}")

# Check if login succeeded
if echo "$RESPONSE" | grep -q "token"; then
    echo "✅ Authentication SUCCESSFUL!"
    echo ""
    TOKEN=$(echo "$RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    echo "Token received (first 20 chars): ${TOKEN:0:20}..."
    echo ""
    echo "You can now run:"
    echo "  python3 scripts/create_reflections_auto.py"
    exit 0
else
    echo "❌ Authentication FAILED"
    echo ""
    echo "Response from Dremio:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    echo ""
    echo "Common issues:"
    echo "1. Wrong password - verify in Dremio UI (http://localhost:9047)"
    echo "2. Username is not 'admin' - set DREMIO_USERNAME if different"
    echo "3. Dremio account not set up yet - create account in UI first"
    echo ""
    echo "Try logging in manually at: http://localhost:9047"
    exit 1
fi
