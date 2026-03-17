#!/bin/bash
set -e

echo "🔧 Setting up virtual environment..."

# Clean up
deactivate 2>/dev/null || true
rm -rf venv

# Create venv
python3 -m venv venv
source venv/bin/activate

echo "✅ Virtual environment created"

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install packages
echo "📦 Installing packages..."
pip install Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Flask-Login==0.6.3 \
    Flask-Bcrypt==1.0.1 Flask-Mail==0.9.1 anthropic==0.84.0 \
    python-dotenv==1.0.0 requests==2.31.0 beautifulsoup4==4.12.3 \
    lxml==5.1.0 validators==0.22.0 markdown==3.5.2 gunicorn==21.2.0 \
    psycopg2-binary==2.9.9 httpx==0.28.1 certifi

echo "✅ All packages installed"

# Test imports
python3 << 'PYEOF'
import flask
import anthropic
print(f"✅ Flask {flask.__version__}")
print(f"✅ Anthropic {anthropic.__version__}")
PYEOF

# Test API
echo ""
echo "Testing Anthropic API..."
python3 << 'PYEOF'
import os
from dotenv import load_dotenv
import anthropic
import httpx

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')

if not api_key or 'your-' in api_key:
    print("⚠️  API key not configured in .env")
else:
    try:
        client = anthropic.Anthropic(
            api_key=api_key,
            timeout=httpx.Timeout(90.0, connect=30.0)
        )
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "test"}]
        )
        print(f"✅ API works! Response: {response.content[0].text[:50]}")
    except Exception as e:
        print(f"❌ API error: {e}")
PYEOF

echo ""
echo "🎉 Setup complete!"
echo "Run: source venv/bin/activate && python3 app.py"
