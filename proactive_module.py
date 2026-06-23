import time
import psutil # Checks battery/CPU
import schedule # Handles timing
import threading
import config # For speaking (Independent of main loop)

# --- NEW IMPORTS REQUIRED FOR VISION ---
from vision_module import VisionSystem
from automation_module import ApplicationController
from ai_module import AIBrain

class ProactiveAgent:
    def __init__(self, voice_queue=None, log_to_dashboard_cb=None):
        self.running = True
        self.last_battery = 100
        self.voice_queue = voice_queue
        self.log_to_dashboard_cb = log_to_dashboard_cb

        # --- INITIALIZE VISION & AI MODULES ---
        self.vision = VisionSystem()
        self.automation = ApplicationController()
        self.brain = AIBrain()
        self.current_key_index = 0
        self.error_start_time = None
        self.last_analyzed_error = None
        # Cooldown warning for the first 10 minutes of startup to let the system stabilize
        self.last_cpu_warning_time = time.time()
        
        # Initialize psutil CPU reference point to prevent blocking calls later
        psutil.cpu_percent(interval=None)
        
        self.scheduler = schedule.Scheduler()
        self.scheduler.every().day.at("09:00").do(self.morning_briefing)
        self.scheduler.every(30).minutes.do(self.drink_water_reminder)

    def speak(self, text):
        """Separate speaking channel for background alerts"""
        print(f"⚡ [PROACTIVE]: {text}")
        if self.voice_queue is not None:
            self.voice_queue.put(text)
        else:
            try:
                # We use the isolated voice_queue from jarvis.py
                from jarvis import voice_queue
                voice_queue.put(text)
            except ImportError:
                print("⚠️ Proactive Module could not reach voice_queue.")
    
    def _call_vision_api(self, img, prompt):
        """Calls Gemini directly using config.py and auto-rotates keys/models on errors."""
        from google import genai
        import random
        
        now = time.time()
        keys_to_try = list(config.API_KEYS_POOL)
        if not keys_to_try:
            print("❌ [VISION CRITICAL]: No active keys in the pool.")
            return None
            
        models_to_try = list(config.AI_MODELS)
        success = False
        response_text = None
        
        for model in models_to_try:
            if success:
                break
                
            start_idx = self.current_key_index
            for i in range(len(keys_to_try)):
                key_idx = (start_idx + i) % len(keys_to_try)
                key = keys_to_try[key_idx]
                
                # Check cooldown
                if now < config.KEY_COOLDOWNS.get(key, 0.0):
                    if len(keys_to_try) > 1:
                        continue
                
                self.current_key_index = key_idx
                
                # Setup Client
                try:
                    client = genai.Client(api_key=key)
                except Exception as conn_err:
                    print(f"❌ [VISION] Connection Error for Key #{key_idx + 1}: {conn_err}")
                    continue
                
                # Try calling the API with transient retries
                max_transient_attempts = 3
                base_delay = 0.5
                
                for transient_attempt in range(max_transient_attempts):
                    try:
                        response = client.models.generate_content(
                            model=model,
                            contents=[img, prompt]
                        )
                        response_text = response.text.strip()
                        success = True
                        break
                    except Exception as e:
                        err_str = str(e).lower()
                        is_transient = any(x in err_str for x in ["503", "unavailable", "overloaded", "504", "timeout", "deadline exceeded"])
                        is_rate_limit = any(x in err_str for x in ["429", "resource_exhausted", "quota exceeded"])
                        
                        # Handle transient error with backoff
                        if is_transient and transient_attempt < max_transient_attempts - 1:
                            sleep_time = (2 ** transient_attempt) * base_delay + random.uniform(0.05, 0.15)
                            print(f"⚠️ [VISION] Transient error (503/504). Retrying key #{key_idx + 1} in {sleep_time:.2f}s...")
                            time.sleep(sleep_time)
                            continue
                            
                        # Handle rate limit (429) -> Cool down key and skip to next key
                        if is_rate_limit:
                            print(f"⚠️ [VISION] Quota Exceeded (429) on Key #{key_idx + 1}. Putting key on 45s cooldown.")
                            config.KEY_COOLDOWNS[key] = time.time() + 45.0
                            break # Break transient loop to rotate key
                            
                        # Other non-transient errors -> Rotate key
                        print(f"⚠️ [VISION] Error on Key #{key_idx + 1} with Model {model}: {e}. Rotating key...")
                        break # Break transient loop to rotate key
                
                if success:
                    break
                    
        if success:
            return response_text
            
        print("❌ [VISION CRITICAL]: All keys and models exhausted for Vision API.")
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
        cpu_usage = psutil.cpu_percent(interval=None)
        if cpu_usage > 85:
            # Check cooldown (10 minutes = 600 seconds)
            if time.time() - getattr(self, "last_cpu_warning_time", 0) > 600:
                self.speak("Warning. CPU usage is critically high. Cooling protocols recommended.")
                self.last_cpu_warning_time = time.time()

    # --- THE NEW PROACTIVE VISION ENGINE (DEBUG MODE) ---
    def _analyze_screen_context(self):
        try:
            active_window = self.automation.get_active_window_title()
            
            # 1. Check if user is coding
            target_apps = ["visual studio code", "cmd", "powershell", "terminal", "pycharm"]
            is_coding_window = any(app in active_window for app in target_apps)
            if not is_coding_window:
                import re
                is_coding_window = bool(re.search(r'\bcode\b', active_window))
                
            if not is_coding_window:
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
            self.scheduler.run_pending()
            
            # 2. Check Hardware
            self.check_system_health()
            
            # 3. Check Screen for Errors (VISION ENGINE INTERGATION)
            vision_alert = self._analyze_screen_context()
            if vision_alert:
                if self.log_to_dashboard_cb is not None:
                    try:
                        self.log_to_dashboard_cb("jarvis", vision_alert)
                    except Exception as le:
                        print(f"⚠️ Failed to log to dashboard callback: {le}")
                else:
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