import time
import psutil # Checks battery/CPU
import schedule # Handles timing
import threading
import config # For speaking (Independent of main loop)
from google import genai
# --- NEW IMPORTS REQUIRED FOR VISION ---
from vision_module import VisionSystem
from automation_module import ApplicationController
from ai_module import AIBrain

class ProactiveAgent:
    def __init__(self):
        self.running = True
        self.last_battery = 100

        # --- INITIALIZE VISION & AI MODULES ---
        self.vision = VisionSystem()
        self.automation = ApplicationController()
        self.brain = AIBrain()
        self.current_key_index = 0
        self.error_start_time = None
        self.last_analyzed_error = None
        
        schedule.every().day.at("09:00").do(self.morning_briefing)
        schedule.every(30).minutes.do(self.drink_water_reminder)

    def speak(self, text):
        """Separate speaking channel for background alerts"""
        print(f"⚡ [PROACTIVE]: {text}")
        try:
            # We use the isolated voice_queue from jarvis.py
            from jarvis import voice_queue
            voice_queue.put(text)
        except ImportError:
            print("⚠️ Proactive Module could not reach voice_queue.")
    
    def _call_vision_api(self, img, prompt):
        """Calls Gemini directly using config.py and auto-rotates your 5 keys on 429 errors."""
        max_attempts = len(config.API_KEYS_POOL)
        attempts = 0
        
        while attempts < max_attempts:
            try:
                # 1. Pull the key and model directly from your config
                current_key = config.API_KEYS_POOL[self.current_key_index]
                current_model = config.AI_MODELS[0] # Uses the first model (e.g., gemini-2.5-flash-lite)
                
                # 2. Connect client
                client = genai.Client(api_key=current_key)
                
                # 3. Generate response
                response = client.models.generate_content(
                    model=current_model,
                    contents=[img, prompt]
                )
                return response.text.strip()
                
            except Exception as e:
                error_str = str(e).upper()
                # 4. If we hit the rate limit, ROTATE THE KEY instantly
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print(f"⚠️ [VISION LIMIT]: Key #{self.current_key_index + 1} exhausted. Rotating to next key...")
                    self.current_key_index = (self.current_key_index + 1) % len(config.API_KEYS_POOL)
                    attempts += 1
                else:
                    print(f"❌ [VISION CRASH]: {e}")
                    return None
                    
        print("❌ [CRITICAL]: All API keys in config.py have hit their rate limits.")
        return None

    def morning_briefing(self):
        self.speak("Good morning, Sir. Systems are online. Recommend checking your email.")

    def drink_water_reminder(self):
        self.speak("Sir, you have been coding for 30 minutes. Hydration check.")

    def check_system_health(self):
        """Monitors Battery and CPU"""
        battery = psutil.sensors_battery()
        
        # 1. Low Battery Warning
        if battery and battery.percent < 20 and not battery.power_plugged:
            if self.last_battery >= 20: # Only say it once
                self.speak(f"Critical Power. Battery is at {battery.percent} percent. Please plug in.")
        
        self.last_battery = battery.percent if battery else 100

        # 2. High CPU Usage (Heavy Load)
        cpu_usage = psutil.cpu_percent(interval=1)
        if cpu_usage > 85:
            self.speak("Warning. CPU usage is critically high. Cooling protocols recommended.")

    # --- THE NEW PROACTIVE VISION ENGINE (DEBUG MODE) ---
    def _analyze_screen_context(self):
        try:
            active_window = self.automation.get_active_window_title()
            
            # 1. Check if user is coding
            target_apps = ["visual studio code", "code", "cmd", "powershell", "terminal", "pycharm"]
            if not any(app in active_window for app in target_apps):
                self.error_start_time = None 
                return None
                
            print(f"👁️ [VISION DEBUG]: Detected coding window '{active_window}'. Taking silent screenshot...")
            
            # 2. Capture Screen Silently
            img = self.vision.capture_screen_to_memory()
            if not img: 
                print("👁️ [VISION DEBUG]: Failed to capture image to memory.")
                return None

            # 3. Analyze for Errors
            prompt = "Look at this screenshot. Is there a prominent coding error, traceback, or red squiggly syntax error visible? Answer with ONLY 'YES' or 'NO'."
            
            print("👁️ [VISION DEBUG]: Sending screenshot to Gemini for analysis...")
            response = self._call_vision_api(img, prompt)
            print(f"👁️ [VISION DEBUG]: AI says error visible? -> {response}")

            # 4. State Management Logic
            if "YES" in response:
                if self.error_start_time is None:
                    # User just encountered the error. Start the timer.
                    self.error_start_time = time.time()
                    print("👁️ [VISION DEBUG]: Stopwatch started. Waiting to see if user fixes it...")
                else:
                    elapsed = time.time() - self.error_start_time
                    print(f"👁️ [VISION DEBUG]: Error has been on screen for {int(elapsed)} seconds.")
                    
                    # ⬇️ CHANGED TO 10 SECONDS FOR TESTING ⬇️
                    if elapsed > 10: 
                        print("👁️ [VISION DEBUG]: Time limit reached. Generating vocal alert...")
                        detail_prompt = "What is the specific error message shown in this screenshot?"
                        error_detail = self._call_vision_api(img, detail_prompt)
                        
                        if error_detail and error_detail != self.last_analyzed_error:
                            self.last_analyzed_error = error_detail
                            self.error_start_time = None # Reset timer
                            return "Sir, I notice you are stuck on a syntax error. Would you like me to analyze the screen and suggest a fix?"
            else:
                self.error_start_time = None

        except Exception as e:
            # ✨ NOW WE CAN SEE HIDDEN ERRORS
            print(f"❌ [VISION CRASH]: {e}") 
        
        return None

    def start_monitoring(self):
        """The Infinite Loop watching you"""
        self.speak("Proactive Systems Engaged.")
        while self.running:
            # 1. Run Schedules (Time-based routines)
            schedule.run_pending()
            
            # 2. Check Hardware
            self.check_system_health()
            
            # 3. Check Screen for Errors (VISION ENGINE INTERGATION)
            vision_alert = self._analyze_screen_context()
            if vision_alert:
                try:
                    # Attempt to log to GUI dashboard if it exists
                    from jarvis import log_to_dashboard
                    log_to_dashboard("jarvis", vision_alert)
                except ImportError:
                    pass
                self.speak(vision_alert)

            # Sleep 10 seconds to save CPU & API limits
            time.sleep(60) 

    def stop(self):
        self.running = False