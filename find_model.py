import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('ANTHROPIC_API_KEY')

print("Finding available Claude models for your account...\n")

# All possible Claude models
models = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-2.1",
    "claude-2.0",
    "claude-instant-1.2"
]

working_model = None

for model in models:
    print(f"Testing {model}... ", end='', flush=True)
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 20,
                "messages": [{"role": "user", "content": "hi"}]
            },
            timeout=15
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"✅ WORKS!")
            print(f"   Response: {result['content'][0]['text']}")
            working_model = model
            break
        elif resp.status_code == 404:
            print("❌ Not found")
        elif resp.status_code == 401:
            print("❌ Unauthorized")
        else:
            print(f"❌ {resp.status_code}")
            
    except Exception as e:
        print(f"❌ {e}")

print()
if working_model:
    print(f"🎉 Found working model: {working_model}")
    print(f"\nUpdate app_new.py to use: CLAUDE_MODEL = \"{working_model}\"")
else:
    print("❌ No models found. Check your Anthropic Console:")
    print("   https://console.anthropic.com/settings/limits")
