import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print(f"Testing Key (first 10 chars): {api_key[:10]}...")

try:
    print("\nListing available models:")
    models = genai.list_models()
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

# Try common model IDs directly
candidates = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash-exp"]
for model_id in candidates:
    print(f"\n--- Testing model: {model_id} ---")
    try:
        model = genai.GenerativeModel(model_id)
        response = model.generate_content("Say hello!")
        print(f"Success! Response: {response.text}")
        print(f"Winning Model ID: {model_id}")
    except Exception as e:
        print(f"Failed {model_id}: {e}")
