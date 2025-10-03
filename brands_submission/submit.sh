#!/bin/bash

# HomeBrainz Brands Submission Script
# This script helps submit the HomeBrainz brand to the Home Assistant brands repository

set -e

echo "🎨 HomeBrainz Brands Submission Helper"
echo "======================================"

# Check if brands repo is cloned
if [ ! -d "../brands" ]; then
    echo "📥 Cloning Home Assistant brands repository..."
    cd ..
    git clone https://github.com/home-assistant/brands.git
    cd brands
    
    echo "🔄 Adding your fork as origin..."
    echo "Please enter your GitHub username:"
    read github_username
    git remote set-url origin https://github.com/$github_username/brands.git
    cd ../ha-homebrainz-integration/brands_submission
else
    echo "✅ Brands repository found"
fi

# Create branch
echo "🌿 Creating new branch..."
cd ../brands
git checkout main
git pull upstream main 2>/dev/null || git pull origin main
git checkout -b add-homebrainz-brand

# Copy files
echo "📁 Copying brand files..."
cp ../ha-homebrainz-integration/brands_submission/custom_integrations/homebrainz.json custom_integrations/
cp -r ../ha-homebrainz-integration/brands_submission/custom_integrations/homebrainz custom_integrations/

# Commit
echo "💾 Committing changes..."
git add custom_integrations/homebrainz.json
git add custom_integrations/homebrainz/
git commit -m "Add HomeBrainz custom integration brand

- Add HomeBrainz Clock integration logos
- 512x512 and 1024x1024 PNG formats  
- Clean brain and house icon design
- Domain: homebrainz"

echo "🚀 Ready to push! Run:"
echo "cd ../brands"
echo "git push origin add-homebrainz-brand"
echo ""
echo "Then create a PR at https://github.com/home-assistant/brands/compare"