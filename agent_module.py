import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import os
import time
import subprocess
import json
import git
import shutil
import threading # NEW: For background recording
import cv2  # NEW: For Video Recording
import pyaudio  # NEW: For Audio Recording
import wave     # NEW: For Saving Audio
import pyautogui  # For Screen Capture
from PIL import Image  # For Image Processing
from pyngrok import ngrok
from ddgs import DDGS
from github import Github
from config import API_KEYS_POOL
import google.generativeai as genai
from fpdf import FPDF  # For Generating Project PDFs
from docx import Document as WordDoc
from docx.shared import Pt, RGBColor
import keyboard

# --- CONFIGURE AI (Rotating Model Wrapper to support API_KEYS_POOL) ---
class RotatingModel:
    def __init__(self, model_name):
        self.model_name = model_name

    def generate_content(self, contents):
        import google.generativeai as genai
        from config import API_KEYS_POOL
        
        last_error = None
        for i, key in enumerate(API_KEYS_POOL):
            try:
                genai.configure(api_key=key)
                m = genai.GenerativeModel(self.model_name)
                response = m.generate_content(contents)
                return response
            except Exception as e:
                last_error = e
                print(f"⚠️ agent_module: Key #{i+1} failed: {e}. Rotating...")
                continue
        raise Exception(f"All keys in pool failed. Last error: {last_error}")

# ✅ PRIMARY MODEL: Gemini 2.5 Flash-Lite (Standard for 2026)
model = RotatingModel('gemini-2.5-flash-lite')

# ✅ FALLBACK MODEL: Gemini 2.0 Flash-Lite (Legacy Backup for Timeouts)
fallback_model = RotatingModel('gemini-2.0-flash-lite')

def clean_json_loads(s):
    """Robust JSON parser that tolerates unescaped backslashes, trailing commas, and raw control characters from LLMs."""
    import re
    import json
    
    # Remove markdown code block fences if present
    s = re.sub(r'^```json\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s*```$', '', s, flags=re.IGNORECASE)
    s = s.strip()
    
    # 1. Double escape backslashes that are not part of a valid escape sequence
    s = re.sub(r'\\(?![bfnrt"/\\]|u[0-9a-fA-F]{4})', r'\\\\', s)
    
    # 2. Character-by-character scan to escape unescaped control characters inside string values
    result = []
    in_string = False
    escape = False
    for char in s:
        if in_string:
            if escape:
                result.append(char)
                escape = False
            elif char == '\\':
                result.append(char)
                escape = True
            elif char == '"':
                result.append(char)
                in_string = False
            elif char == '\n':
                result.append('\\n')
            elif char == '\r':
                result.append('\\r')
            elif char == '\t':
                result.append('\\t')
            else:
                result.append(char)
        else:
            result.append(char)
            if char == '"':
                in_string = True
    cleaned = "".join(result)
    
    # 3. Remove trailing commas before closing braces/brackets
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
    
    try:
        return json.loads(cleaned, strict=False)
    except Exception as e:
        try:
            import ast
            return ast.literal_eval(cleaned)
        except:
            raise e

# =========================================================================
# 🎥 NEW CLASS: RECORDER AGENT (Audio & Video)
# =========================================================================
class RecorderAgent:
    def __init__(self):
        self.doc_dir = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', 'jarvis documents')
        if not os.path.exists(self.doc_dir): os.makedirs(self.doc_dir)
        self.is_recording = False

    def start_video_recording(self, filename="video_capture"):
        self.is_recording = True
        clean_name = filename.replace(" ", "_")
        filepath = os.path.join(self.doc_dir, f"{clean_name}.avi")
        
        def record_thread():
            cap = cv2.VideoCapture(0)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(filepath, fourcc, 20.0, (640, 480))
            print(f"🎥 Recording Video... (Say 'Stop Video' to end)")
            try:
                while self.is_recording:
                    ret, frame = cap.read()
                    if ret:
                        out.write(frame)
                        time.sleep(0.01) # Small sleep to prevent CPU hogging
                    else: break
            finally:
                cap.release()
                out.release()
                print(f"✅ Video Saved: {filepath}")

        threading.Thread(target=record_thread).start()
        return filepath

    def start_screen_recording(self, filename="screen_capture"):
        self.is_recording = True
        clean_name = filename.replace(" ", "_")
        filepath = os.path.join(self.doc_dir, f"{clean_name}.avi")
        
        def record_thread():
            import numpy as np
            from PIL import ImageGrab
            
            screen = ImageGrab.grab()
            width, height = screen.size
            
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(filepath, fourcc, 10.0, (width, height))
            print(f"🎥 Recording Screen... (Say 'Stop Screen Recording' to end)")
            try:
                while self.is_recording:
                    img = ImageGrab.grab()
                    frame = np.array(img)
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    out.write(frame_bgr)
                    time.sleep(0.1)
            finally:
                out.release()
                print(f"✅ Screen Recording Saved: {filepath}")

        threading.Thread(target=record_thread).start()
        return filepath


    def start_audio_recording(self, filename="audio_record"):
        self.is_recording = True
        clean_name = filename.replace(" ", "_")
        filepath = os.path.join(self.doc_dir, f"{clean_name}.wav")
        
        chunk = 1024
        sample_format = pyaudio.paInt16
        channels = 1
        fs = 44100
        p = pyaudio.PyAudio()
        stream = None
        frames = []
        try:
            stream = p.open(format=sample_format, channels=channels, rate=fs, frames_per_buffer=chunk, input=True)
            print("🎙️ RECORDING AUDIO... (Press 'ENTER' in terminal to stop)")
            while self.is_recording:
                data = stream.read(chunk)
                frames.append(data)

                if keyboard.is_pressed('enter'):
                    print("⏹️ Stopping Audio Recording...")
                    self.is_recording = False
                    time.sleep(0.5)
        except Exception as e:
            print(f"Audio Recording Error: {e}")
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            try:
                p.terminate()
            except:
                pass
        
        try:
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b''.join(frames))
            wf.close()
            print(f"✅ Audio Saved: {filepath}")
        except Exception as e:
            print(f"Error saving wave file: {e}")
        return filepath

    def stop_recording(self):
        self.is_recording = False

