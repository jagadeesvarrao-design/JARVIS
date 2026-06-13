import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# ==================== KEYS ====================
API_KEYS_POOL = []
_env_key = os.getenv("GEMINI_API_KEY")
if _env_key:
    API_KEYS_POOL.append(_env_key)

_fallbacks = []
for _k in _fallbacks:
    if _k not in API_KEYS_POOL:
        API_KEYS_POOL.append(_k)
# Preferred models for 2026. Non-flash models or legacy 2.0-flash (restricted quota) are omitted/placed last.
AI_MODELS = ["gemini-3.5-flash",
             "gemini-2.5-flash",
             "gemini-2.5-flash-lite"
             ]

# ==================== IDENTITY ====================
AI_NAME = "Jarvis"
OWNER_NAME = "Jagadees"

# ==================== VOICE SETTINGS ====================
WAKE_WORD = "jarvis"
VOICE_RATE = 175
VOICE_VOLUME = 1.0

# ==================== EMAIL SETTINGS ====================
EMAIL_USER = "jagadeesvarrao@gmail.com" 
EMAIL_PASS = "rqtu rijm qchy onbv" 

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# ==================== PATHS ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== LOCAL AI FALLBACK (OLLAMA) ====================
# The model you downloaded via command prompt
OLLAMA_MODEL = "llama3"

# Default local endpoint for Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"

# ==================== SPEAKER VERIFICATION (BIOMETRICS) ====================
SPEAKER_VERIFICATION_ENABLED = False  # Set to True to enable voice verification
SPEAKER_REF_PATH = "owner_voice_ref.wav"  # Path to the owner's 5-second voice sample
SPEAKER_THRESHOLD = 0.25  # Standard ECAPA-TDNN cosine similarity threshold