import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# ==================== KEYS ====================
API_KEYS_POOL = []
_env_key = os.getenv("GEMINI_API_KEY")
if _env_key:
    for key in _env_key.split(","):
        clean_key = key.strip()
        if clean_key and clean_key not in API_KEYS_POOL:
            API_KEYS_POOL.append(clean_key)

_fallbacks = []
for _k in _fallbacks:
    if _k not in API_KEYS_POOL:
        API_KEYS_POOL.append(_k)
# Preferred models for 2026. Non-flash models or legacy 2.0-flash (restricted quota) are omitted/placed last.
AI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]

# ==================== IDENTITY ====================
AI_NAME = "Jarvis"
OWNER_NAME = "Jagadees"

# ==================== VOICE SETTINGS ====================
WAKE_WORD = "jarvis"
VOICE_RATE = 175
VOICE_VOLUME = 1.0
TTS_VOICE = "en-IN-PrabhatNeural"


# ==================== EMAIL SETTINGS ====================
EMAIL_USER = "jagadeesvarrao@gmail.com" 
EMAIL_PASS = "rqtu rijm qchy onbv" 

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# ==================== PATHS ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== LOCAL AI FALLBACK (OLLAMA) ====================
# General purpose local fallback model
OLLAMA_MODEL = "llama3:latest"

# Dedicated local coding model (e.g. qwen2.5-coder:7b, deepseek-coder:6.7b)
OLLAMA_CODING_MODEL = "qwen2.5-coder:7b"

# Default local endpoint for Ollama
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# ==================== CODING AGENT CONFIGURATION ====================
# Provider options: "gemini" or "ollama" (local)
CODING_PROVIDER = "ollama"


# ==================== SPEAKER VERIFICATION (BIOMETRICS) ====================
SPEAKER_VERIFICATION_ENABLED = False  # Set to True to enable voice verification
SPEAKER_REF_PATH = "owner_voice_ref.wav"  # Path to the owner's 5-second voice sample
SPEAKER_THRESHOLD = 0.25  # Standard ECAPA-TDNN cosine similarity threshold

# ==================== DEPLOYMENT ====================
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