# =========================================================================
# 📰 NEW CLASS: NEWS AGENT
# =========================================================================
class NewsAgent:
    def get_tech_news(self):
        print("📰 Fetching latest tech news...")
        results = []
        
        def do_search():
            nonlocal results
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text("latest technology news artificial intelligence 2026", max_results=5))
            except Exception as e:
                print(f"⚠️ News search warning: {e}")
                
        search_thread = threading.Thread(target=do_search)
        search_thread.daemon = True
        search_thread.start()
        search_thread.join(timeout=8.0)
        
        if not results:
            return "I could not reach the news servers due to a connection timeout."
            
        try:
            news_text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            prompt = f"Act as a Tech News Anchor. Summarize:\n{news_text}"
            return model.generate_content(prompt).text
        except: 
            return "I could not compile the latest technology headlines."

# =========================================================================
# 📅 NEW CLASS: SECRETARY AGENT (Reminders)
# =========================================================================
class SecretaryAgent:
    def __init__(self):
        self.reminders_file = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', 'jarvis_reminders.json')
        if not os.path.exists(self.reminders_file):
            with open(self.reminders_file, 'w') as f: json.dump([], f)

    def add_reminder(self, task, time_str):
        try:
            with open(self.reminders_file, 'r') as f: data = json.load(f)
        except: data = []
        data.append({"task": task, "time": time_str, "status": "pending"})
        with open(self.reminders_file, 'w') as f: json.dump(data, f)
        return f"Reminder set for {time_str}: {task}"

    def check_reminders(self):
        current_time = time.strftime("%H:%M")
        try:
            with open(self.reminders_file, 'r') as f: data = json.load(f)
        except: return None
        active = []
        for item in data:
            if item["time"] == current_time and item["status"] == "pending":
                active.append(item["task"])
                item["status"] = "completed"
        if active:
            with open(self.reminders_file, 'w') as f: json.dump(data, f)
            return f"REMINDER: {', '.join(active)}"
        return None

# =========================================================================
# 📄 CUSTOM CLASS: DARK MODE PDF ENGINE
# =========================================================================
class DarkPDF(FPDF):
    def header(self):
        # Dark Background
        self.set_fill_color(10, 10, 15)  # Almost Black
        self.rect(0, 0, 210, 297, 'F')  # Fill page

        # Neon Line
        self.set_draw_color(0, 243, 255)  # Cyan
        self.set_line_width(1)
        self.line(10, 25, 200, 25)

        # Title
        self.set_font('Courier', 'B', 10)
        self.set_text_color(0, 243, 255)  # Cyan
        self.cell(0, 10, 'JARVIS SYSTEM ARCHIVE // CLASSIFIED', 0, 0, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Courier', 'I', 8)
        self.set_text_color(100, 100, 100)  # Grey
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 243, 255)  # Cyan
        self.cell(0, 10, title.upper(), 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(220, 220, 220)  # Off-White
        # Robust encoding handling to prevent crashes on special chars
        clean_body = body.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 6, clean_body)
        self.ln(5)

    def add_code_block(self, code):
        self.set_font('Courier', '', 10)
        self.set_text_color(0, 255, 0)  # Matrix Green
        self.set_fill_color(20, 20, 20)  # Dark Grey Box
        clean_code = code.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 5, clean_code, 0, 'L', True)
        self.ln(5)

# =========================================================================
# 👁️ VISION AGENT (The Eyes)
# =========================================================================
class VisionAgent:
    """The Eyes of JARVIS: Captures and analyzes the screen."""
    def take_screenshot(self):
        screenshot_path = os.path.join(os.getcwd(), "vision_capture.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        return screenshot_path

    def analyze_screen(self, prompt="What do you see on my screen?"):
        path = self.take_screenshot()
        img = Image.open(path)
        try:
            # Using Primary Model
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            return f"Vision Error: {e}"

# =========================================================================
# 🧠 MEMORY AGENT (The Long-Term Brain - SAFE MODE)
# =========================================================================
class MemoryAgent:
    def __init__(self):
        self.working = False
        self.collection = None
        self.db_path = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', 'JARVIS_Memory')
        
        print("🧠 Initializing Memory Core...")
        
        # Windows-Safe PyTorch DLL Integrity Check via Subprocess Timeout
        pytorch_working = False
        try:
            import importlib.util
            if importlib.util.find_spec("torch") is not None and importlib.util.find_spec("chromadb") is not None:
                import subprocess
                res = subprocess.run(
                    [sys.executable, "-c", "import torch; import chromadb; print('OK')"],
                    capture_output=True,
                    text=True,
                    timeout=3.0
                )
                if res.returncode == 0 and "OK" in res.stdout:
                    pytorch_working = True
                else:
                    print("⚠️ PyTorch dynamic DLL load check failed in subprocess. Bypassing ChromaDB.")
                    pytorch_working = False
            else:
                pytorch_working = False
        except subprocess.TimeoutExpired:
            print("⚠️ PyTorch Import Timeout: Subprocess hung due to DLL loader lock. Gracefully bypassing ChromaDB.")
            pytorch_working = False
        except Exception as pe:
            print(f"⚠️ Memory pre-check error: {pe}. Bypassing ChromaDB.")
            pytorch_working = False
            
        if pytorch_working:
            try:
                import chromadb
                from chromadb.utils import embedding_functions
                
                self.client = chromadb.PersistentClient(path=self.db_path)
                self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
                self.collection = self.client.get_or_create_collection(
                    name="jarvis_long_term_memories",
                    embedding_function=self.embed_fn
                )
                self.working = True
                print("✅ Memory Core Online.")
            except Exception as e:
                print(f"⚠️ MEMORY WARNING: {e}")
                self.working = False
        else:
            self.working = False

    def remember(self, text, metadata={"type": "general"}):
        if not self.working: return "Memory Core is offline."
        print(f"🧠 Storing memory: {text}")
        try:
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[str(time.time())]
            )
            return "Memory stored."
        except: return "Failed to save."

    def recall(self, query, n_results=2):
        if not self.working: return "No relevant past memories found (Core Offline)."
        try:
            results = self.collection.query(query_texts=[query], n_results=n_results)
            memories = results['documents'][0]
            if memories: return "\n".join([f"- {m}" for m in memories])
        except: pass
        return "No relevant past memories found."

