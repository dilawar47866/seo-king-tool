import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('ANTHROPIC_API_KEY')

print(f"Testing with key: {API_KEY[:40]}...\n")

try:
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-3-opus-20240229",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Say 'API key works!'"}]
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        result = resp.json()
        print("✅ SUCCESS!")
        print(f"Response: {result['content'][0]['text']}\n")
        print("🎉 Your API key is working! Ready to run the app!")
    else:
        print(f"❌ Status: {resp.status_code}")
        print(f"Error: {resp.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
