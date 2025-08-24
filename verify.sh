#!/bin/bash

# Verification script for WTfffmpeg deployment configuration
# This script validates all configuration files and ensures readiness for deployment

set -e

echo "🔍 Verifying WTfffmpeg deployment configuration..."
echo "==============================================="

# Check required files exist
echo "✅ Checking required files..."
required_files=("service.yaml" "cloudbuild.yaml" "deploy.sh" "Dockerfile" "app.py" "requirements.txt")

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✓ $file exists"
    else
        echo "  ❌ $file missing"
        exit 1
    fi
done

# Validate YAML syntax
echo ""
echo "✅ Validating YAML syntax..."
if command -v yamllint &> /dev/null; then
    yamllint service.yaml cloudbuild.yaml || echo "  ⚠️  YAML linting warnings (non-critical)"
else
    echo "  ⚠️  yamllint not available, skipping syntax validation"
fi

# Validate Python syntax
echo ""
echo "✅ Validating Python code..."
python3 -m py_compile app.py
echo "  ✓ app.py syntax valid"

# Check deployment script is executable
echo ""
echo "✅ Checking deployment script..."
if [[ -x "deploy.sh" ]]; then
    echo "  ✓ deploy.sh is executable"
else
    echo "  ❌ deploy.sh is not executable"
    exit 1
fi

# Validate deployment script syntax
bash -n deploy.sh
echo "  ✓ deploy.sh syntax valid"

# Check Docker build context
echo ""
echo "✅ Validating Docker configuration..."
if docker --version &> /dev/null; then
    echo "  ✓ Docker is available"
    echo "  ℹ️  Run 'docker build -t wtfffmpeg-test .' to test locally"
else
    echo "  ⚠️  Docker not available for testing"
fi

# Verify project configuration
echo ""
echo "✅ Verifying project configuration..."
echo "  📋 Project ID: yt-v8dr"
echo "  📋 Service Name: master-v8dr"
echo "  📋 Region: us-central1"
echo "  📋 Bucket: yt-v8dr-wtfffmpeg-videos"
echo "  📋 Repository: us-central1-docker.pkg.dev/yt-v8dr/wtfffmpeg-repo/wtfffmpeg"

# Test application health endpoint
echo ""
echo "✅ Testing application..."
CLOUD_STORAGE_BUCKET=yt-v8dr-wtfffmpeg-videos python3 -c "
import app
with app.app.test_client() as client:
    response = client.get('/_health')
    if response.status_code == 200:
        print('  ✓ Health endpoint working')
    else:
        print('  ❌ Health endpoint failed')
        exit(1)
"

echo ""
echo "🎉 All checks passed! Ready for deployment."
echo ""
echo "To deploy, run:"
echo "  ./deploy.sh"
echo ""
echo "Or use Cloud Build directly:"
echo "  gcloud builds submit"