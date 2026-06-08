import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import google.generativeai as genai
import config
import os

print("\n--- 🔍 JARVIS API KEY DIAGNOSTICS START ---")

if not hasattr(config, "API_KEYS_POOL") or not config.API_KEYS_POOL:
    print("❌ ERROR: API_KEYS_POOL is missing or empty in config.py")
    sys.exit(1)

print(f"🔑 Found {len(config.API_KEYS_POOL)} key(s) in API_KEYS_POOL.")

for i, api_key in enumerate(config.API_KEYS_POOL):
    print(f"\n--- Checking Key #{i+1} ({api_key[:5]}...{api_key[-3:] if len(api_key) > 8 else ''}) ---")
    try:
        genai.configure(api_key=api_key)
        
        # Test the key by listing models
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                
        if available_models:
            print(f"✅ Key #{i+1} is active and functional!")
            best_model = next((m for m in available_models if "flash" in m), available_models[0])
            print(f"👉 Recommended Model: {best_model.replace('models/', '')}")
        else:
            print(f"⚠️ Key #{i+1} connected successfully, but returned NO generation models.")
            
    except Exception as e:
        print(f"❌ Key #{i+1} failed verification: {e}")

print("\n--- DIAGNOSTICS END ---")