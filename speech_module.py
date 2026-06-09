import speech_recognition as sr
import numpy as np
import time

class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=16000, chunk_size=512)
        
        # --- 🧠 NEURAL EAR CONFIG (No Compiler Needed) ---
        import importlib.util
        self.has_neural_ear = False
        if importlib.util.find_spec("torch") is not None:
            try:
                import torch
                self.has_neural_ear = True
            except Exception as e:
                print(f"⚠️ [SPEECH INIT] PyTorch DLL check failed: {e}. Bypassing Neural Ear.")
        self.model = None
        self.get_speech_timestamps = None

        # --- DEEP FIX SETTINGS ---
        self.recognizer.energy_threshold = 300  # Default floor
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 4.0 # Give user plenty of time to pause and think
        self.recognizer.non_speaking_duration = 2.5

    def calibrate(self):
        """Creates a fresh noise profile for the room."""
        with self.microphone as source:
            print("🎧 [DEEP FIX] Analyzing room acoustics...")
            # We listen for 1 second to set the base noise floor
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print(f"✅ Noise floor calibrated to: {self.recognizer.energy_threshold}")

    def listen(self):
        """Listens for a command with active noise suppression and neural filtering."""
        try:
            from jarvis import voice_queue
            voice_queue.join()
        except Exception:
            pass

        with self.microphone as source:
            try:
                # We do a mini-calibration before every listen to adapt to changing fans/AC
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
                print("👂 Listening...")
                # phrase_time_limit ensures he doesn't listen forever if there's static
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                if self.has_neural_ear:
                    # Lazy load the neural ear model on the first active voice command
                    if self.model is None:
                        try:
                            print("🧠 JARVIS: Lazy Loading Neural Ear Model...")
                            import torch
                            self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                                              model='silero_vad',
                                                              force_reload=False)
                            (self.get_speech_timestamps, _, self.read_audio, _, _) = utils
                            print("✅ Neural Ear Model loaded successfully.")
                        except Exception as e:
                            print(f"⚠️ [SPEECH WARNING] PyTorch failed to initialize: {e}")
                            print("👉 Gracefully falling back to standard Speech Recognition loop...")
                            self.has_neural_ear = False

                if self.has_neural_ear:
                    # --- 🧠 NEURAL VERIFICATION ---
                    import torch
                    # Convert raw audio to 16k mono for the AI model to analyze
                    raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                    audio_int16 = np.frombuffer(raw_data, dtype=np.int16)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0
                    
                    # Ask the neural network: "Is this a human speaking?"
                    audio_tensor = torch.from_numpy(audio_float32)
                    timestamps = self.get_speech_timestamps(audio_tensor, self.model, sampling_rate=16000)
                    
                    # If the timestamps list is empty, the AI determined it was just background noise
                    if not timestamps: 
                        print(f"🚫 Noise Ignored (Not a human)")
                        return ""

                    print(f"🧠 Processing audio (Human Speech Verified)...")
                else:
                    print(f"👂 Processing audio...")
                # We use the Google engine but with cleaned, verified audio with 4-second timeout
                import socket
                orig_timeout = socket.getdefaulttimeout()
                try:
                    socket.setdefaulttimeout(4.0)
                    query = self.recognizer.recognize_google(audio, language='en-in')
                finally:
                    socket.setdefaulttimeout(orig_timeout)
                return query.lower()

            except sr.WaitTimeoutError:
                return None  # No one spoke
            except sr.UnknownValueError:
                # JARVIS heard a human, but couldn't understand the words
                return "" 
            except Exception as e:
                print(f"❌ Speech Error: {e}")
                return None