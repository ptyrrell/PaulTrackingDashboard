#!/bin/bash
# Quick deployment script for Heroku

echo "🚀 Starting deployment to Heroku..."

# Check if there are uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "📝 Committing local changes..."
    git add -A
    read -p "Enter commit message: " commit_message
    git commit -m "$commit_message"
fi

echo "📤 Pushing to GitHub..."
git push origin main

echo "☁️  Deploying to Heroku..."
git push heroku main

echo "✅ Deployment complete!"
echo "🌐 Your app is at: https://paul-tracking-dashboard.herokuapp.com"
echo "📊 Check status with: heroku logs --tail"
