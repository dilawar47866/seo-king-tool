#!/bin/bash

echo "🔧 Fixing SEO King Tool..."

# 1. Clean up
echo "1️⃣ Cleaning up old files..."
rm -f seoking.db seoking.db-journal
rm -rf __pycache__

# 2. Reinstall packages
echo "2️⃣ Reinstalling packages..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 3. Create database
echo "3️⃣ Creating database..."
python3 << 'PYCODE'
from app import app, db
with app.app_context():
    db.create_all()
    print("✅ Database created!")
PYCODE

# 4. Check API key
echo "4️⃣ Checking API key..."
if grep -q "your-anthropic-key-here" .env; then
    echo "⚠️  WARNING: Update your Anthropic API key in .env file!"
else
    echo "✅ API key seems configured"
fi

echo ""
echo "✅ Setup complete! Run: python3 app.py"
