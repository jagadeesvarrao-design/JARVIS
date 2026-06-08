import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# ==================== KEYS ====================
API_KEYS_POOL = []
_env_key = os.getenv("GEMINI_API_KEY")
if _env_key:
    API_KEYS_POOL.append(_env_key)

_fallbacks = [
    "AIzaSyCf4iganD633ovflagxDAzXDkUc5rPh7Ts",
    "AIzaSyDsZKabtGrPWpyFHteTAUu19-Reh0m8gPM",
    "AIzaSyAd0m1WZ3rVpkv0nHoUtMNiGqAJA6i1cu0",
    "AIzaSyCYyui97LZAl0dXU8RbaqdcN8gPUhxtcFE",
    "AIzaSyAbIfNzr8Kve8cZ0ZECT6nF4JlhN1ZVrhE"
]
for _k in _fallbacks:
    if _k not in API_KEYS_POOL:
        API_KEYS_POOL.append(_k)
# FIX: usage of the correct 2026 Free Model
AI_MODELS = ["gemini-2.5-flash-lite",
             "gemini-2.0-flash-lite",
             "gemini-2.5-flash",
             "gemini-2.0-flash",
             
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