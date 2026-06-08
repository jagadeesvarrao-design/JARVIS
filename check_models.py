import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load your API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: API Key not found in .env file")
else:
    print(f"🔑 Authenticating with key: {api_key[:5]}...{api_key[-3:]}")
    genai.configure(api_key=api_key)

    print("\n🔍 Scanning for available models...")
    try:
        # Ask Google for the list
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - ✅ FOUND: {m.name}")
                available_models.append(m.name)
        
        if not available_models:
            print("\n❌ No models found. Check if 'Generative AI API' is enabled in Google Cloud Console.")
        else:
            print("\n👇 SOLUTION: Copy the exact name below into your config.py:")
            # We prefer flash or pro models
            best_model = next((m for m in available_models if "flash" in m), available_models[0])
            print(f'AI_MODEL = "{best_model.replace("models/", "")}"')

    except Exception as e:
        print(f"❌ Error: {e}")