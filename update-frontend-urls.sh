#!/bin/bash

###############################################################################
# UPDATE FRONTEND API URLS
# Update all frontend files to use new Render API URL
###############################################################################

if [ -z "$1" ]; then
    echo "Usage: ./update-frontend-urls.sh <RENDER_API_URL>"
    echo "Example: ./update-frontend-urls.sh https://clariq-api.onrender.com"
    exit 1
fi

API_URL="$1"
REPO_PATH="/Users/ebubeepuna/Downloads/clariq"

echo "🔄 UPDATING FRONTEND API URLS"
echo "============================"
echo "Old API: https://clariq-production-5974.up.railway.app"
echo "New API: $API_URL"
echo ""

# Update all HTML files
find "$REPO_PATH" -name "*.html" -type f -print0 | while IFS= read -r -d '' file; do
    if grep -q "clariq-production-5974.up.railway.app\|localhost:8000\|127.0.0.1" "$file"; then
        echo "Updating: $file"
        sed -i '' "s|https://clariq-production-5974.up.railway.app|$API_URL|g" "$file"
        sed -i '' "s|http://localhost:8000|$API_URL|g" "$file"
        sed -i '' "s|http://127.0.0.1:8000|$API_URL|g" "$file"
    fi
done

# Update all JS files
find "$REPO_PATH" -name "*.js" -type f -print0 | while IFS= read -r -d '' file; do
    if grep -q "clariq-production-5974.up.railway.app\|localhost:8000\|127.0.0.1" "$file"; then
        echo "Updating: $file"
        sed -i '' "s|https://clariq-production-5974.up.railway.app|$API_URL|g" "$file"
        sed -i '' "s|http://localhost:8000|$API_URL|g" "$file"
        sed -i '' "s|http://127.0.0.1:8000|$API_URL|g" "$file"
    fi
done

echo ""
echo "✅ Frontend URLs updated!"
echo ""
echo "📋 Files to commit:"
git -C "$REPO_PATH" diff --name-only 2>/dev/null | head -20
echo ""
echo "🔗 Next: Commit and push changes"
