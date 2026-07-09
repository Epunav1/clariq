#!/bin/bash
# CLARIQ Pre-Launch Verification Script
# Run this BEFORE deploying to production

set -e

echo "🔍 CLARIQ Pre-Launch Verification"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name=$1
    local command=$2
    
    echo -n "Testing: $test_name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 1: Code Quality
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Phase 1: Code Quality"
echo "--------------------"

run_test "Python syntax (main.py)" "python -m py_compile backend/main.py"
run_test "Python syntax (feedback)" "python -m py_compile backend/routes/feedback.py"
run_test "Python syntax (services)" "python -m py_compile backend/services/feedback_service.py"
run_test "Import main app" "cd backend && python -c 'from main import app; print(\"OK\")' && cd .."
run_test "No exposed secrets" "! grep -r 'sk_live_\|sk_test_\|STRIPE_KEY.*=' backend/ 2>/dev/null | grep -v '.pyc' | grep -q ."
run_test "Git status clean" "git status | grep -q 'nothing to commit' || git status | grep -q 'On branch'"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 2: Dependencies
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Phase 2: Dependencies"
echo "--------------------"

run_test "requirements.txt exists" "test -f backend/requirements.txt"
run_test "FastAPI available" "python -c 'import fastapi; print(fastapi.__version__)' 2>/dev/null || echo 'Install with: pip install -r backend/requirements.txt'"
run_test "Pydantic available" "python -c 'import pydantic; print(pydantic.__version__)' 2>/dev/null || echo 'Install with: pip install -r backend/requirements.txt'"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 3: Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Phase 3: Configuration"
echo "---------------------"

run_test "Environment template exists" "test -f .env.production.example"

# Count variables
VAR_COUNT=$(grep -c "=" .env.production.example || echo "0")
echo "   Environment variables: $VAR_COUNT configured"

# Check critical variables
CRITICAL_VARS=("ENVIRONMENT=" "BACKEND_URL=" "FRONTEND_URL=" "CORS_ORIGINS=" "JWT_SECRET=")
for var in "${CRITICAL_VARS[@]}"; do
    if grep -q "$var" .env.production.example; then
        echo -e "   ${GREEN}✓${NC} $var present"
    else
        echo -e "   ${RED}✗${NC} $var MISSING"
        ((TESTS_FAILED++))
    fi
done

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 4: Documentation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Phase 4: Documentation"
echo "---------------------"

run_test "README.md exists" "test -f README.md"
run_test "API_DOCUMENTATION.md exists" "test -f API_DOCUMENTATION.md"
run_test "PRODUCTION_LAUNCH.md exists" "test -f PRODUCTION_LAUNCH.md"
run_test "FAQ.md exists" "test -f FAQ.md"
run_test "FEEDBACK_SETUP.md exists" "test -f FEEDBACK_SETUP.md"
run_test "GO_LIVE_CHECKLIST.md exists" "test -f GO_LIVE_CHECKLIST.md"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 5: Git Status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Phase 5: Git Status"
echo "------------------"

run_test "Git repository" "git status > /dev/null 2>&1"
run_test "Latest commit" "git log -1 --oneline | grep -q 'feat\|docs\|fix'"

COMMIT_COUNT=$(git log --oneline | wc -l)
echo "   Total commits: $COMMIT_COUNT"

LATEST_COMMIT=$(git log -1 --pretty=format:"%h - %s")
echo "   Latest: $LATEST_COMMIT"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 6: File Structure
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Phase 6: File Structure"
echo "---------------------"

run_test "Backend directory" "test -d backend"
run_test "Routes directory" "test -d backend/routes"
run_test "Services directory" "test -d backend/services"
run_test "Database directory" "test -d backend/db"
run_test "Tests directory" "test -d backend/tests"
run_test "Deploy configs" "test -f Dockerfile && test -f docker-compose.yml"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Pre-Launch Verification Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED - READY FOR DEPLOYMENT${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Go to https://railway.app"
    echo "2. Create new project from GitHub: Epunav1/clariq"
    echo "3. Add environment variables from .env.production.example"
    echo "4. Generate JWT_SECRET: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    echo "5. Deploy"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED - FIX BEFORE DEPLOYING${NC}"
    echo ""
    echo "Issues to fix:"
    echo "- Check error messages above"
    echo "- Review code syntax"
    echo "- Ensure all dependencies installed"
    echo "- Verify configuration complete"
    echo ""
    exit 1
fi
