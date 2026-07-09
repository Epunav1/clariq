#!/bin/bash

###############################################################################
# CLARIQ API TESTING SCRIPT
# Test all endpoints on deployed Render instance
###############################################################################

if [ -z "$1" ]; then
    echo "Usage: ./test-api.sh <RENDER_URL>"
    echo "Example: ./test-api.sh https://clariq-api.onrender.com"
    exit 1
fi

API_URL="$1"
PASS=0
FAIL=0

echo "🧪 CLARIQ API TEST SUITE"
echo "========================"
echo "Testing: $API_URL"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

test_endpoint() {
    local METHOD=$1
    local ENDPOINT=$2
    local EXPECTED_STATUS=$3
    local DATA=$4
    
    if [ -z "$DATA" ]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" -X "$METHOD" "$API_URL$ENDPOINT" -H "Content-Type: application/json")
    else
        RESPONSE=$(curl -s -w "\n%{http_code}" -X "$METHOD" "$API_URL$ENDPOINT" -H "Content-Type: application/json" -d "$DATA")
    fi
    
    STATUS=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$STATUS" = "$EXPECTED_STATUS" ]; then
        echo -e "${GREEN}✓${NC} $METHOD $ENDPOINT (HTTP $STATUS)"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $METHOD $ENDPOINT (Expected $EXPECTED_STATUS, got $STATUS)"
        ((FAIL++))
    fi
}

# Test core endpoints
echo "🔍 Testing Core Endpoints:"
test_endpoint "GET" "/api/health" "200"
test_endpoint "GET" "/" "200"

echo ""
echo "📊 Results:"
echo "  ✓ Passed: $PASS"
echo "  ✗ Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 All tests passed! API is live and responding."
    exit 0
else
    echo "⚠️  Some tests failed. Check the API logs."
    exit 1
fi
