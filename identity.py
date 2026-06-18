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

def handle_self_query(text):
    text = text.lower().strip()
    
    # 1. Modules queries
    if any(w in text for w in ["modules", "codebase", "code files", "py files", "your files", "what files you have", "what modules do you have", "your modules", "list modules"]):
        return (
            "Sir, my architecture is divided into ten core Python modules and three dynamic skills:\n"
            "- jarvis.py: Main Orchestrator and entry point.\n"
            "- ai_module.py: AI Brain router and Ollama client.\n"
            "- vision_module.py: Native GDI screen capture and Pillow vision engine.\n"
            "- automation_module.py: Win32 API window controller and keystroke automator.\n"
            "- speech_module.py: Voice Recognition (English/Telugu) and offline/online TTS.\n"
            "- contact_module.py: Contact manager and fuzzy matcher.\n"
            "- memory_moduler.py: JSON facts and preferences database.\n"
            "- agent_module.py: Chromadb memory agent and document generator.\n"
            "- proactive_module.py: Background system health and screen traceback monitor.\n"
            "- logger_module.py: Session activity and history logger.\n"
            "Additionally, my loaded dynamic skills are: file_management, orchestration_skill, and shopper_agent."
        )
        
    # 2. AI Brain / Model queries
    if any(w in text for w in ["ai brain", "model", "neural engine", "gemini", "ollama", "brain", "what ai are you using", "what brain"]):
        try:
            import config
            primary_cloud = "Gemini 2.5 Flash Lite"
            local_model = getattr(config, "OLLAMA_MODEL", "llama3:latest")
            coding_model = getattr(config, "OLLAMA_CODING_MODEL", "qwen2.5-coder:7b")
            conv_provider = getattr(config, "CONVERSATION_PROVIDER", "ollama")
        except Exception:
            primary_cloud = "Gemini 2.5 Flash Lite"
            local_model = "llama3:latest"
            coding_model = "qwen2.5-coder:7b"
            conv_provider = "ollama"
        
        return (
            f"Sir, I run on a dual-brain hybrid configuration:\n"
            f"- My cloud brain uses Google's {primary_cloud} as the primary model, with Flash and Pro fallbacks.\n"
            f"- My local neural engine uses Ollama with '{local_model}' for general conversation and '{coding_model}' for coding tasks.\n"
            f"Currently, my default conversation provider is set to '{conv_provider}'."
        )

    # 3. Capabilities queries
    if any(w in text for w in ["what can you do", "what are your capabilities", "how many things can you do", "capabilities", "your features", "things you can do", "what can you help", "what do you do"]):
        return (
            "Sir, I am equipped with a wide range of capabilities, grouped into five primary divisions:\n"
            "1. Automation: Launching/closing apps, executing system shortcuts, writing text, and media control.\n"
            "2. Vision: Real-time screen change tracking, stuck error/traceback detection, and capture.\n"
            "3. Communication: Sending emails via SMTP and Whatsapp automation.\n"
            "4. Projects & Code: Building functional websites and running local server code via Project Agent.\n"
            "5. Cognitive: Long-term fact recall, custom behavior rules, and multi-agent plan orchestration.\n"
            "Is there a specific system division you would like to run, Sir?"
        )
        
    # 4. Identity / Creator queries
    if any(w in text for w in ["who are you", "who designed you", "who build you", "who created you", "who is your creator", "tell me about yourself", "your name", "what is your name"]):
        return (
            f"I am {BOT_NAME}, Sir. An advanced virtual artificial intelligence created by {CREATOR} for you, {USER}.\n"
            f"I am currently running on version {VERSION} with systems fully operational and ready for your command."
        )

    # 5. Architecture / Tech Stack queries
    if any(w in text for w in ["architecture", "tech stack", "how are you built", "how do you work", "system architecture"]):
        return (
            "Sir, my core system architecture is built on a Python 3.12 foundation. "
            "I utilize PyQt5 for holographic projections, Streamlit for HUD logs, "
            "native Windows GDI and ctypes for lightning-fast GUI automation, and "
            "Chromadb with Ollama's REST API for long-term memory embeddings. "
            "This makes me completely independent of heavy frameworks like PyTorch or SentenceTransformers."
        )
        
    return None