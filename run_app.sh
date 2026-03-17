#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set environment variables for network
export PYTHONHTTPSVERIFY=1
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")

# Check if in venv
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Virtual environment not activated!"
    exit 1
fi

# Verify packages
echo "Checking packages..."
python3 -c "import flask, anthropic, httpx; print('✅ All packages available')" || exit 1

# Run app
echo "Starting app..."
python3 app.py
