import speech_recognition as sr
import os
import time

def record_owner_voice():
    r = sr.Recognizer()
    m = sr.Microphone(sample_rate=16000)
    
    print("🎙️ JARVIS Voice Registration Utility")
    print("--------------------------------------")
    print("This utility will record a 5-second sample of your voice to act as a biometrics reference.")
    print("Please make sure you are in a quiet room and speak normally.")
    print("--------------------------------------")
    
    input("Press Enter to start recording...")
    
    print("\n🎧 Analyzing background noise...")
    with m as source:
        r.adjust_for_ambient_noise(source, duration=1.0)
        print("✅ Ambient noise analysis complete.")
        print("\n🔴 RECORDING NOW... Please speak clearly (e.g., 'Hello Jarvis, this is my voice reference.')")
        print("--------------------------------------")
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("🟢 Recording stopped.")
            
            # Save the file
            ref_path = "owner_voice_ref.wav"
            with open(ref_path, "wb") as f:
                f.write(audio.get_wav_data())
            
            absolute_path = os.path.abspath(ref_path)
            print("\n🎉 SUCCESS!")
            print(f"Voice reference saved successfully to: {absolute_path}")
            print(f"File size: {os.path.getsize(ref_path)} bytes")
            print("\nNext Steps:")
            print("1. Set `SPEAKER_VERIFICATION_ENABLED = True` in `config.py`")
            print("2. Ensure speechbrain and torch are installed using:")
            print("   pip install torch torchaudio speechbrain")
            
        except sr.WaitTimeoutError:
            print("❌ Error: No voice detected. Please run the script again and speak immediately.")
        except Exception as e:
            print(f"❌ Error during recording: {e}")

if __name__ == "__main__":
    record_owner_voice()
