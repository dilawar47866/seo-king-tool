import os
import requests

# Direct API key (replace with yours)
API_KEY = "sk-ant-api03-wfE9zhuIgRSDiXDWReUa4vt10x_VJRLQVcxgIdlO5RLTm7aqNkM3gIXOjq6KT0AxsEF3wQjACrWl-sBQ5cgcIg"

models = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229", 
    "claude-3-5-sonnet-20240620",
    "claude-3-haiku-20240307"
]

print("Testing which Claude models work with your API key...\n")

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
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "hi"}]
            },
            timeout=15
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"✅ WORKS!")
            print(f"   Response: {result['content'][0]['text']}")
            print(f"\n🎯 This model works! Update app to use: {model}\n")
            break
        else:
            print(f"❌ {resp.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\nTest complete!")
