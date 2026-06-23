import sys
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["QT_LOGGING_RULES"] = "*.warning=false"

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pywinauto")

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import speech_recognition as sr
import time
import pyautogui
import keyboard
import webbrowser
import shutil
import random
import win32com.client
import datetime
import psutil
import queue
import pythoncom
import winsound
import smtplib 
from email.message import EmailMessage 
import json
import urllib.parse
import re
import atexit
import threading
import asyncio
import edge_tts
# Import Custom Modules
import config
from speech_module import SpeechRecognizer
from automation_module import ApplicationController
from vision_module import VisionSystem
from contact_module import ContactManager
from ai_module import AIBrain
import identity
from ddgs import DDGS
from agent_module import ProjectAgent
from proactive_module import ProactiveAgent

# Cached Regular Expressions for Script Detection
TELUGU_SCRIPT_RE = re.compile(r'[\u0C00-\u0C7F]')
DEVANAGARI_SCRIPT_RE = re.compile(r'[\u0900-\u097F]')
BENGALI_SCRIPT_RE = re.compile(r'[\u0980-\u09FF]')
TAMIL_SCRIPT_RE = re.compile(r'[\u0B80-\u0BFF]')
KANNADA_SCRIPT_RE = re.compile(r'[\u0C80-\u0CFF]')
MALAYALAM_SCRIPT_RE = re.compile(r'[\u0D00-\u0D7F]')
GUJARATI_SCRIPT_RE = re.compile(r'[\u0A80-\u0AFF]')

# Create the queue
voice_queue = queue.Queue()
stop_speech_event = threading.Event()
speaking_callback = None
use_edge_tts = True

# The dedicated voice-only worker
def voice_worker():
    import pyttsx3
    import pygame
    
    # Initialize Pygame Mixer for MP3 playback
    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"⚠️ Failed to init Pygame mixer: {e}")
        
    # Initialize Pyttsx3 for fallback offline TTS
    engine = None
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        # Try to set a male offline voice if available
        for voice in voices:
            if "David" in voice.name or "Male" in voice.name:
                engine.setProperty('voice', voice.id)
                break
        engine.setProperty('rate', 175) 
    except Exception as e:
        print(f"⚠️ Failed to init pyttsx3: {e}")
    
    # Initialize persistent event loop for asyncio tasks
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        while True:
            item = voice_queue.get()
            if item is None: break
            
            if isinstance(item, tuple):
                text, voice_override = item
            else:
                text = item
                voice_override = None
            
            if stop_speech_event.is_set():
                voice_queue.task_done()
                stop_speech_event.clear()
                continue
                
            global speaking_callback, use_edge_tts
            if speaking_callback:
                try:
                    speaking_callback(True)
                except Exception:
                    pass
                    
            try:
                temp_file = f"speech_temp_{int(time.time())}.mp3"
                success = False
                if use_edge_tts:
                    try:
                        # Generate Edge TTS voice file
                        async def run_tts():
                            voice = voice_override if voice_override else getattr(config, "TTS_VOICE", "en-IN-PrabhatNeural")
                            communicate = edge_tts.Communicate(text, voice)
                            await communicate.save(temp_file)
                        
                        loop.run_until_complete(asyncio.wait_for(run_tts(), timeout=10.0))
                        success = True
                    except Exception as e:
                        success = False
                        err_str = str(e).lower()
                        is_network_issue = any(phrase in err_str for phrase in ["connection", "getaddrinfo", "timeout", "unreachable"])
                        if is_network_issue:
                            print(f"🌐 [SPEECH SYSTEM]: Network issues detected ({e}). Disabling Edge TTS for this session to prevent lagging and falling back to pyttsx3.")
                            use_edge_tts = False
                        else:
                            import traceback
                            print(f"⚠️ Edge TTS failed: {e}. Falling back to pyttsx3.")
                            traceback.print_exc()
                        
                    if success and os.path.exists(temp_file):
                        try:
                            # Play using Pygame
                            pygame.mixer.music.load(temp_file)
                            pygame.mixer.music.play()
                            
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.05)
                                if stop_speech_event.is_set():
                                    pygame.mixer.music.stop()
                                    break
                                    
                            pygame.mixer.music.unload()
                            # Clean up temporary file
                            try:
                                os.remove(temp_file)
                            except Exception:
                                pass
                        except Exception as pe:
                            print(f"⚠️ Pygame Playback Error: {pe}. Falling back to pyttsx3.")
                            # Fallback speech
                            if engine:
                                engine.say(text)
                                engine.runAndWait()
                    else:
                        # Fallback speech
                        if engine:
                            engine.say(text)
                            engine.runAndWait()
            finally:
                if speaking_callback:
                    try:
                        speaking_callback(False)
                    except Exception:
                        pass
                        
            # Handle post-speech queue clearing if stopped
            if stop_speech_event.is_set():
                while not voice_queue.empty():
                    try:
                        voice_queue.get_nowait()
                        voice_queue.task_done()
                    except Exception:
                        break
                stop_speech_event.clear()
                
            voice_queue.task_done()
    finally:
        try:
            loop.close()
        except Exception:
            pass

voice_thread = None
def start_voice_thread():
    global voice_thread
    if voice_thread is None or not voice_thread.is_alive():
        voice_thread = threading.Thread(target=voice_worker, name="VoiceWorker", daemon=True)
        voice_thread.start()


# --- DASHBOARD LOGGER ---
def log_to_dashboard(type, message):
    log_file = "jarvis_logs.jsonl"
    entry = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "type": type, 
        "message": message
    }
    
    # Append the new log entry
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Error writing dashboard log: {e}")
        
    # Bounded truncation: only read/write when file grows past 100 lines
    try:
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > 100:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.writelines(lines[-50:])
    except Exception as e:
        print(f"Error truncating dashboard log: {e}")

# --- PATH FINDER ---
def get_desktop_path():
    return os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop')

# --- GLOBAL SEARCH ---
def find_folder_globally(folder_name):
    folder_name = folder_name.lower() 
    user_path = os.environ['USERPROFILE']
    
    search_dirs = [
        get_desktop_path(),
        os.path.join(user_path, "Documents"),
        os.path.join(user_path, "Downloads"),
        os.path.join(user_path, "Pictures"),
        os.path.join(user_path, "Music"),
        os.path.join(user_path, "Videos")
    ]
    
    for root in search_dirs:
        if not os.path.exists(root): continue
        possible_path = os.path.join(root, folder_name) 
        if os.path.exists(possible_path): return possible_path

        try:
            for item in os.listdir(root):
                if item.lower() == folder_name and os.path.isdir(os.path.join(root, item)):
                    return os.path.join(root, item)
        except: pass
    
    return None

def record_shutdown():
    stats_file = "jarvis_startup_stats.json"
    try:
        data = {}
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                data = json.load(f)
        data["last_shutdown_time"] = datetime.datetime.now().isoformat()
        with open(stats_file, "w") as f:
            json.dump(data, f, indent=4)
        print("💾 Recorded shutdown time successfully.")
    except Exception as e:
        print(f"⚠️ Error recording shutdown: {e}")

def exit_handler():
    print("🛑 System Shutdown Detected.")
    log_to_dashboard("system", "JARVIS shutting down due to system power off.")
    record_shutdown()

# Register the exit handler
atexit.register(exit_handler)

