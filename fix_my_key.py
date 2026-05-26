import google.generativeai as genai
import config
import os

print("\n--- 🔍 DIAGNOSTIC START ---")

# 1. Check API Key presence
if not config.API_KEY:
    print("❌ ERROR: API Key is missing in config.py")
    exit()
print(f"🔑 Key found: {config.API_KEY[:5]}... (Hidden)")

# 2. Configure
try:
    genai.configure(api_key=config.API_KEY)
    print("✅ Library configured.")
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    exit()

# 3. Test Connection & Find Working Models
print("\n📡 Testing connection to Google...")
working_model = None

try:
    # We ask Google: "What models can I use?"
    print("📋 Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   - Found: {m.name}")
            # We prefer Flash, but will accept Pro if that's all you have
            if 'flash' in m.name and '1.5' in m.name:
                working_model = m.name
            elif 'pro' in m.name and not working_model:
                working_model = m.name

    if working_model:
        print(f"\n🎉 SUCCESS! Your key works. The best available model is: {working_model}")
        print(f"👉 ACTION: Go to config.py and change AI_MODEL to: '{working_model}'")
    else:
        print("\n⚠️ ISSUE: Connection successful, but NO text generation models were found.")
        print("   This usually means your API Key is restricted or the project has no billing/free-tier enabled.")

except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    print("👉 SOLUTION: Your API Key is likely blocked or invalid.")
    print("   Please generate a NEW key at: https://aistudio.google.com/app/apikey")

print("\n--- DIAGNOSTIC END ---")