# =========================================================================
# 🛠️ PROJECT AGENT (STITCH UI + ENTERPRISE BACKEND + AGILE WORKFLOW)
# =========================================================================
class ProjectAgent:
    def __init__(self):
        self.project_name = None
        self.project_path = None
        self.server_process = None
        # Base directory for all projects
        self.base_dir = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', 'PROJECTS')
        if not os.path.exists(self.base_dir): os.makedirs(self.base_dir)

    def _log(self, log_type, message):
        """Telemetry HUD Logger that writes directly to the GUI dashboard logs."""
        # Strip emojis and non-ASCII characters safely when printing to local console to prevent Windows CP1252 crash
        try:
            safe_msg = message.encode('ascii', 'ignore').decode('ascii')
            print(f"[{log_type.upper()}] {safe_msg}")
        except:
            print(f"[{log_type.upper()}] [Message format stripped for terminal safety]")
            
        log_file = "jarvis_logs.json"
        entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "type": log_type, # "user", "jarvis", "task", "system"
            "message": f"🤖 [BUILD]: {message}" if log_type == "jarvis" else message
        }
        data = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except: pass
        data.append(entry)
        if len(data) > 50: data = data[-50:]
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"⚠️ Telemetry logger failure: {e}")

    # --- [STEP 3] MARKET ANALYSIS & REFINEMENT ---
    def consult_and_refine_requirements(self, topic, initial_reqs):
        """
        Searches top 10 websites, analyzes trends, and suggests changes.
        """
        self._log("task", f"Researching top competitor trends for '{topic}'...")
        market_data = "Market data unavailable. Using internal expert knowledge."
        
        def do_search():
            nonlocal market_data
            try:
                with DDGS() as ddgs:
                    query = f"top 10 modern {topic} website features trends 2026"
                    results = list(ddgs.text(query, max_results=5))
                if results:
                    market_data = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            except Exception as e:
                self._log("system", f"DDG Trend search warning: {e}")
                
        search_thread = threading.Thread(target=do_search)
        search_thread.daemon = True
        search_thread.start()
        search_thread.join(timeout=8.0)
        
        if search_thread.is_alive():
            self._log("system", "Research Timeout: DuckDuckGo search hung. Using offline intelligence.")

        # 2. AI Consultant Logic
        prompt = f"""
        Act as a Senior Product Manager & UX Strategist.
        Client wants: {topic} Website.
        Client Requirements: {initial_reqs}
        
        Real-World Market Trends (2026):
        {market_data}
        
        TASK:
        Compare the client's idea against the top 10 competitors.
        1. Identify one OUTDATED feature the client asked for (Suggest REMOVING it).
        2. Identify one TRENDING/CRITICAL feature the client missed (Suggest ADDING it).
        
        OUTPUT FORMAT:
        "Based on my analysis of the top 10 {topic} websites:
        ❌ REMOVE: [Feature] (Reason: [Brief Reason])
        ✅ ADD: [Feature] (Reason: [Brief Reason])"
        """
        return model.generate_content(prompt).text

    def research_market_trends(self, topic):
        """
        Searches top 5 websites, analyzes trends, and returns trend data text.
        """
        self._log("task", f"Analyzing 2026 competitor trends for '{topic}'...")
        market_data = "Market data unavailable. Using internal expert knowledge."
        
        def do_search():
            nonlocal market_data
            try:
                with DDGS() as ddgs:
                    query = f"top 10 modern {topic} website features trends 2026"
                    results = list(ddgs.text(query, max_results=5))
                if results:
                    market_data = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            except Exception as e:
                self._log("system", f"DDG Market search warning: {e}")
                
        search_thread = threading.Thread(target=do_search)
        search_thread.daemon = True
        search_thread.start()
        search_thread.join(timeout=8.0)
        
        if search_thread.is_alive():
            self._log("system", "Market search timeout. Proceeding with standard offline models.")
            
        return market_data

    def analyze_requirements(self, topic, context_reqs, trends):
        """
        Compares client idea and memories against trends and returns suggestions.
        """
        prompt = f"""
        Act as a Senior Product Manager & UX Strategist.
        Client wants: {topic} Website.
        Client Requirements: {context_reqs}
        
        Real-World Market Trends (2026):
        {trends}
        
        TASK:
        Compare the client's idea against the top 10 competitors.
        1. Identify one OUTDATED feature the client asked for (Suggest REMOVING it).
        2. Identify one TRENDING/CRITICAL feature the client missed (Suggest ADDING it).
        
        OUTPUT FORMAT:
        "Based on my analysis of the top 10 {topic} websites:
        ❌ REMOVE: [Feature] (Reason: [Brief Reason])
        ✅ ADD: [Feature] (Reason: [Brief Reason])"
        """
        return model.generate_content(prompt).text

    def save_requirements(self, project_name, final_reqs):
        """Locks the requirements into a file."""
        self.project_name = project_name.replace(" ", "_")
        self.project_path = os.path.join(self.base_dir, self.project_name)
        if not os.path.exists(self.project_path): os.makedirs(self.project_path)
        
        req_file = os.path.join(self.project_path, "requirements.txt")
        with open(req_file, "w", encoding="utf-8") as f:
            f.write(final_reqs)
        self._log("task", f"Locked project requirements saved to: {req_file}")
        return self.project_path

    # --- [STEP 4] ARCHITECTURE & BUILD (Stitch + Enterprise) ---
    def generate_initial_code(self, locked_reqs):
        """
        Generates 'Stitch-Quality' Frontend + 'Enterprise' Backend.
        """
        self._log("task", "Designing architecture: full-stack enterprise blueprint...")
        
        import random
        aesthetics = [
            "Modern warm/earthy theme, cozy color scheme tailored to the topic, rounded-3xl cards, sleek typography using 'Plus Jakarta Sans', dynamic gradient texts, clean minimal structure.",
            "Neo-Brutalism style: high-contrast layout, thick black borders (border-4 border-black), harsh drop shadows (shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]), vibrant bold color fills tailored to the theme, monospace headings using 'Share Tech Mono'.",
            "Cyberpunk Neon style: dark slate/black backgrounds, bright cyan or neon pink outlines, sharp box corners, simulated neon glow effects, tech grid lines, 'Orbitron' or monospace fonts.",
            "Minimalist Obsidian style: ultra-premium dark theme, charcoal/obsidian cards, gold/amber borders and text accents, elegant serif headers using 'Playfair Display', generous white space, luxury minimal design.",
            "Glassmorphism styling: frosted-glass transparency effects (backdrop-blur-md bg-white/10), soft pastel gradients, neon glow accents, soft rounded-2xl panels, modern sans-serif typography like 'Outfit'.",
            "Synthwave Retro Sunset: purple-to-pink gradient panels, warm amber glowing headlines, retro badges, synthwave sunset visual aesthetics, typography using 'Montserrat'.",
            "Emerald Matrix/Terminal: dark slate/green theme, monospace hacker/tech fonts, dashed/dotted border highlights, digital status readouts, clean compact terminal interfaces."
        ]
        chosen_aesthetic = random.choice(aesthetics)
        self._log("task", f"Injecting randomized frontend design archetype: {chosen_aesthetic.split(':')[0]}")
        
        system_prompt = f"""
        Act as a "God Mode" Full-Stack Developer.
        Project: {locked_reqs}
        
        --- FRONTEND RULES (GOOGLE STITCH MODE) ---
        1. UI LIBRARY: Tailwind CSS (via CDN). NO raw CSS files.
        2. AESTHETIC: {chosen_aesthetic}
        3. LAYOUT: Responsive Grid/Flexbox with navbar, hero section, dynamic menu/products, and locations.
        4. ICONS: FontAwesome CDN.
        
        --- BACKEND RULES (ENTERPRISE MODE) ---
        1. FRAMEWORK: Flask (Python).
        2. STRUCTURE: Application Factory Pattern (No single app.py).
           - run.py (Entry point, imports and runs create_app(). You MUST run the server with: app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False) to prevent the Werkzeug file watchdog from triggering loop-restarts when seeding SQLite databases.)
           - config.py (Config class with SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db')
           - app/__init__.py (Factory - defines db = SQLAlchemy(). Inside create_app() it does db.init_app(app), registers blueprints, and runs database seeding within `with app.app_context():` so db.create_all() runs safely.
             CRITICAL DATABASE SEEDING RULES FOR app/__init__.py:
             * You must import the models locally inside the seeding block to avoid circular imports and NameErrors: `from app.models import Product, Location`.
             * To check if the database is already seeded, query a specific model (do NOT query `db.Model` directly as that is invalid and raises a SQLAlchemy ArgumentError). Use: `if Product.query.first() is None:` or `if db.session.query(Product).first() is None:`.
             * Instantiate premium mock Product and Location objects and add/commit them.)
           - app/routes.py (Must use Flask Blueprints! Define a blueprint named `main = Blueprint('main', __name__)` and use `@main.route('/')`. Do NOT use `@app.route` decorators here. Register this blueprint in `app/__init__.py` using `app.register_blueprint(main)`).
           - app/models.py (SQLAlchemy Models: User, Product, Location, Order. Products and Locations must have description, price, address, address-related properties, and Unsplash image URLs).
        3. DATABASE: SQLite (production-ready schema, automatically populated with beautiful real mock products and locations during app startup).
        4. DEPENDENCIES: ONLY use standard Flask and Flask-SQLAlchemy. Do NOT use Flask-Migrate or other external Flask extensions.
        5. DEPLOYMENT: Include Dockerfile and requirements.txt.
        
        --- TEMPLATE RULES ---
        - app/templates/base.html: Premium layout with a sticky navbar, elegant Tailwind styles, FontAwesome icons, and a rich footer.
        - app/templates/index.html: Home page extending base.html. It MUST loop over `menu_items` (Product model objects) and `locations` (Location model objects) using Jinja {{% for item in menu_items %}}. In the main route in routes.py, query all products and locations and pass them. If the database query returns empty lists, provide a beautiful default list of mock dictionaries in the python route as a robust fallback.
        
        --- OUTPUT SPECIFICATION ---
        Return a valid JSON object where the keys are relative file paths and the values are their complete, premium file contents. Do NOT use placeholders. Generate the complete implementation.
        
        Example JSON Output:
        {{
            "run.py": "from app import create_app...",
            "config.py": "class Config...",
            "app/__init__.py": "...",
            "app/routes.py": "...",
            "app/models.py": "...",
            "app/templates/base.html": "...",
            "app/templates/index.html": "...",
            "Dockerfile": "...",
            "requirements.txt": "..."
        }}
        
        Return JSON ONLY. Do not write any explanations before or after the JSON.
        """
        try:
            # Use the smartest model available for architecture
            response_text = model.generate_content(system_prompt).text
            import re
            json_match = re.search(r'(\{[\s\S]*\})', response_text)
            if json_match:
                return clean_json_loads(json_match.group(1))
            else:
                clean_json = response_text.replace("```json", "").replace("```", "").strip()
                return clean_json_loads(clean_json)
        except Exception as e:
            self._log("system", f"Architecture generation error: {e}")
            return None

    def write_code_files(self, code_files):
        """Writes the generated code to the disk, creating folders as needed."""
        # Clean stale SQLite database if rewriting core app files to ensure schema updates
        if self.project_path and ("run.py" in code_files or "app/models.py" in code_files):
            db_path = os.path.join(self.project_path, "instance", "site.db")
            if os.path.exists(db_path):
                self._log("system", "Stale database schema detected. Deleting site.db for schema recreation...")
                try:
                    os.remove(db_path)
                except Exception as de:
                    self._log("system", f"Warning: Could not remove legacy database file: {de}")

        for filename, content in code_files.items():
            # Safeguard: Skip literal "filename" or "content" keys if generated by error
            if filename.lower() in ["filename", "content"]:
                print(f"⚠️ ProjectAgent: Skipping writing invalid file path '{filename}'")
                continue
            full_path = os.path.join(self.project_path, filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            if isinstance(content, list):
                content = "\n".join(content)
            with open(full_path, "w", encoding='utf-8') as f:
                f.write(content)
        self._log("task", f"Successfully wrote {len(code_files)} files to {self.project_path}")

    # --- [STEP 5] DEBUG & SELF-HEALING ---
    def attempt_auto_fix(self, error_log):
        self._log("task", "🚑 SELF-HEALING: Activating smart traceback context-gathering...")
        
        # 1. Parse traceback for python files inside the project directory
        import re
        implicated_files = set()
        
        # Use regex to find python files mentioned in the trace
        matches = re.findall(r'File "([^"]+\.py)"', error_log)
        for path in matches:
            abs_path = os.path.abspath(path)
            if abs_path.lower().startswith(os.path.abspath(self.project_path).lower()):
                rel_path = os.path.relpath(abs_path, self.project_path)
                implicated_files.add(rel_path)
                
        # Fallbacks: check common app files mentioned by name in trace
        default_files = ["run.py", "app/__init__.py", "app/routes.py", "app/models.py"]
        for f in default_files:
            if f.replace("app/", "") in error_log:
                implicated_files.add(f)
                
        if not implicated_files:
            implicated_files = set(default_files)
            
        # 2. Gather actual code context from all implicated files
        context_files = {}
        for rel_path in implicated_files:
            full_path = os.path.join(self.project_path, rel_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        context_files[rel_path] = f.read()
                except Exception as ree:
                    print(f"Error reading {rel_path} for context: {ree}")

        # Build prompt with context files
        context_str = ""
        for file_path, code in context_files.items():
            context_str += f"\n--- FILE: {file_path} ---\n{code}\n"
            
        self._log("task", f"Context gathered from files: {', '.join(context_files.keys())}")

        fix_prompt = f"""
        CRITICAL ERROR IN FLASK BLUEPRINT BLUEPRINT SYSTEM.
        
        ERROR LOG:
        {error_log}
        
        IMPLICATED CODE FILES CONTEXT:
        {context_str}
        
        TASK:
        Fix the crash. Ensure the project structure follows the Flask Application Factory and Blueprint pattern (avoid circular imports by importing models/db cleanly and registering blueprints).
        
        CRITICAL DEPENDENCY RULE:
        * ONLY use standard Flask and Flask-SQLAlchemy. Do NOT use Flask-Migrate or other external Flask extensions under any circumstances! Ensure no such imports are introduced.
        
        Return a valid JSON object where the keys are the relative file paths of the files that need to be created or updated (e.g., "app/__init__.py"), and the values are the complete updated file content strings.
        Do NOT return placeholders, do NOT return a key literally named "filename", and do NOT simplify the application to return a raw string. Render index.html with seeded data.
        
        Example JSON Output:
        {{
            "app/__init__.py": "complete fixed factory code here",
            "app/routes.py": "complete fixed routes code here"
        }}
        
        Return JSON ONLY.
        """
        try:
            res = model.generate_content(fix_prompt).text
            import re
            json_match = re.search(r'(\{[\s\S]*\})', res)
            if json_match:
                fixes = clean_json_loads(json_match.group(1))
            else:
                clean_json = res.replace("```json", "").replace("```", "").strip()
                fixes = clean_json_loads(clean_json)
                
            self.write_code_files(fixes)
            self._log("task", "✅ Surgical self-healing patches successfully compiled and applied.")
            return True
        except Exception as e:
            self._log("system", f"Self-healing agent failed to apply fix: {e}")
            return False

    # --- [STEP 6] LOCAL LAUNCH ---
    def launch_with_autofix(self):
        if self.server_process: self.server_process.kill()
        
        # 1. Clean Port 5000 of any lingering processes using psutil (Optimized System-wide check)
        self._log("task", "Checking Port 5000 to resolve any binding conflicts...")
        import psutil
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.laddr.port == 5000 and conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()
                        self._log("system", f"Releasing Port 5000: Terminated process {proc_name} (PID: {conn.pid}).")
                        # Terminate child processes as well to prevent orphan reloaders
                        for child in proc.children(recursive=True):
                            try:
                                child.kill()
                            except:
                                pass
                        proc.kill()
                    except Exception as pe:
                        pass
        except Exception as e:
            # Fallback to slower iterative approach if net_connections requires higher privilege
            self._log("system", f"net_connections scan bypassed: {e}. Falling back to process_iter...")
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for conn in proc.connections(kind='inet'):
                        if conn.laddr.port == 5000:
                            self._log("system", f"Releasing Port 5000: Terminated process {proc.info['name']} (PID: {proc.info['pid']}).")
                            proc.kill()
                except Exception:
                    pass

        self._log("task", "Initializing Enterprise Server...")
        
        # 1.5 Setup Sandbox Virtual Environment if not exists
        venv_dir = os.path.join(self.project_path, ".venv")
        if os.name == "nt":
            venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            venv_python = os.path.join(venv_dir, "bin", "python")
            
        if not os.path.exists(venv_dir) or not os.path.exists(venv_python):
            self._log("task", "Setting up isolated virtual environment sandbox...")
            subprocess.run([sys.executable, "-m", "venv", ".venv"], cwd=self.project_path)
            
            # Install dependencies in the sandbox
            req_file = os.path.join(self.project_path, "requirements.txt")
            if os.path.exists(req_file):
                self._log("task", "Installing project dependencies in sandbox (this may take a moment)...")
                # Use pip inside venv to install requirements
                subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], cwd=self.project_path)
        
        # 2. Database Seed (Enterprise Style)
        db_path = os.path.join(self.project_path, "instance", "site.db")
        if not os.path.exists(db_path):
            self._log("task", "Database site.db not found. Seeding SQLite tables in sandbox...")
            seed_cmd = "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
            subprocess.run(f'cd "{self.project_path}" && "{venv_python}" -c "{seed_cmd}"', shell=True)

        # 3. Launch Server (redirect stdout/stderr to a log file to avoid subprocess pipe buffer locks)
        log_file_path = os.path.join(self.project_path, "flask_server.log")
        try:
            self.server_log_file = open(log_file_path, "w", encoding="utf-8")
        except Exception as le:
            self._log("system", f"Warning: Could not create server log file: {le}")
            self.server_log_file = subprocess.DEVNULL

        self.server_process = subprocess.Popen(
            [venv_python, "run.py"],
            cwd=self.project_path,
            stdout=self.server_log_file,
            stderr=self.server_log_file,
            text=True
        )
        
        # Monitor for immediate startup crashes (5 sec window)
        time.sleep(5)
        if self.server_process.poll() is not None:
            # Server crashed on startup! Read log file for details
            if hasattr(self, 'server_log_file') and hasattr(self.server_log_file, 'close'):
                try: self.server_log_file.close()
                except: pass
            
            stderr_content = "Unknown launch error (Log file unavailable)."
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, "r", encoding="utf-8") as lf:
                        stderr_content = lf.read()
                except: pass
                
            self._log("system", f"Launch Failure Detected:\n{stderr_content}")
            if self.attempt_auto_fix(stderr_content):
                return self.launch_with_autofix() # Retry recursion
            else:
                return "Error: Fatal Crash Loop."
        else:
            self._log("jarvis", "Server successfully initialized and running on: http://127.0.0.1:5000")
            return "http://127.0.0.1:5000"

    # --- [STEP 7] DEPLOYMENT & PORT STORAGE ---
    def deploy_to_internet(self, database_type=None):
        self._log("task", "🌐 HANDOVER: Initializing secure public ngrok tunnel...")
        ngrok.kill()
        
        # 1. Start Tunnel
        tunnel = ngrok.connect(5000)
        public_url = tunnel.public_url
        
        # 2. Store Port & Creds (As requested)
        info_file = os.path.join(self.project_path, "deployment_manifest.txt")
        with open(info_file, "w") as f:
            f.write(f"--- PROJECT DEPLOYMENT MANIFEST ---\n")
            f.write(f"Project: {self.project_name}\n")
            f.write(f"Date: {time.ctime()}\n")
            f.write(f"Public URL: {public_url}\n")
            f.write(f"Local Port: 5000\n")
            f.write(f"Database: {database_type or 'Local SQLite'}\n")
            f.write(f"Architecture: Flask Factory + Tailwind + Docker\n")
            
        self._log("jarvis", f"Deployment Successful. Access your live website at: {public_url}")
        return public_url

    # --- UPDATER (For User Feedback Loop) ---
    def update_code(self, history, feedback):
        prompt = f"""
        User wants changes or refactoring to the existing project codebase.
        
        CONTEXT / REQUIREMENTS HISTORY:
        {history}
        
        USER FEEDBACK / REQUEST:
        {feedback}
        
        TASK:
        Implement the requested changes in the codebase.
        Ensure you maintain the Flask Application Factory pattern, Blueprints, and database auto-seeding. Do not simplify the app to bypass errors. Keep templates fully functional.
        
        CRITICAL DEPENDENCY RULE:
        * ONLY use standard Flask and Flask-SQLAlchemy. Do NOT use Flask-Migrate or other external Flask extensions under any circumstances! Ensure no such imports are introduced.
        
        Return a valid JSON object where keys are the relative file paths of the files to be created or modified (e.g., "app/routes.py", "templates/index.html") and the values are their complete, updated file content strings.
        
        Example JSON Output:
        {{
            "app/routes.py": "complete updated routes code",
            "templates/index.html": "complete updated template HTML"
        }}
        
        Return JSON ONLY.
        """
        try:
            res = model.generate_content(prompt).text
            import re
            json_match = re.search(r'(\{[\s\S]*\})', res)
            if json_match:
                return clean_json_loads(json_match.group(1))
            else:
                clean_json = res.replace("```json", "").replace("```", "").strip()
                return clean_json_loads(clean_json)
        except Exception as e:
            self._log("system", f"Update code processing error: {e}")
            return None

    def stop_server(self):
        if self.server_process:
            self._log("task", f"Stopping web server process tree (PID: {self.server_process.pid})...")
            try:
                import psutil
                parent = psutil.Process(self.server_process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except Exception as e:
                try:
                    self.server_process.kill()
                except:
                    pass
        ngrok.kill()
        self._log("task", "Web server processes and public ngrok tunnels cleanly terminated.")

    def migrate_to_cloud_db(self, cloud_url):
        """Replaces SQLite DATABASE URI in config.py of the generated project with the cloud URL."""
        if not self.project_path: return False
        config_path = os.path.join(self.project_path, "config.py")
        if not os.path.exists(config_path): return False
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            import re
            pattern = r"SQLALCHEMY_DATABASE_URI\s*=\s*['\"].*?['\"]"
            replacement = f"SQLALCHEMY_DATABASE_URI = '{cloud_url}'"
            new_content = re.sub(pattern, replacement, content)
            
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            self._log("task", f"Successfully migrated SQLite connection string to: {cloud_url}")
            return True
        except Exception as e:
            self._log("system", f"Migration to cloud database failed: {e}")
            return False

    def find_project(self, name):
        """Finds a project folder by name in the base projects directory."""
        if not os.path.exists(self.base_dir): return None
        clean_name = name.replace(" ", "_").lower()
        try:
            for item in os.listdir(self.base_dir):
                full_path = os.path.join(self.base_dir, item)
                if os.path.isdir(full_path) and item.replace(" ", "_").lower() == clean_name:
                    return full_path
            # Fuzzy match fallback
            for item in os.listdir(self.base_dir):
                full_path = os.path.join(self.base_dir, item)
                if os.path.isdir(full_path) and clean_name in item.replace(" ", "_").lower():
                    return full_path
        except Exception as e:
            print(f"Error finding project: {e}")
        return None

    # --- DOCUMENTATION ---
    def generate_project_pdf(self, requirements, trends):
        if not self.project_path: return None
        try:
            pdf = DarkPDF() # Assumes DarkPDF class exists in your file
            pdf.add_page()
            pdf.chapter_title(f"PROJECT: {self.project_name}")
            pdf.chapter_body(requirements)
            pdf.chapter_title("MARKET TRENDS")
            pdf.chapter_body(trends)
            pdf.chapter_title("ARCHITECTURE")
            pdf.chapter_body("Frontend: Tailwind CSS (Stitch Mode)\nBackend: Flask Factory Pattern\nContainer: Docker")
            doc_path = os.path.join(self.project_path, f"{self.project_name}_Manual.pdf")
            pdf.output(doc_path)
            self._log("task", f"Classified Dark PDF manual successfully generated: {doc_path}")
            return doc_path
        except Exception as e:
            self._log("system", f"PDF manual creation warning: {e}")
            return None

    # --- [STEP 8] GITHUB DEPLOYMENT (God Mode) ---
    def push_to_github(self):
        """Autonomously creates a remote repo and pushes the project code."""
        self._log("task", "🐙 JARVIS: Initiating secure GitHub Handover protocol...")
        
        try:
            import config
            if not hasattr(config, 'GITHUB_TOKEN') or not config.GITHUB_TOKEN:
                return "Sir, I need a GITHUB_TOKEN in your .env file to access your account."
                
            # 1. Authenticate with GitHub API
            from github import Auth
            auth = Auth.Token(config.GITHUB_TOKEN)
            g = Github(auth=auth)
            user = g.get_user()
            
            # 2. Create the Remote Repository
            repo_name = self.project_name
            self._log("task", f"Creating secure private repository '{repo_name}' on GitHub...")
            try:
                # JARVIS creates a private repo by default for your safety
                remote_repo = user.create_repo(repo_name, description="Autonomously generated by JARVIS AI", private=True)
            except Exception as e:
                # If a repo with this name already exists, grab it instead of crashing
                try:
                    remote_repo = user.get_repo(repo_name)
                except:
                    remote_repo = user.get_repo(f"{user.login}/{repo_name}")
                self._log("system", "Repository already exists. Preparing update sequence...")
                
            # 3. Initialize Local Git (git init)
            local_repo = git.Repo.init(self.project_path)
            
            # 4. Stage and Commit (git add . && git commit)
            local_repo.git.add(all=True)
            commit_message = f"JARVIS Auto-Commit: Completed {self.project_name} build."
            try:
                local_repo.index.commit(commit_message)
                self._log("task", "Local directory changes committed.")
            except Exception as ce:
                print(f"⚠️ Commit status: {ce} (Continuing to push...)")
            
            # 5. Link Remote and Push
            # We inject the token into the URL so JARVIS can push securely without prompts
            remote_url = f"https://{config.GITHUB_TOKEN}@github.com/{user.login}/{repo_name}.git"
            
            # Check if remote 'origin' already exists to avoid errors on updates
            if 'origin' in [r.name for r in local_repo.remotes]:
                origin = local_repo.remotes.origin
                origin.set_url(remote_url)
            else:
                origin = local_repo.create_remote('origin', remote_url)
                
            self._log("task", "Pushing local commits to remote master/main branch...")
            # Force push to main or master branch
            try:
                origin.push(refspec='master:master')
            except:
                origin.push(refspec='main:main')
                
            success_msg = f"Successfully deployed to GitHub: {remote_repo.html_url}"
            self._log("jarvis", success_msg)
            return success_msg
            
        except Exception as e:
            error_msg = f"❌ GitHub Deployment Failed: {e}"
            self._log("system", error_msg)
            return error_msg

    def delete_github_repo(self, repo_name):
        """Autonomously deletes a remote repository on GitHub."""
        self._log("task", f"🐙 JARVIS: Initiating GitHub Repository Deletion Protocol for '{repo_name}'...")
        try:
            import config
            if not hasattr(config, 'GITHUB_TOKEN') or not config.GITHUB_TOKEN:
                return "Sir, I need a GITHUB_TOKEN in your .env file to access your account."
                
            from github import Auth
            auth = Auth.Token(config.GITHUB_TOKEN)
            g = Github(auth=auth)
            user = g.get_user()
            
            try:
                repo = user.get_repo(repo_name)
            except:
                repo = user.get_repo(f"{user.login}/{repo_name}")
                
            repo.delete()
            time.sleep(2) # Give GitHub API a moment to process the deletion
            
            # Verify deletion
            try:
                try:
                    user.get_repo(repo_name)
                except:
                    user.get_repo(f"{user.login}/{repo_name}")
                # If we reached here, the repo still exists
                return f"⚠️ Warning: Deletion command sent, but repository '{repo_name}' still appears to exist on GitHub."
            except:
                # If it raises an exception (e.g. 404 Not Found), deletion is verified
                success_msg = f"Successfully deleted repository '{repo_name}' from GitHub."
                self._log("jarvis", success_msg)
                return success_msg
        except Exception as e:
            error_msg = f"❌ GitHub Repository Deletion Failed: {e}"
            self._log("system", error_msg)
            return error_msg

# =========================================================================
# 📝 DOCUMENT AGENT (Updated for Gemini 2.5 & 504 Errors)
# =========================================================================
class DocumentAgent:
    def __init__(self):
        # UPDATED PATH: Targets your existing 'jarvis documents' folder
        self.doc_dir = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', 'jarvis documents')
        if not os.path.exists(self.doc_dir): 
            os.makedirs(self.doc_dir)

    def generate_content(self, topic, context_memory=""):
        """Uses Gemini to write a comprehensive report on the topic."""
        print(f"📝 Drafting content for: {topic}...")
        prompt = f"""
        Act as a Professional Technical Writer.
        Topic: {topic}
        Context from Conversation: {context_memory}
        
        Task: Write a detailed, well-structured document about this topic.
        Structure:
        1. Title
        2. Executive Summary
        3. Key Details / Analysis
        4. Conclusion
        
        Tone: Professional, Informative, and Clear.
        Do NOT use markdown symbols like ** or ## in the output, just clean text.
        """
        
        # --- ROBUST RETRY LOGIC FOR 504 ERRORS ---
        for attempt in range(1, 4): # Try 3 times
            try:
                # Attempt 1 & 2: Use Primary Model (Smart)
                if attempt < 3:
                    response = model.generate_content(prompt)
                else:
                    # Attempt 3: Use Fallback Model (Fast) to avoid timeout
                    print("⚠️ Switching to Fast Model (2.0-Flash-Lite) to prevent timeout...")
                    response = fallback_model.generate_content(prompt)
                
                # Check for valid text
                if response.text and len(response.text) > 10:
                    return response.text
            except Exception as e:
                print(f"⚠️ Generation Attempt {attempt} failed: {e}")
                time.sleep(2) # Wait a bit before retrying
        
        return "Error: System timed out. The topic might be too complex for the current server load."

    def create_file(self, topic, content, file_type="pdf"):
        """Saves the content to the specified format."""
        clean_topic = topic.replace(" ", "_").replace("/", "-")
        filename = f"{clean_topic}.{file_type}"
        filepath = os.path.join(self.doc_dir, filename)
        
        try:
            # 1. PDF GENERATION (Dark Mode Style)
            if file_type == "pdf":
                pdf = DarkPDF()
                pdf.add_page()
                pdf.chapter_title(topic.upper())
                pdf.chapter_body(content)
                pdf.output(filepath)

            # 2. WORD DOCUMENT (.docx)
            elif file_type == "docx":
                doc = WordDoc()
                title = doc.add_heading(topic.upper(), 0)
                run = title.runs[0]
                run.font.color.rgb = RGBColor(0, 50, 150) # Dark Blue Title
                doc.add_paragraph(content)
                doc.save(filepath)

            # 3. TEXT FILE (.txt)
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"TOPIC: {topic.upper()}\n{'='*40}\n\n{content}")

            print(f"✅ Document Saved: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ File Creation Error: {e}")
            return None
