#!/bin/bash
# Verification script for app.yaml + Asset Bundle migration

set -e

echo "🔍 Verifying migration to app.yaml + Asset Bundle..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if we're in the app directory
if [ ! -f "databricks.yml" ]; then
    echo -e "${RED}Error: Must run from app/ directory${NC}"
    exit 1
fi

echo "📁 Checking for required files..."

# Check app.yaml
if [ -f "app.yaml" ]; then
    echo -e "${GREEN}✓${NC} app.yaml exists"
else
    echo -e "${RED}✗${NC} app.yaml missing"
    exit 1
fi

# Check databricks.yml
if [ -f "databricks.yml" ]; then
    echo -e "${GREEN}✓${NC} databricks.yml exists"
else
    echo -e "${RED}✗${NC} databricks.yml missing"
    exit 1
fi

# Check build-frontend.sh
if [ -f "build-frontend.sh" ]; then
    echo -e "${GREEN}✓${NC} build-frontend.sh exists"
    if [ -x "build-frontend.sh" ]; then
        echo -e "${GREEN}✓${NC} build-frontend.sh is executable"
    else
        echo -e "${RED}✗${NC} build-frontend.sh not executable"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} build-frontend.sh missing"
    exit 1
fi

echo ""
echo "🔧 Checking backend modifications..."

# Check for aiofiles in requirements.txt
if grep -q "aiofiles" backend/requirements.txt; then
    echo -e "${GREEN}✓${NC} aiofiles dependency added"
else
    echo -e "${RED}✗${NC} aiofiles dependency missing"
    exit 1
fi

# Check for StaticFiles in main.py
if grep -q "StaticFiles" backend/main.py; then
    echo -e "${GREEN}✓${NC} StaticFiles import added to backend"
else
    echo -e "${RED}✗${NC} StaticFiles import missing"
    exit 1
fi

# Check for frontend path mounting
if grep -q "frontend_build_dir" backend/main.py; then
    echo -e "${GREEN}✓${NC} Frontend build directory configured"
else
    echo -e "${RED}✗${NC} Frontend build directory not configured"
    exit 1
fi

echo ""
echo "📋 Checking databricks.yml format..."

# Check for Asset Bundle structure
if grep -q "bundle:" databricks.yml; then
    echo -e "${GREEN}✓${NC} Asset Bundle format detected"
else
    echo -e "${YELLOW}⚠${NC}  Asset Bundle format not detected (may be old format)"
fi

if grep -q "resources:" databricks.yml && grep -q "apps:" databricks.yml; then
    echo -e "${GREEN}✓${NC} resources.apps structure present"
else
    echo -e "${RED}✗${NC} resources.apps structure missing"
    exit 1
fi

if grep -q "targets:" databricks.yml; then
    echo -e "${GREEN}✓${NC} Target environments configured"
else
    echo -e "${YELLOW}⚠${NC}  No target environments found"
fi

echo ""
echo "📝 Checking app.yaml structure..."

# Check for command
if grep -q "command:" app.yaml; then
    echo -e "${GREEN}✓${NC} Command defined"
else
    echo -e "${RED}✗${NC} Command not defined"
    exit 1
fi

# Check for uvicorn
if grep -q "uvicorn" app.yaml; then
    echo -e "${GREEN}✓${NC} uvicorn command found"
else
    echo -e "${RED}✗${NC} uvicorn command not found"
    exit 1
fi

# Check for environment variables
if grep -q "env:" app.yaml; then
    echo -e "${GREEN}✓${NC} Environment variables defined"
else
    echo -e "${RED}✗${NC} Environment variables not defined"
    exit 1
fi

# Check for secret references
if grep -q "valueFrom:" app.yaml && grep -q "secretRef:" app.yaml; then
    echo -e "${GREEN}✓${NC} Secret references configured"
else
    echo -e "${RED}✗${NC} Secret references not configured"
    exit 1
fi

echo ""
echo "🔐 Checking environment configuration..."

# Check for required environment variables
required_vars=("DATABRICKS_HOST" "DATABRICKS_TOKEN" "DATABRICKS_HTTP_PATH" "FRONTEND_BUILD_DIR")
for var in "${required_vars[@]}"; do
    if grep -q "$var" app.yaml; then
        echo -e "${GREEN}✓${NC} $var configured"
    else
        echo -e "${YELLOW}⚠${NC}  $var not found (may be optional)"
    fi
done

echo ""
echo "📚 Verifying documentation updates..."

docs_updated=true

# Check DEPLOYMENT.md
if grep -q "bundle deploy" docs/DEPLOYMENT.md 2>/dev/null; then
    echo -e "${GREEN}✓${NC} DEPLOYMENT.md updated"
else
    echo -e "${YELLOW}⚠${NC}  DEPLOYMENT.md may need updates"
    docs_updated=false
fi

# Check README.md
if grep -q "build-frontend.sh" README.md 2>/dev/null; then
    echo -e "${GREEN}✓${NC} README.md updated"
else
    echo -e "${YELLOW}⚠${NC}  README.md may need updates"
    docs_updated=false
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$docs_updated" = true ]; then
    echo -e "${GREEN}✅ Migration verification complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Build frontend: ./build-frontend.sh"
    echo "2. Validate bundle: databricks bundle validate -t dev"
    echo "3. Deploy: databricks bundle deploy -t dev"
else
    echo -e "${YELLOW}⚠️  Migration mostly complete, but check documentation${NC}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
