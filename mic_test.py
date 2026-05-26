import speech_recognition as sr
import time

r = sr.Recognizer()
m = sr.Microphone()

print("🎧 LISTENING TO ENERGY LEVELS...")
print("---------------------------------")
print("1. Stay QUIET (Watch the numbers - this is your background noise)")
print("2. SPEAK normally (Watch the numbers jump up)")
print("---------------------------------")

with m as source:
    r.adjust_for_ambient_noise(source)
    while True:
        # This prints how loud the sound is right now
        print(f"Energy Level: {m.stream.read(1024).hex()[:4]}") # Crude visualizer
        # Better way to check threshold:
        try:
             # We just read raw energy to give you an idea
             print(f"Current Threshold needed: {r.energy_threshold}")
             time.sleep(1)
        except KeyboardInterrupt:
            break