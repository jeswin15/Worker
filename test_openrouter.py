import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-lite-001")

print(f"Testing Key (first 10 chars): {key[:10]}...")
print(f"Testing Model: {model}")

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://holocene.vc", # Optional
        "X-Title": "Holocene Sourcing Agent", # Optional
    },
    json={
        "model": model,
        "messages": [
            {"role": "user", "content": "Say hello!"}
        ]
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
