import time
import os
import tempfile
import re
import threading
import socket
import speech_recognition as sr

TELUGU_SCRIPT_RE = re.compile(r'[\u0C00-\u0C7F]')

class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=16000, chunk_size=512)
        
        # --- 🧠 NEURAL EAR CONFIG (No Compiler Needed) ---
        import config
        self.has_neural_ear = False
        if getattr(config, "USE_NEURAL_EAR", False):
            try:
                import torch
                self.has_neural_ear = True
            except Exception as e:
                print(f"⚠️ [SPEECH INIT] PyTorch DLL check failed: {e}. Bypassing Neural Ear.")
        self.model = None
        self.get_speech_timestamps = None

        # --- 🎙️ SPEAKER VERIFICATION (BIOMETRICS) ---
        self.speaker_verification_enabled = getattr(config, "SPEAKER_VERIFICATION_ENABLED", False)
        self.speaker_model = None
        self.speaker_ref_path = getattr(config, "SPEAKER_REF_PATH", "owner_voice_ref.wav")
        self.speaker_threshold = getattr(config, "SPEAKER_THRESHOLD", 0.25)
        
        if self.speaker_verification_enabled:
            threading.Thread(
                target=self._load_speaker_verification_model,
                daemon=True,
                name="SpeakerVerificationLoader"
            ).start()

        # --- DEEP FIX SETTINGS ---
        self.recognizer.energy_threshold = 300  # Default floor
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 1.2 # snappier response
        self.recognizer.non_speaking_duration = 0.8

    def _load_speaker_verification_model(self):
        try:
            print("🎙️ JARVIS: Initializing Speaker Verification Core (SpeechBrain)...")
            from speechbrain.inference.speaker import SpeakerRecognition
            savedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".speechbrain_model")
            self.speaker_model = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir=savedir,
                run_opts={"device": "cpu"}
            )
            print("🎙️ JARVIS: Speaker Verification Core loaded successfully.")
        except Exception as e:
            print(f"⚠️ [SPEECH WARNING] Failed to load Speaker Verification: {e}")
            print("👉 Please ensure dependencies are installed via: pip install torch torchaudio speechbrain")
            print("👉 Temporarily disabling speaker verification fallback.")
            self.speaker_verification_enabled = False

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

                # --- 🎙️ SPEAKER VERIFICATION CHECK ---
                if self.speaker_verification_enabled and self.speaker_model:
                    if not os.path.exists(self.speaker_ref_path):
                        print(f"⚠️ [SPEECH WARNING] Reference voice file '{self.speaker_ref_path}' not found.")
                        print("👉 Please record a 5-second sample of your voice and save it as 'owner_voice_ref.wav'.")
                        print("👉 Bypassing verification for this command.")
                    else:
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                            f.write(audio.get_wav_data())
                            temp_wav_path = f.name
                        
                        try:
                            score, prediction = self.speaker_model.verify_files(self.speaker_ref_path, temp_wav_path)
                            score_val = score.item() if hasattr(score, "item") else float(score)
                            pred_val = prediction.item() if hasattr(prediction, "item") else bool(prediction)
                            
                            print(f"🎙️ [BIOMETRICS] Speaker voice match score: {score_val:.4f} (Threshold: {self.speaker_threshold})")
                            if not pred_val and score_val < self.speaker_threshold:
                                print("🚫 [BIOMETRICS] Unauthorized speaker detected. Command ignored.")
                                return ""  # Ignore command
                        except Exception as ve:
                            print(f"⚠️ [BIOMETRICS] Verification failed: {ve}")
                        finally:
                            try:
                                os.unlink(temp_wav_path)
                            except:
                                pass
                
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
                    import numpy as np
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
                # Run parallel English and Telugu speech recognition
                
                en_result = []
                te_result = []
                
                def recognize_en():
                    orig_timeout = socket.getdefaulttimeout()
                    try:
                        socket.setdefaulttimeout(4.0)
                        query = self.recognizer.recognize_google(audio, language='en-in')
                        if query:
                            en_result.append(query.strip())
                    except:
                        pass
                    finally:
                        socket.setdefaulttimeout(orig_timeout)

                def recognize_te():
                    orig_timeout = socket.getdefaulttimeout()
                    try:
                        socket.setdefaulttimeout(4.0)
                        query = self.recognizer.recognize_google(audio, language='te-in')
                        if query:
                            te_result.append(query.strip())
                    except:
                        pass
                    finally:
                        socket.setdefaulttimeout(orig_timeout)

                t_en = threading.Thread(target=recognize_en)
                t_te = threading.Thread(target=recognize_te)
                
                t_en.start()
                t_te.start()
                
                t_en.join(timeout=4.0)
                t_te.join(timeout=4.0)
                
                en_text = en_result[0] if en_result else ""
                te_text = te_result[0] if te_result else ""
                
                print(f"👂 [Speech recognition] en: '{en_text}' | te: '{te_text}'")
                
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
                    return en_text.lower()
                
                # Check if Telugu transcription contains Telugu characters
                if te_text and TELUGU_SCRIPT_RE.search(te_text):
                    return te_text
                
                if en_text:
                    return en_text.lower()
                elif te_text:
                    return te_text.lower()
                
                raise sr.UnknownValueError()

            except sr.WaitTimeoutError:
                return None  # No one spoke
            except sr.UnknownValueError:
                # JARVIS heard a human, but couldn't understand the words
                return "" 
            except Exception as e:
                print(f"❌ Speech Error: {e}")
                return None