# =========================================================================
# 🧠 NEW CLASS: GENERALIST AGENT (Open Interpreter - RESTRICTED MODE)
# =========================================================================
class GeneralistAgent:
    def __init__(self):
        try:
            from interpreter import interpreter
            self.interpreter = interpreter
            
            # 1. LINK TO YOUR API KEY & MODEL
            self.interpreter.llm.api_key = API_KEYS_POOL
            self.interpreter.llm.model = "gemini-2.0-flash" # Use the smartest model for logic
            
            # 2. SECURITY PROTOCOL (THE LIMITER)
            self.interpreter.auto_run = False  # CRITICAL: Forces user approval for every step
            self.interpreter.offline = False   # Allows internet research
            
            # 3. SAFETY INSTRUCTIONS (Hypnotic Constraints)
            self.interpreter.system_message += """
            \n[SAFETY PROTOCOL ACTIVE]
            You are a RESTRICTED AI Assistant. 
            RULES:
            1. You are FORBIDDEN from deleting system files or modifying OS registry.
            2. You are FORBIDDEN from running 'rm -rf', 'format', or admin commands.
            3. If asked to manipulate files, ONLY work inside 'Desktop/jarvis documents'.
            4. You must ASK the user for confirmation before installing any new libraries.
            """
        except ImportError:
            print("❌ Open Interpreter not installed. Run 'pip install open-interpreter'")
            self.interpreter = None

    def solve(self, task):
        if not self.interpreter: return "Error: Interpreter module missing."
        
        print(f"🧠 GENERALIST: Analyzing task '{task}'...")
        # We wrap this in a try-catch because Interpreter can throw errors
        try:
            # We use .chat() to start the process. 
            # Since auto_run=False, it will pause and ask for input in the terminal.
            self.interpreter.chat(task)
            return "Task completed via Interpreter."
        except Exception as e:
            return f"Interpreter Error: {e}"

