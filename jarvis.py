import speech_recognition as sr
import os
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

# Create the queue
voice_queue = queue.Queue()

# The dedicated voice-only worker
def voice_worker():
    pythoncom.CoInitialize() # Crucial for Windows Audio
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    
    # Adjust speed: 0 is normal, positive (1-10) is faster, negative is slower
    speaker.Rate = 2 
    
    while True:
        text = voice_queue.get()
        if text is None: break
        
        try:
            # This is naturally blocking, so no runAndWait() is needed!
            speaker.Speak(text) 
        except Exception as e:
            print(f"❌ Direct Audio Error: {e}")
            
        voice_queue.task_done()

# Start the voice worker thread in the background
voice_thread = threading.Thread(target=voice_worker, name="VoiceWorker", daemon=True)
voice_thread.start()


# --- DASHBOARD LOGGER ---
def log_to_dashboard(type, message):
    log_file = "jarvis_logs.json"
    entry = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "type": type, 
        "message": message
    }
    
    data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                data = json.load(f)
        except: pass
        
    data.append(entry)
    
    if len(data) > 50: data = data[-50:]
        
    with open(log_file, "w") as f:
        json.dump(data, f, indent=4)

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

def exit_handler():
    print("🛑 System Shutdown Detected.")
    log_to_dashboard("system", "JARVIS shutting down due to system power off.")

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
        self.models = ["gemini-2.5-pro", "gemini-2.5", "gemini-2-pro", "gemini-2", "gemini-1.5-pro", "gemini-1.5"]
        self.rec_agent = None
        self.project_agent = None
        
        # Initialize Memory Globally
        from agent_module import MemoryAgent
        self.memory_brain = MemoryAgent()
    def _respond(self, text):
        if text:
            print(f"🤖 JARVIS: {text}")
            voice_queue.put(text)
            
            try:
                # 1. Log to the GUI dashboard
                from jarvis_gui import log_to_dashboard
                log_to_dashboard("jarvis", text)
            except ImportError:
                pass
    def _play_chime(self):  
        try:
            winsound.Beep(1200, 150)       
        except: pass
    
    def _listen_for_command(self):
        return self.ears.listen()

    def _force_listen(self, retries=1):
        for _ in range(retries + 1):
            text = self.ears.listen()
            if text: return text
            if _ < retries: self._respond("I didn't catch that. Please repeat.")
        return None
    
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


        
    def process_command(self, text):
        text = text.lower()
        print(f"👤 USER: {text}")
        
        # 1. Handle Exit
        if "exit" in text or "quit" in text:
            self._respond("Powering down.")
            os._exit(0)
            
        # 2. Handle Web Search (The Clean Way)
        elif "search" in text or "google" in text or "tell me about" in text:
            # We don't replace "google", we just strip the trigger words
            # and keep the rest of the search query intact
            query = text.replace("search for", "").replace("google", "").replace("tell me about", "").strip()
            self._respond(f"Searching for {query}")
            
            # Now pass the 'query' variable to your DDGS search
            # (ensure your ddgs usage is: with DDGS() as ddgs: ... )
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
        # 💻 LEVEL 2: WEB DESIGNER (NEW!)
        # ==========================================
        if "design a page" in text:
            try:
                # 1. Extract Topic
                topic = text.replace("create website", "").replace("design a page", "").replace("about", "").strip()
                if not topic: topic = "JARVIS Interface"
                
                self._respond(f"Initializing web design protocol for {topic}...")
                
                # 2. Generate Futuristic HTML (Iron Man Style)
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{topic.upper()} - JARVIS ARCHIVE</title>
                    <style>
                        body {{ background-color: #050505; color: #00f3ff; font-family: 'Courier New', Courier, monospace; text-align: center; margin-top: 50px; }}
                        h1 {{ font-size: 3em; text-shadow: 0 0 20px #00f3ff; }}
                        p {{ font-size: 1.2em; color: #aeeeff; max-width: 600px; margin: 20px auto; }}
                        .reactor {{
                            width: 150px; height: 150px; border-radius: 50%;
                            border: 5px solid #00f3ff; box-shadow: 0 0 50px #00f3ff;
                            margin: 50px auto; animation: spin 4s linear infinite;
                        }}
                        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                        .container {{ border: 1px solid #333; padding: 20px; display: inline-block; background: #0a0a0a; box-shadow: 0 0 20px rgba(0, 243, 255, 0.2); }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="reactor"></div>
                        <h1>{topic.upper()}</h1>
                        <p>GENERATED BY JARVIS SYSTEM.<br>SECURE DATA VISUALIZATION.</p>
                        <p>This is a generated web interface dedicated to {topic}. All systems nominal.</p>
                    </div>
                </body>
                </html>
                """
                
                # 3. Save and Open
                file_path = os.path.join(get_desktop_path(), f"{topic.replace(' ', '_')}_design.html")
                with open(file_path, "w") as f:
                    f.write(html_content)
                
                self._respond("Website generated successfully. Opening now.")
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
        
        if any(vt in text for vt in visual_triggers) and any(iw in text for iw in image_words):
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
        # 📂 LEVEL 2: FILES & FOLDERS
        # ==========================================
        if "create folder" in text:
            name = text.replace("create folder", "").strip()
            path = os.path.join(get_desktop_path(), name)
            if not os.path.exists(path):
                os.makedirs(path)
                self._respond(f"Created {name}.")
                os.startfile(path)
            return False

        if "create file" in text:
            if " inside " in text:
                parts = text.replace("create file", "").split(" inside ")
                file_name = parts[0].strip()
                folder_name = parts[1].strip()
                folder_path = find_folder_globally(folder_name)
                if folder_path:
                    full_path = os.path.join(folder_path, f"{file_name}.txt")
                    with open(full_path, "w") as f: f.write("")
                    self._respond(f"Created {file_name} inside {folder_name}.")
                    os.startfile(full_path)
                else: self._respond(f"Folder {folder_name} not found.")
            else:
                name = text.replace("create file", "").strip()
                path = os.path.join(get_desktop_path(), f"{name}.txt")
                with open(path, "w") as f: f.write("")
                self._respond(f"Created {name}.")
                os.startfile(path)
            return False

        if "open folder" in text:
            name = text.replace("open folder", "").strip()
            path = find_folder_globally(name)
            if path:
                self._respond("Opening.")
                os.startfile(path)
            else: self._respond("Not found.")
            return False

        if "delete folder" in text:
            name = text.replace("delete folder", "").strip()
            path = os.path.join(get_desktop_path(), name)
            if os.path.exists(path):
                self._respond(f"Delete {name}?")
                confirm = self._force_listen(retries=2) or ""
                if any(w in confirm.lower() for w in ["yes", "delete", "sure"]):
                    try:
                        def on_rm_error(func, path, exc_info):
                         os.chmod(path, 128)
                         os.unlink(path)
                        shutil.rmtree(path, onerror=on_rm_error)
                        self._respond("Deleted.")
                    except: self._respond("Could not delete.")
            return False

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
        
        # ==========================================
        # 🎵 LEVEL 3: MEDIA (Music & Youtube)
        # ==========================================
        if "play" in text and "music" in text:
            self._respond("Playing on YouTube...")
            self.automation.play_music(text)
            return False
        
        if text.startswith("play") and len(text.split()) <= 6:
            self._respond("Playing...")
            self.automation.play_music(text)
            return False

        if any(x in text for x in ["volume", "mute", "pause", "next track", "previous track"]):
            self.automation.media_control(text)
            return False

        # ==========================================
        # ⌨️ LEVEL 4: SYSTEM AUTOMATION
        # ==========================================
        if "open" in text and "folder" not in text and "file" not in text and "memory" not in text:
            word_count = len(text.split())
            if word_count < 5:
                self._respond(self.automation.open_app(text))
                return False

        if "close" in text and "folder" not in text:
            self._respond(self.automation.close_app(text))
            return False

        if text.startswith("write") or text.startswith("type"):
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
        
        # ==========================================
        # 🎙️ LEVEL 6: RECORDER (Audio & Video & Screen)
        # ==========================================
        if "record video" in text:
            from agent_module import RecorderAgent
            if self.rec_agent is None:
                self.rec_agent = RecorderAgent()
            self._respond("Starting Video Recording. Say 'Jarvis Stop Video' to end it.")
            self.rec_agent.start_video_recording("jarvis_video")
            return False

        if "record screen" in text or "start screen recording" in text:
            from agent_module import RecorderAgent
            if self.rec_agent is None:
                self.rec_agent = RecorderAgent()
            self._respond("Starting Screen Recording. Say 'Jarvis Stop Screen Recording' to end it.")
            self.rec_agent.start_screen_recording("jarvis_screen")
            return False

        if "stop video" in text or "stop screen recording" in text or "stop recording" in text:
            if self.rec_agent is not None:
                self.rec_agent.stop_recording() 
                self._respond("Recording stopped.")
                self.rec_agent = None
            else:
                self._respond("No active recording is running.")
            return False

        if "record voice" in text or "record audio" in text:
            from agent_module import RecorderAgent
            rec_agent = RecorderAgent()
            self._respond("Recording started. Please press ENTER in the terminal window to stop.")
            
            # This runs in a thread but blocks the mic logic, so we wait for Key Press
            file = rec_agent.start_audio_recording("jarvis_audio")
            
            # Since we used 'input()' inside the agent (simulated), we ask for name now
            self._respond("Recording saved. What should I name this file?")
            new_name = self._force_listen()
            if new_name:
                old_path = file
                new_path = file.replace("jarvis_audio", new_name.replace(" ", "_"))
                os.rename(old_path, new_path)
                self._respond(f"Renamed to {new_name}.wav")
            return False

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
        
        # ==========================================
        # 🟢 WHATSAPP (NATIVE DESKTOP APP)
        # ==========================================
        if "whatsapp" in text:
            self._respond("Recipient?")
            name = self._force_listen()
            if not name: return False
            
            # 1. Get Number
            contact = self.contacts.get_contact(name)
            phone = None
            if contact and "phone" in contact:
                phone = contact["phone"]
            else:
                self._respond(f"I need the number for {name}. Please enter it.")
                phone = pyautogui.prompt(text=f"Enter Number for {name}:", title="WhatsApp")
            
            if not phone: return False
            
            self._respond("Message?")
            msg = self._force_listen()
            
            if msg:
                self._respond("Opening WhatsApp Desktop...")
                # 2. Use Windows Protocol to open the App directly
                # Ensure number format (remove + if user typed it, we add it safely)
                clean_phone = phone.replace("+", "").replace(" ", "")
                
                # Command to open WhatsApp App
                os.system(f"start whatsapp://send?phone={clean_phone}&text={urllib.parse.quote(msg)}")
                
                # 3. Press Enter to send (Wait for app to load)
                time.sleep(2) # Wait 2 seconds for app to open
                pyautogui.press('enter')
                self._respond("Message sent.")
            return False

        # ==========================================
        # 📧 EMAIL (FIXED + ATTACHMENTS)
        # ==========================================
        if "send" in text and "email" in text:
            # Check Config First
            if not hasattr(config, 'EMAIL_USER') or not config.EMAIL_USER:
                self._respond("Error. Email credentials missing in config file.")
                return False

            self._respond("Recipient?")
            name = self._force_listen()
            if not name: return False
            
            # Get Email Address
            email_addr = None
            contact = self.contacts.get_contact(name)
            if contact and "email" in contact:
                email_addr = contact["email"]
            else:
                self._respond(f"I need the email for {name}. Please enter it.")
                email_addr = pyautogui.prompt(text=f"Enter Email for {name}:", title="Email")
            
            if not email_addr: return False

            self._respond("Subject?")
            subj = self._force_listen() or "No Subject"
            
            self._respond("Message?")
            body = self._force_listen() or "Sent via Jarvis"

            # ✨ NEW: Ask for Attachment
            self._respond("Do you want to attach a file? Say yes or no.")
            attach_resp = self._force_listen()
            
            if attach_resp and "yes" in attach_resp.lower():
                self._respond("Please select the file on screen.")
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw() # Hide empty window
                self.attachment_path = filedialog.askopenfilename(title="Select Attachment")
                root.destroy()
            
            self._respond("Sending...")
            
            try:
                msg = EmailMessage()
                msg['Subject'] = subj
                msg['From'] = config.EMAIL_USER
                msg['To'] = email_addr
                msg.set_content(body)

                if self.attachment_path and os.path.exists(self.attachment_path):
                    with open(self.attachment_path, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(self.attachment_path)
                        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
                    print(f"📎 Attached: {self.attachment_path}")

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(config.EMAIL_USER, config.EMAIL_PASS)
                    smtp.send_message(msg)

                self._respond("Email sent successfully.")
                self.attachment_path = None 
            except Exception as e:
                print(f"❌ Email Error: {e}")
                self._respond("Failed. Please check your internet or password.")
            return False
        
        # ==========================================
        # 🏗️  MULTI-AGENT FACTORY (CREWAI INTEGRATION)
        # ==========================================
        dev_triggers = [
            "build a website", "create a website", "make a website", "design a website",
            "build a project", "create a project", "make a project", "design a project",
            "build website", "create website", "make website", "design website"
        ]
        if any(trigger in text for trigger in dev_triggers):
            # STEP 1: INITIATION
            topic = text
            for trigger in dev_triggers:
                topic = topic.replace(trigger, "")
            topic = topic.replace("about", "").replace("for", "").replace("a ", "").strip()
            if not topic: topic = "Business"
            
            project_name = f"{topic.replace(' ', '_')}_Project"
            project_dir = os.path.join(get_desktop_path(), "PROJECTS", project_name)
            
            self._respond(f"Initiating Multi-Agent CrewAI Factory for {topic}.")
            self._respond("My engineering team is building this, please wait. This may take up to 60 seconds.")
            
            try:
                import subprocess
                import random
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
                
                # Run the subprocess
                print(f"🤖 JARVIS: Spawning CrewAI Subprocess...")
                result = subprocess.run(
                    cmd, 
                    cwd=factory_dir, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8', 
                    errors='ignore'
                )
                
                if result.returncode == 0:
                    self._respond(f"Project built successfully! The files are saved in the PROJECTS folder under {project_name}.")
                    os.startfile(project_dir)
                else:
                    self._respond("The engineering team encountered an error during compilation.")
                    print(f"CrewAI Error:\n{result.stderr}\n{result.stdout}")
                    
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
        
        active_window = self.automation.get_active_window_title() if hasattr(self.automation, 'get_active_window_title') else ""
        context = f"{self.last_topic}. User is looking at: {active_window}" if active_window else self.last_topic

        # 1. Get raw response (Force Anti-Code)
        force_tag = " IMPORTANT: Use the tag [IMAGE: <topic>] for visual explanations. Do NOT write code."
        response = self.brain.get_response(text + force_tag, context=context)

        # 2. Process Response (Holograms & Filters)
        if response:
            try:
                # A) Check for Hologram Tag
                image_tag = re.search(r'\[IMAGE: (.*?)\]', response, re.IGNORECASE)
                
                if image_tag:
                    topic = image_tag.group(1)
                    response = response.replace(image_tag.group(0), "").strip()
                    print(f"🎨 JARVIS: Projecting diagram for {topic}...")
                    search_url = f"https://www.google.com/search?q={urllib.parse.quote(topic)}&tbm=isch"
                    webbrowser.open(search_url)

                # B) Clean Up HTML and Code
                response = re.sub(r'\[.*?\]', '', response).strip()
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
        
        lower_resp = response.lower()
        if "?" in response or "want to know more" in lower_resp or "would you like" in lower_resp:
            return True # STAY AWAKE
            
        return False # SLEEP

    def run(self):
        # --- NEW ADDITION: AUDIO FIX ---
        time.sleep(5) # Waits for Proactive voice to finish before greeting
        # -------------------------------
        self._morning_briefing()
        
        WAKE_WORD = "jarvis"
        print(f"💤 Standby Mode. Say '{WAKE_WORD}' to wake me up...")
        
        wake_recognizer = sr.Recognizer()
        
        while True:
            try:
                try:
                    voice_queue.join()
                except Exception:
                    pass
                with sr.Microphone() as source:
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

if __name__ == "__main__":
    # 1. Start PROACTIVE BACKGROUND BRAIN
    background_brain = ProactiveAgent()
    t = threading.Thread(target=background_brain.start_monitoring)
    t.daemon = True 
    t.start()

    app = JARVIS()
    app.run()