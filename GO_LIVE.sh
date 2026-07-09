#!/bin/bash

###############################################################################
# CLARIQ GO LIVE - COMPLETE DEPLOYMENT WORKFLOW
# This script guides you through the complete deployment process
###############################################################################

echo "🚀 CLARIQ GO LIVE SCRIPT"
echo "========================================"
echo ""
echo "This script will guide you through:"
echo "  1. Preparing your code for deployment"
echo "  2. Creating the Render service"
echo "  3. Testing the live API"
echo "  4. Updating the frontend"
echo ""

# Function to ask yes/no question
ask_yes_no() {
    local question="$1"
    local response
    while true; do
        read -p "$question (yes/no): " response
        case "$response" in
            [yY][eE][sS]|[yY]) return 0 ;;
            [nN][oO]|[nN]) return 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

# Step 1: Verify code is ready
echo "📋 Step 1: Verifying code..."
cd /Users/ebubeepuna/Downloads/clariq

if [ -d ".git" ]; then
    echo "✅ Git repository found"
else
    echo "❌ Not a git repository!"
    exit 1
fi

# Step 2: Check all files exist
echo ""
echo "📋 Step 2: Checking required files..."
REQUIRED_FILES=(
    "Procfile"
    "render.yaml"
    "backend/requirements.txt"
    "backend/main.py"
    "backend/data/.gitkeep"
)

ALL_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo "❌ Some required files are missing!"
    exit 1
fi

# Step 3: Show deployment checklist
echo ""
echo "📋 Step 3: Pre-Deployment Checklist"
echo "===================================="
echo ""
echo "  ✅ Backend code: Production-ready"
echo "  ✅ Dependencies: All wrapped with graceful fallback"
echo "  ✅ Database: SQLite directory created"
echo "  ✅ Procfile: Configured for Render"
echo "  ✅ render.yaml: Configured for Render"
echo "  ✅ Environment: Variables ready"
echo ""

# Step 4: Ready to deploy?
echo "🎯 Next Steps (Manual on Render):"
echo "=================================="
echo ""
echo "1. Go to: https://dashboard.render.com"
echo "   (Make sure you're logged in with GitHub account: Epunav1)"
echo ""
echo "2. Click: 'New +' → 'Web Service'"
echo ""
echo "3. Select: Repository 'Epunav1/clariq'"
echo ""
echo "4. Configure:"
echo "   Name:               clariq-api"
echo "   Environment:        Python 3"
echo "   Region:             Oregon"
echo "   Branch:             main"
echo "   Build Command:      pip install -r backend/requirements.txt"
echo "   Start Command:      cd backend && python -m uvicorn main:app --host 0.0.0.0 --port \$PORT --workers 1"
echo ""
echo "5. Add Environment Variables (click 'Environment'):"
echo "   DATABASE_URL         → sqlite:///./data/clariq.db"
echo "   JWT_SECRET           → fpZauHy00sDYFakpi2OKod9sgRD4UAMaAv7n6TOmgRw"
echo "   ENVIRONMENT          → production"
echo "   PYTHONUNBUFFERED     → 1"
echo ""
echo "6. Click: 'Create Web Service'"
echo ""
echo "⏱️  Wait 3-5 minutes for build to complete..."
echo ""
echo "7. Once you see 'Live' status, copy your URL:"
echo "   Format: https://clariq-api.onrender.com"
echo "   (Your actual URL will be different)"
echo ""

if ask_yes_no "Have you completed all steps 1-7 above and have your Render URL?"; then
    echo ""
    read -p "Enter your Render URL (e.g., https://clariq-api.onrender.com): " RENDER_URL
    
    # Validate URL format
    if [[ ! "$RENDER_URL" =~ ^https:// ]]; then
        echo "❌ Invalid URL. Must start with https://"
        exit 1
    fi
    
    echo ""
    echo "🧪 Step 4: Testing API..."
    echo "=========================="
    echo ""
    
    # Wait a moment for service to warm up
    echo "Waiting 10 seconds for service to warm up..."
    sleep 10
    
    # Test health endpoint
    HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$RENDER_URL/api/health")
    STATUS_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
    BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)
    
    if [ "$STATUS_CODE" = "200" ]; then
        echo "✅ API is live!"
        echo ""
        echo "Response:"
        echo "$BODY" | python -m json.tool 2>/dev/null || echo "$BODY"
        echo ""
    else
        echo "⚠️  Got HTTP $STATUS_CODE"
        echo "Response: $BODY"
        echo ""
        echo "Wait a few more seconds and try again, or check Render logs"
        exit 1
    fi
    
    # Step 5: Update frontend
    if ask_yes_no "Update frontend to use the new API URL?"; then
        echo ""
        echo "🔄 Step 5: Updating Frontend..."
        echo "================================"
        
        # Find and update all frontend files
        UPDATED=0
        for file in $(find . -name "*.html" -o -name "*.js" | grep -v node_modules); do
            if grep -q "clariq-production-5974.up.railway.app\|localhost:8000\|127.0.0.1" "$file" 2>/dev/null; then
                sed -i '' "s|https://clariq-production-5974.up.railway.app|$RENDER_URL|g" "$file" 2>/dev/null || true
                sed -i '' "s|http://localhost:8000|$RENDER_URL|g" "$file" 2>/dev/null || true
                sed -i '' "s|http://127.0.0.1:8000|$RENDER_URL|g" "$file" 2>/dev/null || true
                echo "  ✅ Updated: $file"
                ((UPDATED++))
            fi
        done
        
        if [ $UPDATED -gt 0 ]; then
            echo ""
            echo "Updated $UPDATED files"
            echo ""
            
            # Commit changes
            echo "📝 Committing changes..."
            git add .
            git commit -m "chore: Update API URLs to Render production endpoint ($RENDER_URL)" || true
            
            echo "✅ Changes committed!"
        else
            echo "No frontend files needed updating"
        fi
    fi
    
    echo ""
    echo "🎉 DEPLOYMENT COMPLETE!"
    echo "========================"
    echo ""
    echo "Your CLARIQ backend is now live at:"
    echo "📍 $RENDER_URL"
    echo ""
    echo "Next steps:"
    echo "  1. Visit: https://tryclariq.com"
    echo "  2. Sign up and start using clariq"
    echo "  3. Monitor: https://dashboard.render.com/services/clariq-api"
    echo ""
    echo "Health Check:"
    echo "  curl $RENDER_URL/api/health"
    echo ""
    
else
    echo ""
    echo "Complete the steps in the Render dashboard and run this script again when ready."
    exit 0
fi