# =========================================================================
# 🌐 NEW CLASS: BROWSER AGENT (Playwright-Based Autonomous Web Agent)
# =========================================================================
class BrowserAgent:
    def __init__(self):
        print("🌐 Initializing Autonomous Browser Agent...")
        
    def execute_goal(self, goal, log_callback=None):
        """Runs the Playwright browser autonomously to achieve the user's goal"""
        def log(msg):
            print(f"🌐 [BrowserAgent]: {msg}")
            if log_callback:
                log_callback(msg)
                
        log(f"Starting browser automation for goal: '{goal}'")
        
        from playwright.sync_api import sync_playwright
        import json
        
        result = "Goal not accomplished."
        
        try:
            with sync_playwright() as p:
                log("Launching Chromium browser...")
                browser = p.chromium.launch(headless=False, args=["--start-maximized"])
                context = browser.new_context(viewport=None)
                page = context.new_page()
                
                log("Navigating to start page...")
                page.goto("https://www.google.com")
                page.wait_for_load_state("networkidle")
                
                step = 0
                max_steps = 10
                
                while step < max_steps:
                    step += 1
                    current_url = page.url
                    try:
                        visible_text = page.evaluate("() => document.body.innerText")
                    except:
                        visible_text = "Page content empty or loading."
                        
                    log(f"Step {step}/{max_steps} | URL: {current_url}")
                    
                    prompt = f"""
                    You are an autonomous web-browsing agent controlling a Playwright browser.
                    Your ultimate goal is: "{goal}"
                    
                    CURRENT PAGE INFO:
                    URL: {current_url}
                    VISIBLE TEXT ON PAGE (TRUNCATED):
                    {visible_text[:4000]}
                    
                    Choose the next single action to move closer to the goal.
                    Choose from one of these actions:
                    1. GOTO: Navigate to a URL. target = complete URL.
                    2. CLICK: Click a link, button, or input field. target = selector (like text "Search", "a.post-title", "input[name='q']").
                    3. TYPE: Type text into a focused input field. target = selector, text = content to type.
                    4. WAIT: Wait for a short duration. text = number of seconds to wait.
                    5. ANSWER: You have gathered enough information to answer the user's goal. text = your final answer to the user.
                    
                    Format your response in VALID JSON matching this structure:
                    {{
                        "action": "GOTO" | "CLICK" | "TYPE" | "WAIT" | "ANSWER",
                        "target": "selector_or_url_here",
                        "text": "text_content_to_type_or_wait_time_or_final_answer",
                        "thought": "brief explanation of your reasoning"
                    }}
                    
                    Return JSON ONLY. No markdown wrapping. No formatting.
                    """
                    
                    try:
                        raw_res = model.generate_content(prompt).text
                        import re
                        json_match = re.search(r'(\{[\s\S]*\})', raw_res)
                        if json_match:
                            action_data = json.loads(json_match.group(1))
                        else:
                            action_data = json.loads(raw_res.strip())
                    except Exception as le:
                        log(f"Error parsing agent decision: {le}. Retrying simple prompt...")
                        prompt_backup = prompt + "\nRespond with standard raw JSON without code blocks."
                        try:
                            raw_res = model.generate_content(prompt_backup).text
                            clean_res = raw_res.replace("```json", "").replace("```", "").strip()
                            action_data = json.loads(clean_res)
                        except Exception as le2:
                            log(f"Fallback parse failed: {le2}")
                            break
                        
                    action = action_data.get("action", "").upper()
                    target = action_data.get("target", "")
                    action_text = action_data.get("text", "")
                    thought = action_data.get("thought", "")
                    
                    log(f"Thought: {thought}")
                    log(f"Action: {action} | Target: {target} | Text: {action_text}")
                    
                    if action == "GOTO":
                        page.goto(target)
                        page.wait_for_load_state("load")
                    elif action == "CLICK":
                        try:
                            page.click(target, timeout=5000)
                        except:
                            try:
                                page.click(f"text={target}", timeout=5000)
                            except Exception as ce:
                                log(f"Failed to click: {ce}")
                    elif action == "TYPE":
                        try:
                            page.click(target, timeout=5000)
                            page.fill(target, action_text)
                        except:
                            try:
                                page.click(f"text={target}", timeout=5000)
                                page.fill(f"text={target}", action_text)
                            except:
                                try:
                                    page.keyboard.type(action_text)
                                except Exception as te:
                                    log(f"Failed to type: {te}")
                    elif action == "WAIT":
                        try:
                            wait_sec = float(action_text)
                            time.sleep(wait_sec)
                        except:
                            time.sleep(2)
                    elif action == "ANSWER":
                        result = action_text
                        log("Goal achieved!")
                        break
                    else:
                        log(f"Unknown action: {action}")
                        
                    time.sleep(1.0)
                    
                browser.close()
        except Exception as e:
            log(f"Browser crash error: {e}")
            result = f"Failed to complete goal: {e}"
            
        return result