class JARVIS:
    def __init__(self):
        self.ears = SpeechRecognizer()
        self.automation = ApplicationController()
        self.vision = VisionSystem()
        self.contacts = ContactManager()
        self.brain = AIBrain()
        
        self.attachment_path = None
        self.last_topic = None 
        self.models = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"]
        self.rec_agent = None
        self.project_agent = None
        self.active_voice = None
        
        # Interactive Dialog Queues
        self.waiting_for_input = False
        self.input_queue = queue.Queue()
        
        # Initialize Memory Globally (Lazy Loaded with thread-safe lock)
        self._memory_brain = None
        self._memory_lock = threading.Lock()
        
        # Start background thread to warm up ChromaDB/PyTorch Memory Core
        threading.Thread(target=self._warm_up_memory, daemon=True, name="MemoryWarmupThread").start()
        
        # Start background thread to ensure Ollama is running and connected
        threading.Thread(target=self._ensure_ollama_running_bg, daemon=True, name="OllamaDaemonThread").start()
        
        # Dynamic Skills System initialization
        self.skills = []
        self.load_skills()
        
        # Start voice worker thread to prevent import-time deadlock
        start_voice_thread()

    def load_skills(self):
        self.skills = []
        skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
        if not os.path.exists(skills_dir):
            os.makedirs(skills_dir)
            
        import importlib.util
        try:
            for filename in os.listdir(skills_dir):
                if filename.endswith(".py") and filename != "__init__.py":
                    skill_name = filename[:-3]
                    filepath = os.path.join(skills_dir, filename)
                    spec = importlib.util.spec_from_file_location(skill_name, filepath)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, "get_triggers") and hasattr(module, "execute"):
                        self.skills.append(module)
                        print(f"🔌 [SKILLS SYSTEM]: Dynamic skill '{skill_name}' successfully loaded.")
        except Exception as e:
            print(f"⚠️ [SKILLS SYSTEM]: Error loading dynamic skills: {e}")


    @property
    def memory_brain(self):
        with self._memory_lock:
            if self._memory_brain is None:
                print("🧠 [SYSTEM]: Lazily Initializing Memory Core (ChromaDB)...")
                from agent_module import MemoryAgent
                self._memory_brain = MemoryAgent()
            return self._memory_brain

    def _warm_up_memory(self):
        try:
            # Access property to trigger background initialization
            _ = self.memory_brain
        except Exception as e:
            print(f"⚠️ [SYSTEM] Background Memory Core warmup failed: {e}")

    def _ensure_ollama_running_bg(self):
        import requests
        url_tags = config.OLLAMA_URL.replace("/api/generate", "/api/tags")
        print("🧠 [SYSTEM]: Checking Ollama status in background...")
        try:
            resp = requests.get(url_tags, timeout=5.0)
            if resp.status_code == 200:
                print("🧠 [SYSTEM]: Ollama is online and connected.")
                return
        except Exception:
            pass

        # Check if Ollama process is already running on the OS
        ollama_running = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                    ollama_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if ollama_running:
            print("🚀 [SYSTEM]: Ollama process is already running but not responding yet. Waiting for it to initialize...")
        else:
            print("🚀 [SYSTEM]: Local Ollama server is offline. Starting in background...")
            import subprocess
            try:
                ollama_bin = "ollama"
                default_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Ollama\ollama.exe")
                if os.path.exists(default_path):
                    ollama_bin = default_path
                subprocess.Popen(
                    [ollama_bin, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            except Exception as e:
                print(f"❌ [SYSTEM]: Failed to launch Ollama: {e}")
                return

        # Poll port for up to 15 seconds with 3.0s timeout
        for _ in range(15):
            try:
                resp = requests.get(url_tags, timeout=3.0)
                if resp.status_code == 200:
                    print("🚀 [SYSTEM]: Local Ollama server started successfully and connected.")
                    return
            except Exception:
                pass
            time.sleep(1.0)
        print("⚠️ [SYSTEM]: Ollama server did not respond within 15 seconds.")
    def _respond(self, text, voice=None):
        if text:
            # Determine voice to use: active_voice takes precedence if explicitly set by command
            voice_to_use = voice
            if not voice_to_use:
                voice_to_use = getattr(self, "active_voice", None)
            if not voice_to_use:
                voice_to_use = getattr(self, "temp_voice_override", None)
            
            # If we are using Telugu but response is in English, translate to Telugu script
            is_telugu = (voice_to_use == "te-IN-MohanNeural")
            if is_telugu and not TELUGU_SCRIPT_RE.search(text):
                print(f"🤖 JARVIS (English response): {text}")
                text = self.translate_to_telugu(text)
                voice_to_use = "te-IN-MohanNeural"
                
            print(f"🤖 JARVIS: {text}")
            
            # Auto-detect script to match voice dynamically if no override/session voice is set
            if not voice_to_use:
                # Check for Telugu script characters
                if TELUGU_SCRIPT_RE.search(text):
                    voice_to_use = "te-IN-MohanNeural"
                # Check for Devanagari (Hindi) script characters
                elif DEVANAGARI_SCRIPT_RE.search(text):
                    voice_to_use = "hi-IN-MadhurNeural"
                # Check for Bengali script characters
                elif BENGALI_SCRIPT_RE.search(text):
                    voice_to_use = "bn-IN-BashkarNeural"
                # Check for Tamil script characters
                elif TAMIL_SCRIPT_RE.search(text):
                    voice_to_use = "ta-IN-ValluvarNeural"
                # Check for Kannada script characters
                elif KANNADA_SCRIPT_RE.search(text):
                    voice_to_use = "kn-IN-GaganNeural"
                # Check for Malayalam script characters
                elif MALAYALAM_SCRIPT_RE.search(text):
                    voice_to_use = "ml-IN-MidhunNeural"
                # Check for Gujarati script characters
                elif GUJARATI_SCRIPT_RE.search(text):
                    voice_to_use = "gu-IN-NiranjanNeural"

            if voice_to_use:
                voice_queue.put((text, voice_to_use))
            else:
                voice_queue.put(text)
            
            try:
                # 1. Log to the GUI dashboard
                log_to_dashboard("jarvis", text)
            except Exception as e:
                pass
    def _play_chime(self):  
        try:
            winsound.Beep(1200, 150)       
        except: pass
    def _listen_for_command(self):
        return self.ears.listen()

    def get_user_response(self, retries=1):
        self.waiting_for_input = True
        
        # Clear the queue first
        while not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
            except queue.Empty:
                break
            except Exception:
                break
                
        stop_listening = None
        try:
            # We use the existing self.ears.microphone and self.ears.recognizer
            with self.ears.microphone as source:
                self.ears.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
            # Define callback to put recognized text to input_queue
            def callback(recognizer, audio):
                try:
                    import socket
                    import threading
                    import re
                    
                    en_result = []
                    te_result = []
                    
                    def rec_en():
                        orig_timeout = socket.getdefaulttimeout()
                        try:
                            socket.setdefaulttimeout(4.0)
                            query = recognizer.recognize_google(audio, language='en-in')
                            if query:
                                en_result.append(query.strip())
                        except Exception:
                            pass
                        finally:
                            socket.setdefaulttimeout(orig_timeout)
 
                    def rec_te():
                        orig_timeout = socket.getdefaulttimeout()
                        try:
                            socket.setdefaulttimeout(4.0)
                            query = recognizer.recognize_google(audio, language='te-in')
                            if query:
                                te_result.append(query.strip())
                        except Exception:
                            pass
                        finally:
                            socket.setdefaulttimeout(orig_timeout)
 
                    t_en = threading.Thread(target=rec_en)
                    t_te = threading.Thread(target=rec_te)
                    
                    t_en.start()
                    t_te.start()
                    
                    t_en.join(timeout=4.0)
                    t_te.join(timeout=4.0)
                    
                    en_text = en_result[0] if en_result else ""
                    te_text = te_result[0] if te_result else ""
                    
                    # Define core English grammatical words to identify English speech
                    ENGLISH_CORE_WORDS = {
                        "the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "on", "at", 
                        "by", "for", "with", "about", "from", "into", "through", "during", "before", "after",
                        "i", "me", "my", "myself", "we", "us", "our", "ours", "you", "your", "yours", 
                        "he", "him", "his", "she", "her", "hers", "it", "its", "they", "them", "their", "theirs",
                        "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had", 
                        "do", "does", "did", "done", "will", "would", "shall", "should", "can", "could", "may", "might", "must",
                        "what", "which", "who", "whom", "whose", "this", "that", "these", "those",
                        "there", "here", "when", "where", "why", "how", "all", "any", "both", "each", "few", 
                        "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", 
                        "so", "than", "too", "very", "just", "hello", "jarvis", "please", "speak", "english"
                    }
                    
                    en_words = set(en_text.lower().split()) if en_text else set()
                    is_english_command = bool(en_words & ENGLISH_CORE_WORDS)
                    
                    # If we detected English core words, assume it is English speech
                    if en_text and is_english_command:
                        self.input_queue.put(en_text.lower())
                    # Check if Telugu transcription contains Telugu characters
                    elif te_text and re.search(r'[\u0C00-\u0C7F]', te_text):
                        self.input_queue.put(te_text)
                    elif en_text:
                        self.input_queue.put(en_text.lower())
                    elif te_text:
                        self.input_queue.put(te_text.lower())
                except Exception:
                    pass
            
            stop_listening = self.ears.recognizer.listen_in_background(self.ears.microphone, callback)
        except Exception as e:
            print(f"⚠️ Failed to start background voice listener: {e}")
            
        response = None
        # Wait for up to 15 seconds (150 * 100ms) for user response
        for _ in range(150):
            try:
                response = self.input_queue.get(timeout=0.1)
                if response:
                    break
            except queue.Empty:
                pass
                
        if stop_listening:
            try:
                stop_listening(wait_for_stop=True)
            except Exception:
                pass
                
        self.waiting_for_input = False
        
        if response:
            return response
            
        if retries > 0:
            self._respond("I didn't catch that. Please repeat.")
            return self.get_user_response(retries=retries - 1)
            
        return None

    def _force_listen(self, retries=1):
        return self.get_user_response(retries=retries)
    
    def _morning_briefing(self):
        hour = int(datetime.datetime.now().hour)
        if 0 <= hour < 12: greeting = "Good Morning"
        elif 12 <= hour < 18: greeting = "Good Afternoon"
        else: greeting = "Good Evening"

        try:
            battery = psutil.sensors_battery()
            bat_msg = f"Power is at {battery.percent}%." if battery else "Running on AC power."
        except:
            bat_msg = "Power systems online."
        
        strTime = datetime.datetime.now().strftime("%I:%M %p")

        intro = (
            f"{greeting}, {config.OWNER_NAME}. "
            f"Time is {strTime}. System status: {bat_msg} "
            "I am online."
        )
        self._respond(intro)

        # Start tracking and briefing logic
        stats_file = "jarvis_startup_stats.json"
        today = datetime.date.today().isoformat()
        now_str = datetime.datetime.now().isoformat()
        
        prev_shutdown = None
        startup_count = 1
        
        try:
            if os.path.exists(stats_file):
                with open(stats_file, "r") as f:
                    data = json.load(f)
                prev_shutdown = data.get("last_shutdown_time")
                last_run_date = data.get("last_run_date")
                if last_run_date == today:
                    startup_count = data.get("startup_count", 0) + 1
                else:
                    startup_count = 1
            else:
                data = {}
                startup_count = 1
                
            data["last_run_date"] = today
            data["startup_count"] = startup_count
            data["last_startup_time"] = now_str
            
            with open(stats_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"⚠️ Error updating startup stats: {e}")

        # Deliver appropriate briefing
        if startup_count == 1:
            self._respond("This is my first startup of the day, Sir. Let me compile a briefing on the latest developments in the AI industry...")
            sentences = self._fetch_and_compile_briefing()
            if sentences:
                self._speak_briefing(sentences)
        else:
            print(f"ℹ️ Jarvis startup count for today: {startup_count}")
            if prev_shutdown:
                print(f"ℹ️ Checking for AI news since last shutdown: {prev_shutdown}")
                sentences = self._check_for_big_news_since_shutdown(prev_shutdown)
                if sentences:
                    self._respond("Sir, some significant developments have occurred in the AI industry since we last shut down. Here is a quick briefing...")
                    self._speak_briefing(sentences)

    def _fetch_and_compile_briefing(self):
        try:
            from ddgs import DDGS
            results = []
            current_year = datetime.datetime.now().year
            query = f"latest artificial intelligence breakthroughs news {current_year}"
            
            print(f"🔍 Searching for AI news with query: '{query}'")
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=6))
                
            if not results:
                return ["I was unable to retrieve any recent news from the network."]
                
            news_text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            
            prompt = (
                "You are Jarvis, a sophisticated and conversational AI assistant. "
                "Review the following recent AI industry news articles:\n"
                f"{news_text}\n\n"
                "Summarize these events in a conversational briefing for your creator. "
                "Break the briefing down into 4 to 6 clear, distinct sentences. "
                "Ensure each sentence is on a new line and stands alone as a complete, spoken thought. "
                "Do not use markdown lists (like bullet points or numbers) or code formatting. Just return the raw sentences, one per line."
            )
            
            response = self.brain.get_response(prompt)
            sentences = [s.strip() for s in response.split("\n") if s.strip()]
            return sentences
        except Exception as e:
            print(f"Error compiling briefing: {e}")
            return ["I encountered an error while compiling the AI news update."]

    def _check_for_big_news_since_shutdown(self, prev_shutdown):
        try:
            from ddgs import DDGS
            results = []
            current_year = datetime.datetime.now().year
            query = f"latest artificial intelligence breakthroughs news {current_year}"
            
            print(f"🔍 Searching for AI news with query: '{query}'")
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=6))
                
            if not results:
                return None
                
            news_text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            
            prev_shutdown_dt = datetime.datetime.fromisoformat(prev_shutdown)
            prev_shutdown_formatted = prev_shutdown_dt.strftime("%Y-%m-%d %H:%M:%S")
            current_time_formatted = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            prompt = (
                "You are Jarvis, a sophisticated AI desktop assistant.\n"
                "Here is the latest AI industry news:\n"
                f"{news_text}\n\n"
                f"The user last shut down Jarvis at {prev_shutdown_formatted}. The current time is {current_time_formatted}.\n"
                "Identify if there is any major, highly significant breakthrough or massive news announcement "
                "in the AI industry (e.g., a major model release, critical tech acquisition, or significant AI breakthrough) "
                "that appears to have happened since the last shutdown.\n"
                "If YES, summarize the major news in 2 to 3 sentences in a conversational way, stating that it happened since the last shutdown. "
                "Each sentence must be on a new line. Do not use bullet points or code block formatting.\n"
                "If NO major/groundbreaking news occurred since then, you MUST respond with exactly the single word: NONE."
            )
            
            response = self.brain.get_response(prompt)
            if response.strip().upper() == "NONE":
                return None
                
            sentences = [s.strip() for s in response.split("\n") if s.strip()]
            return sentences
        except Exception as e:
            print(f"Error checking for big news: {e}")
            return None

    def _check_for_stop(self):
        # 1. Keyboard Interrupt (instant and reliable)
        if keyboard.is_pressed('esc'):
            print("🛑 Keyboard interrupt detected via ESC.")
            return True
            
        # 2. Voice Interrupt (non-blocking listening check)
        try:
            with self.ears.microphone as source:
                print("👂 [Briefing Active] Checking for stop command...")
                audio = self.ears.recognizer.listen(source, timeout=0.4, phrase_time_limit=1.2)
                text = self.ears.recognizer.recognize_google(audio).lower()
                print(f"👂 Briefing listen heard: '{text}'")
                if "stop" in text or "cancel" in text or "quiet" in text or "hush" in text:
                    print("🛑 Voice interrupt detected.")
                    return True
        except Exception:
            pass
            
        return False

    def _speak_briefing(self, sentences, start_idx=0):
        self.pending_briefing = list(sentences)
        self.briefing_index = start_idx
        stop_speech_event.clear()
        
        while self.briefing_index < len(self.pending_briefing):
            sentence = self.pending_briefing[self.briefing_index]
            self._respond(sentence)
            
            # Wait for SAPI to finish speaking this sentence, checking for Esc key
            is_interrupted = False
            while voice_queue.unfinished_tasks > 0:
                if keyboard.is_pressed('esc'):
                    print("🛑 Keyboard interrupt detected via ESC.")
                    stop_speech_event.set()
                    is_interrupted = True
                    break
                time.sleep(0.05)
                
            if is_interrupted:
                self._respond("Understood, Sir. Pausing the briefing. You can ask me to resume it anytime.")
                return True
                
            self.briefing_index += 1
            
            # Check for stop request between sentences
            if self._check_for_stop():
                stop_speech_event.set()
                self._respond("Understood, Sir. Pausing the briefing. You can ask me to resume it anytime.")
                return True
                
        # Reset if fully read
        self.pending_briefing = None
        self.briefing_index = 0
        return False

    def translate_to_english(self, telugu_text):
        prompt = (
            "You are a translation assistant for a voice command system.\n"
            "The user spoke a command in Telugu, English, or a mix of both (Telugu-English code-switching).\n"
            "Translate this command into a direct, concise English voice assistant command.\n"
            "Ensure that any technical or application terms (like 'website', 'file', 'folder', 'email', 'whatsapp') are translated to standard English actions.\n"
            "Return ONLY the English translation, with no explanation or punctuation. Example input: 'వెబ్‌సైట్ క్రియేట్ చేయి', output: 'create a website'.\n\n"
            f"Input: {telugu_text}"
        )
        try:
            response = self.brain.get_response(prompt)
            return response.strip().lower()
        except Exception as e:
            print(f"⚠️ [TRANSLATION ERROR] Failed to translate Telugu command: {e}")
            return telugu_text

    def translate_to_telugu(self, english_text):
        prompt = (
            "You are a translation assistant for a voice command system.\n"
            "Translate the following English assistant response into natural, polite, and conversational Telugu script.\n"
            "Preserve any proper nouns or technical names (like 'Jarvis', 'Google', 'WhatsApp', 'Email') in their standard spoken transliterated form or in English if appropriate.\n"
            "Return ONLY the Telugu translation without any extra formatting or explanation.\n\n"
            f"Text: {english_text}"
        )
        try:
            response = self.brain.get_response(prompt)
            return response.strip()
        except Exception as e:
            print(f"⚠️ [TRANSLATION ERROR] Failed to translate response to Telugu: {e}")
            return english_text

    def interactive_website_builder(self, topic, command_text):
        # 1. Ask for requirements
        if not topic or topic == "New_Project":
            self._respond("Understood, Sir. What is the topic of the website you want to create?")
            topic = self._force_listen()
            if not topic:
                self._respond("No topic provided. Aborting website creation.")
                return False
        
        self._respond(f"Understood, Sir. What specific requirements or features would you like to incorporate into your {topic} website?")
        user_reqs = self._force_listen()
        if not user_reqs:
            self._respond("No requirements provided. Aborting website creation.")
            return False
            
        from agent_module import ProjectAgent
        self.project_agent = ProjectAgent()
        
        confirmed = False
        current_reqs = user_reqs
        final_reqs = user_reqs
        trends = ""
        
        while not confirmed:
            self._respond("Researching competitor trends and analyzing requirements, please hold...")
            # 2. Search top 10 websites related to domain and suggest changes
            trends = self.project_agent.research_market_trends(topic)
            suggestions = self.project_agent.consult_and_refine_requirements(topic, current_reqs)
            
            # Speak / present the recommendations
            self._respond(f"Based on my analysis of top competitor websites, here are my suggestions:\n{suggestions}\n\nDo you want to confirm these requirements and build the website? Say yes to proceed, or state your changes.")
            
            response = self._force_listen()
            if not response:
                self._respond("No response received. Proceeding with the current requirements.")
                final_reqs = f"Website Topic: {topic}\nInitial Requirements: {current_reqs}\nCompetitor Recommendations:\n{suggestions}"
                confirmed = True
            elif any(w in response.lower() for w in ["yes", "confirm", "yep", "sure", "ok", "yeah"]):
                final_reqs = f"Website Topic: {topic}\nInitial Requirements: {current_reqs}\nCompetitor Recommendations:\n{suggestions}"
                confirmed = True
            else:
                self._respond("Understood. Updating requirements based on your feedback...")
                current_reqs = f"{current_reqs}\nUser Update: {response}"
        
        # 3. Create the website
        self._respond("Requirements confirmed. Initiating code generation for your full-stack Flask application...")
        project_name = f"{topic.replace(' ', '_')}_Project"
        
        # Save requirements
        self.project_agent.save_requirements(project_name, final_reqs)
        
        # Generate code files
        full_context = f"Topic: {topic}. Requirements: {final_reqs}. Trends: {trends}"
        code_files = self.project_agent.generate_initial_code(full_context)
        if not code_files:
            self._respond("I encountered an issue generating the initial blueprints. Retrying generation...")
            code_files = self.project_agent.generate_initial_code(full_context)
            if not code_files:
                self._respond("Blueprints generation failed. Please try again.")
                return False
                
        # Write files to disk
        self.project_agent.write_code_files(code_files)
        
        # Generate Classified PDF Manual
        self.project_agent.generate_project_pdf(final_reqs, trends)
        
        # 4. Self-healing launch
        self._respond("Files compiled successfully. Launching server and performing database seeding...")
        local_url = self.project_agent.launch_with_autofix()
        
        if "Error" in local_url or "Fatal" in local_url:
            self._respond("The server failed to launch cleanly after self-healing attempts.")
            return False
            
        # 5. Local preview and show user
        webbrowser.open(local_url)
        self._respond(f"Website is live locally at {local_url}. Please review the layout in your browser. Do you have any changes to make, or would you like to confirm the website?")
        
        # Feedback loop on local preview
        history = final_reqs
        while True:
            feedback = self._force_listen()
            if not feedback or any(w in feedback.lower() for w in ["confirm", "good", "perfect", "done", "no changes", "ok", "yes", "looks great", "looks good"]):
                self._respond("Website design confirmed, Sir.")
                break
            else:
                self._respond("Understood, Sir. Modifying code files and updating the live server...")
                updated_code = self.project_agent.update_code(history, feedback)
                if updated_code:
                    self.project_agent.write_code_files(updated_code)
                    local_url = self.project_agent.launch_with_autofix()
                    webbrowser.open(local_url)
                    self._respond("Website updated successfully. Please check your browser. Do you have any other changes or can we confirm the website?")
                    history = f"{history}\nFeedback: {feedback}"
                else:
                    self._respond("I was unable to compile the requested updates. Please restate your feedback.")
        
        # 6. Ask for internet deployment
        self._respond("Would you like me to launch the website on the internet? Say yes or no.")
        deploy_resp = self._force_listen()
        
        if deploy_resp and any(w in deploy_resp.lower() for w in ["yes", "yep", "sure", "ok", "yeah"]):
            self._respond("Understood. Deploying via ngrok tunnel...")
            public_url = self.project_agent.deploy_to_internet()
            if public_url:
                webbrowser.open(public_url)
                self._respond(f"Website successfully deployed to the internet, Sir! Access it at: {public_url}. The port and URL have been stored in the project's deployment_manifest.txt.")
            else:
                self._respond("Internet deployment failed. The website remains active on your local port 5000.")
        else:
            self._respond("Understood, Sir. I will keep the website served locally on port 5000.")
            
        return False

    def _determine_intent(self, text):
        prompt = f"""Analyze the user's command and determine the intent.
Command: "{text}"
Return ONLY a valid JSON object matching this schema:
{{
  "intent": "web_search" | "build_project" | "memory_store" | "memory_recall" | "system_control" | "conversational",
  "topic": "extracted topic or None"
}}
"""
        try:
            response_text = self.brain.get_response(prompt).strip()
            import re, json
            json_match = re.search(r'(\{[\s\S]*\})', response_text)
            if json_match:
                return json.loads(json_match.group(1))
            return {"intent": "conversational", "topic": text}
        except Exception as e:
            return {"intent": "conversational", "topic": text}

    def process_command(self, text):
        self.temp_voice_override = None
        try:
            return self._process_command_impl(text)
        finally:
            self.temp_voice_override = None

    def _process_command_impl(self, text):
        original_text = text
        text = text.lower()
        
        # Correct common speech-to-text homophone errors for "greet"
        text = re.sub(r'\b(?:great|great\s+great)\b(?=\s+(?:her|him|them|my|your|nanna|amma|mother|father|brother|sister|guest|parent))', 'greet', text)
        text = re.sub(r'\bgreating\b', 'greeting', text)
        text = text.replace("great greet", "greet").replace("great great", "greet")
        
        # Sync original_text if it was changed (and not containing Telugu script)
        if text != original_text.lower():
            if not re.search(r'[\u0C00-\u0C7F]', original_text):
                original_text = text
                
        print(f"👤 USER: {text}")
        
        # If waiting for interactive user response, redirect console inputs to input_queue
        if getattr(self, 'waiting_for_input', False):
            self.input_queue.put(original_text)
            return True

        # Check if the user's input contains Telugu script characters
        if TELUGU_SCRIPT_RE.search(original_text):
            self.temp_voice_override = "te-IN-MohanNeural"
            print("🎙️ Telugu command detected. Translating...")
            translated_text = self.translate_to_english(original_text)
            print(f"🎙️ Translated Telugu command to English: '{translated_text}'")
            original_text = translated_text
            text = translated_text.lower()

        # --- DYNAMIC INDIAN VOICE ROUTER ---
        voice_mappings = {
            "telugu": "te-IN-MohanNeural",
            "hindi": "hi-IN-MadhurNeural",
            "bengali": "bn-IN-BashkarNeural",
            "bangla": "bn-IN-BashkarNeural",
            "kannada": "kn-IN-GaganNeural",
            "malayalam": "ml-IN-MidhunNeural",
            "marathi": "mr-IN-ManoharNeural",
            "tamil": "ta-IN-ValluvarNeural",
            "gujarati": "gu-IN-NiranjanNeural",
            "urdu": "ur-IN-SalmanNeural",
            "english": "en-IN-PrabhatNeural"
        }
        
        # Check for explicit language commands:
        # e.g., "speak in english", "talk in telugu", "switch to hindi", "change language to tamil", "speak english"
        lang_detected = None
        for lang in voice_mappings:
            if lang in text:
                # Highly robust pattern matching for language switching commands
                patterns = [
                    # e.g., "speak ... english", "talk ... telugu", "switch ... hindi", "use ... tamil"
                    rf"\b(?:talk|speak|switch|change|convert|use)\b.*\b{lang}\b",
                    # e.g., "english ... voice", "telugu ... language"
                    rf"\b{lang}\b.*\b(?:voice|language)\b",
                    # e.g., "voice ... english", "language ... telugu"
                    rf"\b(?:voice|language)\b.*\b{lang}\b",
                    # e.g., "in english", "to telugu" (as a standalone command)
                    rf"^\s*(?:in|to|into)\s+{lang}\s*$"
                ]
                if any(re.search(pat, text) for pat in patterns) or text.strip() == lang:
                    lang_detected = lang
                    break

        if lang_detected:
            target_voice = voice_mappings[lang_detected]
            if lang_detected == "english":
                self.active_voice = None  # Reset to default
                self.temp_voice_override = None  # Clear any translation override
                self._respond("Sure Sir, switching back to default English voice.", voice="en-IN-PrabhatNeural")
            else:
                self.active_voice = target_voice
                self.temp_voice_override = None  # Clear override so that greeting does not undergo double translation
                greetings = {
                    "telugu": "తప్పకుండా సర్, ఇకపై నేను తెలుగులో మాట్లాడతాను.",
                    "hindi": "जी सर, अब से मैं हिंदी में बात करूँगा।",
                    "bengali": "হ্যাঁ স্যার, এখন থেকে আমি বাংলায় কথা বলব।",
                    "bangla": "হ্যাঁ স্যার, এখন থেকে আমি বাংলায় কথা বলব।",
                    "tamil": "சரி சார், இனி நான் தமிழில் பேசுவேன்.",
                    "kannada": "ಖಂಡಿತ ಸರ್, ಇನ್ನು ಮುಂದೆ ನಾನು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುತ್ತೇನೆ.",
                    "malayalam": "ശരി സർ, ഇനി ഞാൻ മലയാളത്തിൽ സംസാരിക്കാം.",
                    "marathi": "नक्कीच सर, आतापासून मी मराठीत बोलेन.",
                    "gujarati": "ચોક્કસ સર, હવેથી હું ગુજરાતીમાં વાત કરીશ.",
                    "urdu": "جی سر، اب سے میں اردو میں بات کروں گا۔"
                }
                greeting = greetings.get(lang_detected, f"Sure Sir, I will now speak in {lang_detected.capitalize()}.")
                self._respond(greeting, voice=target_voice)
            return False
        
        # 1. Handle Exit (Hard override)
        if "exit" in text or "quit" in text:
            self._respond("Powering down.")
            record_shutdown()
            import sys
            sys.exit(0)
            
        # 1.1 Handle Sleep/Standby (Hard override)
        if any(w in text for w in ["go to sleep", "sleep mode", "enter sleep mode", "go to standby", "standby mode", "standby"]):
            self._respond("Entering standby mode.")
            return False
            
        # 1.5 Dynamic Skills Routing
        for skill in self.skills:
            try:
                triggers = skill.get_triggers()
                for trigger in triggers:
                    if isinstance(trigger, str):
                        match = re.search(trigger, text)
                        if match:
                            res = skill.execute(self, text, original_text, match)
                            if res is not None:
                                return res
            except Exception as se:
                print(f"⚠️ [SKILLS SYSTEM]: Error executing skill: {se}")
            
        # 2. Semantic Intent Routing
        intent_data = self._determine_intent(text)
        intent = intent_data.get("intent", "conversational")
        topic = intent_data.get("topic", "")
        
        print(f"🧠 [ROUTER] Intent detected: {intent} | Topic: {topic}")
        
        # Override specifically for building complex projects to use the interactive website builder
        is_site_request = bool(re.search(r'\b(build|create|design|make)\s+(?:an?\s+)?(?!.*\b(?:document|report|file|folder)\b)(?:[a-z0-9_-]+\s+){0,3}(?:website|web site|project|app)\b', text))
        if intent == "build_project" or is_site_request:
            if not topic or len(topic) < 3:
                topic = "New_Project"
            self.interactive_website_builder(topic, text)
            return False
        
        # 1. Handle Exit
        if "exit" in text or "quit" in text:
            self._respond("Powering down.")
            record_shutdown()
            import sys
            sys.exit(0)
            
        # Handle Briefing Controls
        if "resume briefing" in text or "continue briefing" in text:
            if hasattr(self, 'pending_briefing') and self.pending_briefing and self.briefing_index < len(self.pending_briefing):
                self._respond("Resuming briefing from where we left off...")
                self._speak_briefing(self.pending_briefing, start_idx=self.briefing_index)
            else:
                self._respond("There is no paused briefing to resume, Sir.")
            return False

        if "tell me the briefing" in text or "start briefing" in text:
            self._respond("Fetching the latest news to compile a briefing...")
            sentences = self._fetch_and_compile_briefing()
            if sentences:
                self._speak_briefing(sentences)
            else:
                self._respond("I could not compile the briefing at this moment.")
            return False
            
        # ==========================================
        # 🧠 MEMORY & IDENTITY
        # ==========================================
        if text.startswith("remember"):
            from memory_moduler import MemorySystem
            self._respond(MemorySystem().remember_fact(text))
            return False
        
        if "open memory" in text or "show memory" in text:
            mem_path = "memory.json"
            if os.path.exists(mem_path):
                self._respond("Opening memory database.")
                os.startfile(os.path.abspath(mem_path))
            else:
                self._respond("Memory file not created yet.")
            return False

        if any(w in text for w in ["tell me about yourself", "introduce yourself", "who are you", "what is jarvis", "who is jarvis", "tell me about you"]):
            self._respond("Initializing self-introduction sequence...")
            prompt = (
                "Introduce yourself to a guest. Synthesize an impressive, professional butler-style vocal greeting. "
                "Briefly mention your version, creator, key system components (like your neural engine and modules), "
                "and some advanced dynamic capabilities from your capabilities reference manual. "
                "CRITICAL SPEECH RULES:\n"
                "1. Keep it concise, natural, and conversational.\n"
                "2. Do NOT use markdown symbols (no asterisks, backticks, hashes, underlines, or square brackets).\n"
                "3. Do NOT output bullet points or list dashes (use words like 'first', 'second', 'additionally' instead of lists).\n"
                "4. Conclude with a loyal butler remark, such as 'I am online and ready to assist, Sir.'"
            )
            try:
                intro_response = self.brain.get_response(prompt)
                # Cleanup formatting symbols to make text perfectly readable by TTS
                clean_response = intro_response.replace("*", "").replace("`", "")
                clean_response = re.sub(r'#+\s+', '', clean_response)
                clean_response = re.sub(r'^\s*[-*+]\s+', '', clean_response, flags=re.MULTILINE)
                clean_response = re.sub(r'^\s*\d+\.\s+', '', clean_response, flags=re.MULTILINE)
                clean_response = re.sub(r'\s+', ' ', clean_response).strip()
                self._respond(clean_response)
            except Exception as e:
                print(f"Error generating introduction: {e}")
                self._respond("I am JARVIS, Sir. A virtual artificial intelligence designed by Jagdees. I operate on python architecture with a Gemini neural engine, and I am online and ready to assist.")
            return False

        if any(w in text for w in ["show my profile", "who am i to you", "what is my style", "show operator profile"]):
            from memory_moduler import MemorySystem
            mem = MemorySystem()
            profile = mem.get_user_profile()
            style = profile.get("conversational_style", "conversational")
            interaction = profile.get("interaction_type", "text")
            frequent_topics = profile.get("frequent_topics", {})
            
            top_topics = sorted(frequent_topics.items(), key=lambda x: x[1], reverse=True)
            fav_topic = top_topics[0][0].replace("_", " ") if top_topics else "casual chat"
            
            report = (
                f"Sir, I have dynamically analyzed your usage patterns. "
                f"Your detected conversational style is currently classified as {style}. "
                f"Your primary topic of interest is {fav_topic}, and you typically interact with me using {interaction} input. "
                f"I am actively using these parameters to adjust and optimize your experience."
            )
            self._respond(report)
            return False

        if any(w in text for w in ["what have you learned", "what do you know about me", "show learned memory"]):
            from memory_moduler import MemorySystem
            mem = MemorySystem()
            facts = mem.recall_facts()
            rules = mem.recall_rules()
            prefs = mem.recall_preferences()
            
            summary = []
            if facts:
                summary.append(f"Facts I remember: {facts}.")
            if rules:
                rules_str = ", ".join(rules)
                summary.append(f"Behavioral rules: {rules_str}.")
            if prefs:
                prefs_str = ", ".join([f"{k} is {v}" for k, v in prefs.items()])
                summary.append(f"Preferences: {prefs_str}.")
                
            if summary:
                self._respond("Sir, here is what I have learned from our conversations: " + " ".join(summary))
            else:
                self._respond("I haven't learned any facts, rules, or preferences yet, Sir.")
            return False

        if text.startswith("forget rule") or "delete rule" in text:
            rule_query = text.replace("forget rule", "").replace("delete rule", "").strip()
            from memory_moduler import MemorySystem
            res = MemorySystem().forget_rule(rule_query)
            self._respond(res)
            return False

        if text.startswith("forget fact") or "delete fact" in text:
            fact_query = text.replace("forget fact", "").replace("delete fact", "").strip()
            from memory_moduler import MemorySystem
            res = MemorySystem().forget_fact(fact_query)
            self._respond(res)
            return False

        if text.startswith("forget preference") or "delete preference" in text:
            pref_query = text.replace("forget preference", "").replace("delete preference", "").strip()
            from memory_moduler import MemorySystem
            res = MemorySystem().forget_preference(pref_query)
            self._respond(res)
            return False

        # ==========================================
        # 🌐 LEVEL 1: WEB SEARCH (NEW!)
        # ==========================================
        search_triggers = ["search for", "google", "look up", "find info on"]
        if any(trigger in text for trigger in search_triggers) and "image" not in text and "photo" not in text:
            try:
                from ddgs import DDGS
                
                # 1. Clean Query
                query = text
                for t in search_triggers:
                    if t in query:
                        query = query.split(t,1)[-1]
                        break
                query = query.strip()
                
                if not query:
                    query = text 
                    
                self._respond(f"Searching the web for {query}...")
                print(f"🌍 JARVIS: Browsing for '{query}'...")
                
                # 2. Perform Search
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=2))
                    
                if results:
                    # 3. Summarize First Result
                    top_result = results[0]['body']
                    self._respond(f"Here is what I found: {top_result}")
                    
                    # 4. Open Link in Browser for user to see more
                    webbrowser.open(results[0]['href'])
                else:
                    self._respond("I couldn't find any results on the secure network.")
                
                return False # Stop here
            except Exception as e:
                print(f"Search Error: {e}")
                self._respond("Network error. I am unable to connect to the search grid.")
                return False

        # ==========================================
        # 💻 LEVEL 2: WEBPAGE DESIGNER (LOCAL SINGLE PAGE)
        # ==========================================
        is_page_request = bool(re.search(r'\b(build|create|design|make)\s+(?:an?\s+)?(?!.*\b(?:document|report|file|folder)\b)(?:[a-z0-9_-]+\s+){0,3}(?:webpage|web page|page)\b', text))
        if is_page_request and "website" not in text and "web site" not in text:
            try:
                # Extract Topic
                match = re.search(r'\b(build|create|design|make)\s+(?:an?\s+)?(?!.*\b(?:document|report|file|folder)\b)(?:[a-z0-9_-]+\s+){0,3}(?:webpage|web page|page)\b', text)
                topic = text[match.end():].strip()
                topic = topic.replace("about", "").replace("for", "").strip()
                if not topic: topic = "JARVIS Interface"
                
                self._respond(f"Initializing local web designer module for '{topic}'...")
                time.sleep(1.2)
                
                # 2. Design Archetypes Array
                archetypes = [
                    {
                        "name": "Stark Industries / Iron Man",
                        "bg": "#050505",
                        "text": "#00f3ff",
                        "font": "'Courier New', Courier, monospace",
                        "container_bg": "#0a0a0a",
                        "border": "1px solid #00f3ff",
                        "shadow": "0 0 20px rgba(0, 243, 255, 0.2)",
                        "decoration": '<div class="reactor"></div>',
                        "css_extra": """
                            .reactor {
                                width: 120px; height: 120px; border-radius: 50%;
                                border: 5px solid #00f3ff; box-shadow: 0 0 50px #00f3ff;
                                margin: 30px auto; animation: spin 4s linear infinite;
                            }
                            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                        """
                    },
                    {
                        "name": "Cyberpunk Grid",
                        "bg": "#0f051d",
                        "text": "#ff007f",
                        "font": "'Orbitron', sans-serif",
                        "container_bg": "#180b30",
                        "border": "2px solid #ff007f",
                        "shadow": "0 0 25px #ff007f, inset 0 0 10px #ff007f",
                        "decoration": '<div class="grid-line"></div><div class="pulse-core"></div>',
                        "css_extra": """
                            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');
                            .pulse-core {
                                width: 60px; height: 60px; border-radius: 50%;
                                background-color: #ff007f; box-shadow: 0 0 30px #ff007f;
                                margin: 30px auto; animation: pulse 2s infinite alternate;
                            }
                            @keyframes pulse { 0% { transform: scale(0.8); opacity: 0.6; } 100% { transform: scale(1.2); opacity: 1; } }
                            .grid-line {
                                width: 100%; height: 2px; background: linear-gradient(90deg, transparent, #ff007f, transparent);
                                margin: 15px 0;
                            }
                        """
                    },
                    {
                        "name": "Minimalist Obsidian",
                        "bg": "#121212",
                        "text": "#d4af37",
                        "font": "'Playfair Display', serif",
                        "container_bg": "#1c1c1c",
                        "border": "1px solid #333333",
                        "shadow": "0 10px 30px rgba(0,0,0,0.5)",
                        "decoration": '<div class="gold-line"></div>',
                        "css_extra": """
                            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&display=swap');
                            .gold-line {
                                width: 80px; height: 1px; background-color: #d4af37;
                                margin: 30px auto;
                            }
                        """
                    },
                    {
                        "name": "Emerald Matrix",
                        "bg": "#020a02",
                        "text": "#00ff00",
                        "font": "'Lucida Console', Monaco, monospace",
                        "container_bg": "#051505",
                        "border": "1px dashed #00ff00",
                        "shadow": "0 0 15px rgba(0, 255, 0, 0.3)",
                        "decoration": '<div class="matrix-rain">1010110101001</div>',
                        "css_extra": """
                            .matrix-rain {
                                font-family: monospace; font-size: 1.5em; text-shadow: 0 0 5px #00ff00;
                                margin: 30px auto; animation: blink 1s infinite;
                            }
                            @keyframes blink { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
                        """
                    },
                    {
                        "name": "Synthwave Sunset",
                        "bg": "linear-gradient(180deg, #1f1135 0%, #0c081e 100%)",
                        "text": "#ff8a00",
                        "font": "'Inter', sans-serif",
                        "container_bg": "rgba(25, 15, 48, 0.85)",
                        "border": "1px solid rgba(255, 138, 0, 0.4)",
                        "shadow": "0 8px 32px 0 rgba(229, 46, 113, 0.25)",
                        "decoration": '<div class="sunset-disc"></div>',
                        "css_extra": """
                            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap');
                            .sunset-disc {
                                width: 100px; height: 100px; border-radius: 50%;
                                background: linear-gradient(180deg, #ff8a00 0%, #e52e71 100%);
                                box-shadow: 0 0 35px rgba(255, 138, 0, 0.4);
                                margin: 30px auto;
                            }
                        """
                    }
                ]
                
                style = random.choice(archetypes)
                self._respond(f"Applying styling archetype: '{style['name']}'...")
                time.sleep(1.2)
                
                self._respond("Generating CSS stylesheet and custom visual classes...")
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{topic.upper()} - JARVIS ARCHIVE</title>
    <style>
        body {{ background: {style['bg']}; color: {style['text']}; font-family: {style['font']}; text-align: center; margin-top: 50px; }}
        h1 {{ font-size: 3em; text-shadow: 0 0 10px {style['text']}; }}
        p {{ font-size: 1.2em; color: {style['text']}; max-width: 600px; margin: 20px auto; opacity: 0.85; }}
        .container {{ border: {style['border']}; padding: 25px; display: inline-block; background: {style['container_bg']}; box-shadow: {style['shadow']}; border-radius: 12px; }}
        {style['css_extra']}
    </style>
