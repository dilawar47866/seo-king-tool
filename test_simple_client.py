"""Test Anthropic with simplest possible client"""
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"Testing with key: {api_key[:30]}...\n")

try:
    # Use default client (no custom HTTP settings)
    print("Creating simple client...")
    client = anthropic.Anthropic(api_key=api_key)
    
    print("Making API call...")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": "Write a 2 sentence intro about phones"}]
    )
    
    print("✅ SUCCESS!")
    print(f"\nResponse:\n{response.content[0].text}")
    
except anthropic.APIConnectionError as e:
    print(f"❌ Connection Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check internet connection")
    print("2. Disable VPN if active")
    print("3. Check firewall settings")
    print("4. Try from different network (mobile hotspot)")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")

