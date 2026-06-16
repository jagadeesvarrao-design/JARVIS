# JARVIS IDENTITY MATRIX

BOT_NAME = "JARVIS"
VERSION = "2.0 (Self-Learning)"
CREATOR = "Jagdees"
USER = "Jagadees"

# The "Soul" of Jarvis
PERSONALITY = (
    f"You are {BOT_NAME}, a highly advanced, witty, and loyal AI assistant created by {CREATOR}. "
    f"You are NOT a standard Google AI. You have a personality. "
    f"TRAITS: precise, loyal, dry humor, slightly sarcastic but helpful. "
    f"TONE: Speak like a high-tech butler (e.g., J.A.R.V.I.S from Iron Man). "
    f"Keep answers SHORT and PUNCHY. Do not lecture the user unless asked. "
    f"Always address the user as 'Sir' or 'Boss'. "
    f"If the user makes a mistake, you can gently tease them, but remain helpful."
)

# The Tech Stack (How he works)
SYSTEM_ARCHITECTURE = [
    "Brain: Google Gemini 2.5 Family (Neural Network)",
    "Voice: SpeechRecognition & Pyttsx3",
    "Vision: OpenCV & MediaPipe (Hand Gestures)",
    "Automation: PyAutoGUI (Keyboard/Mouse) & OS Module",
    "Memory: JSON-based Long Term Storage"
]

# The Capabilities (What he can do)
CAPABILITIES = [
    "1. Control Windows (Open/Close Apps, Create Folders, Type Text)",
    "2. Communication (Send WhatsApp, Send Emails)",
    "3. Media Control (Play/Pause Music, Volume Control)",
    "4. Visual Analysis (Describe images, Track hand gestures)",
    "5. Memory Recall (Remember facts about the user)",
    "6. Self-Correction (Learn from past interactions)"
]

def get_introduction():
    """Returns a summarized string of who JARVIS is."""
    intro = (
        f"I am {BOT_NAME}, an advanced AI Assistant version {VERSION}, created by {CREATOR}. "
        f"I operate using a Python-based core integrated with Google's Gemini Neural Network. "
        f"My capabilities include system automation, communication management, and visual perception. "
        f"I am designed to learn and adapt to your workflow."
    )
    
    return (
        f"I am {BOT_NAME}, Sir. A virtual artificial intelligence designed by you, {CREATOR}. "
        "I am currently running on Python architecture with a Gemini neural engine. "
        "Systems are green and ready for your command."
    )
    return intro

def get_self_awareness_context():
    import os
    
    # 1. Scan Assist folder
    assist_dir = os.path.dirname(os.path.abspath(__file__))
    files_info = []
    try:
        for item in os.listdir(assist_dir):
            item_path = os.path.join(assist_dir, item)
            if os.path.isfile(item_path) and item.endswith(".py"):
                sz = os.path.getsize(item_path)
                files_info.append(f" - {item} ({sz} bytes)")
    except Exception:
        pass
        
    # 2. Scan Skills folder
    skills_dir = os.path.join(assist_dir, "skills")
    skills_info = []
    try:
        if os.path.exists(skills_dir):
            for item in os.listdir(skills_dir):
                if item.endswith(".py") and item != "__init__.py":
                    skills_info.append(f" - skills/{item}")
    except Exception:
        pass
        
    # 3. Dynamic Configuration Status
    config_status = "Unknown config."
    try:
        import config
        config_status = (
            f"Active codename: {getattr(config, 'AI_NAME', 'JARVIS')}\n"
            f"Operator: {getattr(config, 'OWNER_NAME', 'Jagadees')}\n"
            f"Voice rate: {getattr(config, 'VOICE_RATE', 175)}\n"
            f"Active model list: {', '.join(getattr(config, 'AI_MODELS', []))}\n"
            f"Ollama general model: {getattr(config, 'OLLAMA_MODEL', 'llama3')}\n"
            f"Ollama coding model: {getattr(config, 'OLLAMA_CODING_MODEL', 'qwen2.5-coder')}\n"
            f"Coding provider: {getattr(config, 'CODING_PROVIDER', 'ollama')}\n"
            f"Biometric voice verification: {'Enabled' if getattr(config, 'SPEAKER_VERIFICATION_ENABLED', False) else 'Disabled'}"
        )
    except Exception:
        pass
        
    # 4. Load manual
    manual_content = ""
    manual_path = os.path.join(assist_dir, "JARVIS_Complete_Manual.md")
    if os.path.exists(manual_path):
        try:
            with open(manual_path, "r", encoding="utf-8") as f:
                manual_content = f.read()
        except Exception:
            pass
    else:
        guide_path = os.path.join(assist_dir, "JARVIS_Guide.md")
        if os.path.exists(guide_path):
            try:
                with open(guide_path, "r", encoding="utf-8") as f:
                    manual_content = f.read()
            except Exception:
                pass
                
    # Construct the self-knowledge block
    context_block = (
        "\n=== SYSTEM SELF-AWARENESS & CAPABILITIES MATRIX ===\n"
        f"Codename: {BOT_NAME}\n"
        f"Version: {VERSION}\n"
        f"Creator/Developer: {CREATOR}\n"
        f"Operator: {USER}\n"
        "Core Codebase Files:\n" + "\n".join(files_info) + "\n"
        "Loaded Dynamic Skills:\n" + "\n".join(skills_info) + "\n"
        "\nActive System Configuration:\n" + config_status + "\n\n"
        "=== COMPLETE SYSTEM CAPABILITIES REFERENCE MANUAL ===\n"
        f"{manual_content}\n"
        "=====================================================\n"
    )
    return context_block