</head>
<body>
    <div class="container">
        {style['decoration']}
        <h1>{topic.upper()}</h1>
        <p>GENERATED BY JARVIS SYSTEM.<br>SECURE DATA VISUALIZATION.</p>
        <p>This is a generated web interface dedicated to {topic}. All systems nominal.</p>
    </div>
</body>
</html>
"""
                time.sleep(1.5)
                
                self._respond("Compiling secure data visualization containers...")
                time.sleep(1.0)
                
                # Resolve PROJECTS path, create separate folder, and save index.html
                projects_dir = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', 'PROJECTS')
                clean_topic = re.sub(r'[\\/*?:"<>|]', "", topic)
                folder_name = f"{clean_topic.replace(' ', '_')}_Webpage"
                page_dir = os.path.join(projects_dir, folder_name)
                os.makedirs(page_dir, exist_ok=True)
                
                file_path = os.path.join(page_dir, "index.html")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                self._respond(f"Webpage successfully compiled and saved in PROJECTS folder under '{folder_name}'. Launching preview.")
                os.startfile(file_path)
                return False
            except Exception as e:
                print(f"Web Gen Error: {e}")
                self._respond("Failed to compile HTML assets.")
                return False

        # ==========================================
        # 👁️ VISUAL OVERRIDE (TRUE HD MODE)
        # ==========================================
        visual_triggers = ["show me", "display", "give me", "find", "search", "look for"]
        image_words = ["images", "image", "picture", "pictures", "photo", "photos", "diagram", "diagrams"]
        conversational_triggers = ["tell", "who", "what", "why", "how", "explain", "describe", "know", "write", "information", "info", "details", "about", "her", "him", "it", "them", "this", "that", "she", "he", "other", "more", "another"]
        
        has_conversational_intent = any(ct in text for ct in conversational_triggers)
        
        if any(vt in text for vt in visual_triggers) and any(iw in text for iw in image_words) and not has_conversational_intent:
            # 1. CLEAN TOPIC
            topic = text
            garbage_words = visual_triggers + image_words + ["an", "of", "the", "some", "related to", "about", "for"]
            for word in garbage_words:
                pattern = r'\b' + re.escape(word) + r'\b'
                topic = re.sub(pattern, '', topic)
            topic = " ".join(topic.split()) 
            
            if topic:
                self._respond(f"Retrieving high-resolution image of {topic}...")
                print(f"🎨 JARVIS: Fetching HD Image for '{topic}'...")

                try:
                    import requests
                    from PIL import Image
                    from io import BytesIO
                    from ddgs import DDGS # Use DDG for direct HD links

                    # 2. SEARCH FOR HD IMAGE
                    with DDGS() as ddgs:
                        search_term = f"{topic} high quality"
                        results = list(ddgs.images(search_term, max_results=1))
                        
                    if results:
                        img_url = results[0]['image'] 
                        print(f"🔗 Found HD URL: {img_url}")

                        # 3. DOWNLOAD & SHOW
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
                        img_data = requests.get(img_url, headers=headers, timeout=10).content
                        
                        image = Image.open(BytesIO(img_data))
                        image.show() 
                        self._respond(f"Displaying image.")
                    else:
                        self._respond("I couldn't find a high-res image. Opening browser.")
                        webbrowser.open(f"https://www.google.com/search?q={topic}&tbm=isch")

                except Exception as e:
                    print(f"Image Error: {e}")
                    self._respond("Network error while downloading. Opening browser.")
                    webbrowser.open(f"https://www.google.com/search?q={topic}&tbm=isch")
                
                return False

        # ==========================================
        # 👁️ VISION (CAMERA)
        # ==========================================
        if "what do you see" in text:
            path = self.vision.capture_image()
            if path:
                self._respond("Analyzing...")
                self._respond(self.brain.get_response("Describe image", image_path=path))
            return False
        
        # ==========================================
        # 🧠 MEMORY COMMANDS
        # ==========================================
        if "remember that" in text or "save this info" in text:
            fact = text.replace("remember that", "").replace("save this info", "").strip()
            self.memory_brain.remember(fact, metadata={"source": "user_voice"})
            self._respond(f"I have stored that in my long-term memory: '{fact}'")
            return False

        # ==========================================
        # 📂 LEVEL 2: FILES & FOLDERS (Migrated to skills/file_management.py)
        # ==========================================

        # ==========================================
        # 📝: DOCUMENT GENERATION
        # ==========================================
        if "create a document" in text or "make a report" in text or "write a file" in text:
            # 1. Extract Topic
            topic = text.replace("create a document", "").replace("make a report", "").replace("write a file", "").replace("about", "").replace("on", "").strip()
            
            if not topic:
                self._respond("What is the topic?")
                topic = self._force_listen()
            
            if not topic: return False

            # 2. Initialize Agents
            from agent_module import MemoryAgent, DocumentAgent
            mem_agent = MemoryAgent()
            doc_agent = DocumentAgent()
            
            # 3. Check Memory for Context
            self._respond(f"Researching {topic}...")
            context = mem_agent.recall(topic)
            if "No relevant" in context: context = ""

            # 4. Ask for Format
            self._respond("PDF, Word, or Text format?")
            format_resp = self._force_listen() or "pdf"
            
            file_type = "pdf"
            if "word" in format_resp.lower() or "doc" in format_resp.lower(): file_type = "docx"
            elif "text" in format_resp.lower(): file_type = "txt"

            # 5. Generate & Save
            self._respond("Writing document...")
            content = doc_agent.generate_content(topic, context)
            path = doc_agent.create_file(topic, content, file_type)
            
            if path:
                self._respond(f"Saved to Jarvis Documents folder. Opening now.")
                os.startfile(path)
            else:
                self._respond("Error saving file.")
                
            return False
        
        # [Note: Media block has been migrated to dynamic skills/media_skill.py]

        # ==========================================
        # ⌨️ LEVEL 4: SYSTEM AUTOMATION
        # ==========================================
        if "open" in text and "folder" not in text and "file" not in text and "memory" not in text:
            word_count = len(text.split())
            if word_count < 5:
                self._respond(self.automation.open_app(text))
                return False

        if "close" in text and "folder" not in text:
            word_count = len(text.split())
            if word_count < 5:
                self._respond(self.automation.close_app(text))
                return False

        # --- Window Focus & Listing (pywinauto Upgrades) ---
        if "focus window" in text or "activate window" in text or "switch to window" in text:
            name = text.replace("focus window", "").replace("activate window", "").replace("switch to window", "").strip()
            if name:
                msg = self.automation.activate_window(name)
                self._respond(msg)
            else:
                self._respond("Which window should I bring to the front, Sir?")
            return False

        if "list open windows" in text or "show open windows" in text or "list active windows" in text:
            self._respond("Scanning the desktop for active windows...")
            windows = self.automation.get_open_windows()
            if windows:
                formatted_list = ", ".join(windows[:10])
                self._respond(f"Here are the active windows: {formatted_list}")
            else:
                self._respond("I couldn't find any visible windows, Sir.")
            return False

        # --- Autonomous Browser Agent (Web Upgrades) ---
        if any(w in text for w in ["browse web", "search online for", "autonomous browser", "web agent"]):
            goal = text.replace("browse web", "").replace("search online for", "").replace("autonomous browser", "").replace("web agent", "").replace("about", "").strip()
            if not goal:
                self._respond("What goal would you like me to accomplish on the web, Sir?")
                goal = self._force_listen()
                
            if goal:
                self._respond(f"Initializing web agent to accomplish goal: '{goal}'. Launching browser...")
                
                def run_browser_agent():
                    from agent_module import BrowserAgent
                    agent = BrowserAgent()
                    def log_cb(msg):
                        try:
                            from jarvis import log_to_dashboard
                            log_to_dashboard("system", f"🌐 [BrowserAgent]: {msg}")
                        except:
                            pass
                    
                    final_answer = agent.execute_goal(goal, log_callback=log_cb)
                    self._respond(f"Web agent completed the goal. Final response: {final_answer}")
                    
                threading.Thread(target=run_browser_agent, daemon=True).start()
            return False

        if (text.startswith("write ") or text.startswith("type ")) and not (text.startswith("types ") or text.startswith("type of ") or text.startswith("types of ")):
            self._respond("Typing...")
            self.automation.type_text(text)
            return False

        master_triggers = [
            "new tab", "close tab", "switch tab", "refresh", "incognito", "history", "downloads",
            "zoom", "scroll", "reset zoom",
            "minimise", "maximise", "close window", "switch window", "lock screen", "show desktop",
            "select all", "copy", "paste", "save", "undo", "redo", "enter", "delete", "clear text", "remove text",
            "screenshot", "task manager", "settings", "file explorer", "run dialog", "clipboard", "emoji", "control panel",
            "magnifier", "narrator", "on-screen keyboard", "brightness", "fullscreen",
            "recycle bin", "documents folder", "pictures folder", "videos folder"
        ]

        if any(trigger in text for trigger in master_triggers):
            self._respond("Executing.")
            msg = self.automation.perform_action(text)
            if "Screenshot" in msg: self._respond(msg)
            return False
        
        # [Note: Recording block has been migrated to dynamic skills/recorder_skill.py]

        # ==========================================
        # 📰 LEVEL 7: NEWS ANCHOR
        # ==========================================
        if "tell me the news" in text or "tech news" in text:
            from agent_module import NewsAgent
            news_agent = NewsAgent()
            self._respond("Fetching the latest headlines from the quantum network...")
            summary = news_agent.get_tech_news()
            self._respond(summary)
            return False

        # ==========================================
        # 📅 LEVEL 8: SECRETARY (Reminders)
        # ==========================================
        if "set a reminder" in text:
            self._respond("What is the task?")
            task = self._force_listen()
            self._respond("At what time? (Say 5 PM or 17:00)")
            time_str = self._force_listen()
            
            # Basic parsing logic (Simple version)
            # You might need to convert "5 pm" to "17:00" logic here
            from agent_module import SecretaryAgent
            sec_agent = SecretaryAgent()
            res = sec_agent.add_reminder(task, time_str)
            self._respond(res)
            return False
        
        # [Note: WhatsApp block has been migrated to dynamic skills/whatsapp_skill.py]

        # [Note: Email block has been migrated to dynamic skills/email_skill.py]
        
        # ==========================================
        # 🏗️  MULTI-AGENT FACTORY (CREWAI INTEGRATION)
        # ==========================================
        # This has been successfully routed via Semantic Intent Routing to the IterativeProjectAgent above.
        # Retaining the old logic block condition so it doesn't break syntax, but it will never be reached 
        # because the intent router catches it first at the top of process_command.
        is_site_request = False 
        if is_site_request:
            # STEP 1: INITIATION
            match = re.search(r'\b(build|create|design|make)\s+(?:an?\s+)?(?!.*\b(?:document|report|file|folder)\b)(?:[a-z0-9_-]+\s+){0,3}(?:website|web site|project)\b', text)
            topic = text[match.end():].strip()
            topic = topic.replace("about", "").replace("for", "").replace("a ", "").strip()
            if not topic: topic = "Business"
            
            project_name = f"{topic.replace(' ', '_')}_Project"
            project_dir = os.path.join(get_desktop_path(), "PROJECTS", project_name)
            
            self._respond(f"Initiating Multi-Agent CrewAI Factory for {topic}.")
            self._respond("My engineering team is assembling the architecture. Please hold.")
            
            try:
                import subprocess
                from config import API_KEYS_POOL
                
                # Select a random API key from JARVIS's pool to avoid hitting limits
                api_key = random.choice(API_KEYS_POOL)
                
                # The factory directory
                factory_dir = os.path.join(get_desktop_path(), "PROJECTS", "Multi_Agent_Factory")
                
                # Call the uv environment
                uv_executable = "uv" # Assumes uv is on path
                cmd = [
                    uv_executable, "run", "main.py",
                    "--topic", topic,
                    "--dir", project_dir,
                    "--api_key", api_key
                ]
                
                # Run the subprocess and read stdout line by line
                print(f"🤖 JARVIS: Spawning CrewAI Subprocess...")
                process = subprocess.Popen(
                    cmd, 
                    cwd=factory_dir, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8', 
                    errors='ignore',
                    bufsize=1
                )

                pm_started = False
                coder_started = False
                qa_started = False
                last_report_time = time.time()

                for line in process.stdout:
                    print(line, end='') # Stream to console logs
                    line_lower = line.lower()
                    current_time = time.time()
                    
                    if "senior product manager" in line_lower and not pm_started:
                        if "working on" in line_lower or "task" in line_lower:
                            self._respond("Product Manager is starting competitor trends research and software specs design.")
                            pm_started = True
                            last_report_time = current_time
                            
                    elif "senior python engineer" in line_lower and not coder_started:
                        if "working on" in line_lower or "task" in line_lower:
                            self._respond("Product Manager finished research. Software Engineer is now writing the code files to disk.")
                            coder_started = True
                            last_report_time = current_time
                            
                    elif "quality assurance engineer" in line_lower and not qa_started:
                        if "working on" in line_lower or "task" in line_lower:
                            self._respond("Code files successfully compiled. QA reviewer is now performing syntax audits.")
                            qa_started = True
                            last_report_time = current_time

                    # Periodically report activity (every 20 seconds) to ensure the user knows it's alive
                    elif current_time - last_report_time > 20:
                        if "using tool" in line_lower or "tool use" in line_lower or "tool call" in line_lower:
                            self._respond("The building agent is currently calling a tool to proceed with the project build.")
                            last_report_time = current_time
                        elif "thought:" in line_lower:
                            self._respond("The agent is actively analyzing requirements and planning the next stage.")
                            last_report_time = current_time
                        elif "entering new crewagentexecutor chain" in line_lower:
                            self._respond("Entering new agent executor phase.")
                            last_report_time = current_time
                        else:
                            self._respond("The multi-agent factory is working on compiling the website files...")
                            last_report_time = current_time

                process.wait()
                
                if process.returncode == 0:
                    self._respond(f"Project built successfully! The files are saved in the PROJECTS folder under {project_name}.")
                    os.startfile(project_dir)
                else:
                    self._respond("The engineering team encountered an error during compilation.")
                    
            except Exception as e:
                self._respond("Failed to launch the Multi-Agent Factory.")
                print(f"Subprocess Error: {e}")
                
            return False
        
        # ==========================================
        # 🐙 GITHUB HANDOVER (Direct Trigger)
        # ==========================================
        if "push to github" in text or "deploy to github" in text:
            if not hasattr(self, 'project_agent') or self.project_agent is None or self.project_agent.project_path is None:
                self._respond("Which project would you like to deploy? Please say the name of the project.")
                project_name = self._force_listen()
                if project_name:
                    self.project_agent = ProjectAgent()
                    path = self.project_agent.find_project(project_name)
                    if path:
                        self.project_agent.project_path = path
                        self.project_agent.project_name = os.path.basename(path)
                    else:
                        self._respond("I couldn't find that project in your archives.")
                        return False
                else:
                    return False
            
            self._respond(f"Do you give me permission to create a repository for '{self.project_agent.project_name}' on your GitHub and upload the files? Say yes or no.")
            confirm = self._force_listen()
            if confirm and any(w in confirm.lower() for w in ["yes", "yep", "sure", "ok", "yeah"]):
                self._respond("Generating README file...")
                readme_path = os.path.join(self.project_agent.project_path, "README.md")
                if not os.path.exists(readme_path):
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(f"# {self.project_agent.project_name}\n\nAutonomously generated by JARVIS AI.\n")
                
                self._respond("Creating remote repository and pushing files...")
                github_msg = self.project_agent.push_to_github()
                self._respond(github_msg)
                
                try:
                    url_match = re.search(r'https://github.com/\S+', github_msg)
                    if url_match:
                        webbrowser.open(url_match.group(0))
                except:
                    pass
            else:
                self._respond("GitHub deployment cancelled.")
            return False

        # ==========================================
        # 🐙 GITHUB DELETION / DROP REPO (Direct Trigger)
        # ==========================================
        if "delete github repository" in text or "drop github repository" in text or "delete repository" in text or "drop repository" in text:
            # Extract repository name from the text
            repo_name = text.replace("delete github repository", "").replace("drop github repository", "").replace("delete repository", "").replace("drop repository", "").strip()
            
            if not repo_name:
                self._respond("Which repository would you like me to delete? Please say the name of the repository.")
                repo_name = self._force_listen()
            
            if repo_name:
                repo_name = repo_name.replace(" ", "_")
                self._respond(f"Sir, deleting a repository is destructive. Do you give me permission to delete '{repo_name}' from your GitHub account? Say yes or no.")
                confirm = self._force_listen()
                if confirm and any(w in confirm.lower() for w in ["yes", "yep", "sure", "ok", "yeah"]):
                    self._respond(f"Deleting repository '{repo_name}'...")
                    agent = ProjectAgent()
                    result = agent.delete_github_repo(repo_name)
                    self._respond(result)
                else:
                    self._respond("Deletion cancelled.")
            return False

        # ==========================================
        # 📂 PROJECT LAUNCHER (Recall)
        # ==========================================
        if "open project" in text:
            name = text.replace("open project", "").strip()
            self._respond(f"Searching archives for {name}...")
            
            try:
                temp_agent = ProjectAgent() 
                path = temp_agent.find_project(name)
                
                if path:
                    self._respond("Project found. Launching server.")
                    temp_agent.project_path = path
                    url = temp_agent.launch_with_autofix() # Updated
                    webbrowser.open(url)
                else:
                    self._respond("Project not found.")
            except Exception as e:
                print(e)
                self._respond("Error opening project.")
            return False
        
        # ==========================================
        # 🧠 AI CONVERSATION
        # ==========================================
        
        # Check for YouTube links to inject transcript context
        query_text = text
        yt_match = re.search(r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})", original_text)
        if yt_match:
            video_id = yt_match.group(1)
            self._respond("Extracting YouTube video transcript, please hold...")
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                transcript_list = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
                yt_transcript = " ".join([entry['text'] for entry in transcript_list])
                print(f"📹 [YOUTUBE SYSTEM]: Successfully fetched transcript for video ID: {video_id} ({len(yt_transcript)} characters)")
                query_text = f"User Request: {text}\n\n[YouTube Transcript Context (Video ID: {video_id})]\n{yt_transcript}\n[End YouTube Transcript Context]"
            except Exception as e:
                print(f"⚠️ YouTube Transcript Error: {e}")
                self._respond("I was unable to retrieve the transcript for this video. It may not have subtitles or they might be disabled, Sir.")

        active_window = self.automation.get_active_window_title() if hasattr(self.automation, 'get_active_window_title') else ""
        context = f"{self.last_topic}. User is looking at: {active_window}" if active_window else self.last_topic

        # Intercept queries about JARVIS itself to answer without invoking the AI brain
        self_response = identity.handle_self_query(text)
        if self_response:
            self._respond(self_response)
            return True

        # 1. Get raw response (Force Anti-Code)
        force_tag = " IMPORTANT: Use the tag [IMAGE: <topic>] for visual explanations. Do NOT write code."
        response = self.brain.get_response(query_text + force_tag, context=context)

        # 2. Process Response (Holograms & Filters)
        if response:
            try:
                # B) Clean Up HTML and Code
                response = re.sub(r'<.*?>', '', response).strip() 
                if "MEMORY:" in response: 
                    response = response.split("MEMORY:")[0].strip()
                if "```" in response: 
                    response = response.split("```")[0].strip()
            except Exception as e:
                print(f"⚠️ Cleaning Error: {e}")
               
        if response and len(response) > 20: 
            self.last_topic = f"User asked: {text}. You answered: {response[:100]}..."

        self._respond(response)
        
        # Trigger Self-Learning asynchronously from this conversation turn
        try:
            from memory_moduler import MemorySystem
            MemorySystem().analyze_and_learn_from_chat(original_text, response)
        except Exception as sle:
            print(f"⚠️ Self-learning trigger failed: {sle}")
            
        return True # STAY AWAKE (Main loop will auto-sleep if user is silent)

    def run(self):
        # --- NEW ADDITION: AUDIO FIX ---
        time.sleep(5) # Waits for Proactive voice to finish before greeting
        # -------------------------------
        self._morning_briefing()
        
        WAKE_WORD = "jarvis"
        print(f"💤 Standby Mode. Say '{WAKE_WORD}' to wake me up...")
        
        wake_recognizer = sr.Recognizer()
        wake_microphone = None
        
        while True:
            try:
                if wake_microphone is None:
                    wake_microphone = sr.Microphone()
                
                try:
                    voice_queue.join()
                except Exception:
                    pass
                with wake_microphone as source:
                    wake_recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    try:
                        audio = wake_recognizer.listen(source, timeout=5, phrase_time_limit=3)
                        text = wake_recognizer.recognize_google(audio).lower()
                        print(f"👂 Heard: {text}")
                    except sr.WaitTimeoutError:
                        text = ""
                    except sr.UnknownValueError:
                        text = ""
                    except Exception:
                        text = ""

            except Exception as e:
                print(f"⚠️ [STANDBY ERROR]: {e}")
                wake_microphone = None
                time.sleep(1)
                text = ""

            if WAKE_WORD in text:
                self._play_chime() 
                self._respond("Yes, Sir?")
                
                active = True
                while active:
                    print("🔴 ACTIVE MODE: Waiting for command...")
                    command = self._listen_for_command()
                    
                    if command:
                        try:
                            stay_awake = self.process_command(command)
                            
                            if stay_awake:
                                print("❓ Conversation continuing...")
                            else:
                                print("✅ Command done. Returning to Standby.")
                                active = False
                        except Exception as e:
                            print(f"❌ Error: {e}")
                            active = False
                    else:
                        print("💤 Timeout. Returning to Standby.")
                        active = False
            else:
                pass

def ensure_ollama_running():
    print("🧠 [SYSTEM]: Checking Ollama status in background...")
    import requests
    import subprocess
    import config
    import os
    import time
    
    url_tags = config.OLLAMA_URL.replace("/api/generate", "/api/tags")
    try:
        resp = requests.get(url_tags, timeout=2.0)
        if resp.status_code == 200:
            print("🧠 [SYSTEM]: Ollama is online and connected.")
            return
    except Exception:
        pass
        
    print("🚀 [SYSTEM]: Local Ollama server is offline. Attempting to start it silently...")
    try:
        ollama_bin = "ollama"
        default_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Ollama\ollama.exe")
        if os.path.exists(default_path):
            ollama_bin = default_path
            
        subprocess.Popen(
            [ollama_bin, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Poll the server for up to 10 seconds to confirm connection
        for _ in range(10):
            try:
                resp = requests.get(url_tags, timeout=1.0)
                if resp.status_code == 200:
                    print("🧠 [SYSTEM]: Ollama server started successfully and connected.")
                    return
            except Exception:
                pass
            time.sleep(1.0)
        print("⚠️ [SYSTEM]: Ollama server started in background but was slow to connect.")
    except Exception as e:
        print(f"❌ [SYSTEM]: Failed to automatically launch Ollama: {e}")

if __name__ == "__main__":
    # 0. Start OLLAMA BACKGROUND LAUNCHER
    t_ollama = threading.Thread(target=ensure_ollama_running)
    t_ollama.daemon = True
    t_ollama.start()

    # 1. Start PROACTIVE BACKGROUND BRAIN
    background_brain = ProactiveAgent(voice_queue=voice_queue, log_to_dashboard_cb=log_to_dashboard)
    t = threading.Thread(target=background_brain.start_monitoring)
    t.daemon = True 
    t.start()

    app = JARVIS()
    app.run()