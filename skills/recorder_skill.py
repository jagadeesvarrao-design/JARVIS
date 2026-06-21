import os
import re

def get_triggers():
    return [
        r"\brecord\b.*\b(?:video|screen|voice|audio)\b",
        r"\bstart\b.*\bscreen\s+recording\b",
        r"\bstop\b.*\b(?:video|recording|screen\s+recording)\b"
    ]

def execute(jarvis_instance, text, original_text, match=None):
    from agent_module import RecorderAgent
    
    # Initialize rec_agent on jarvis_instance if not present
    if not hasattr(jarvis_instance, "rec_agent"):
        jarvis_instance.rec_agent = None

    if "record video" in text:
        if jarvis_instance.rec_agent is None:
            jarvis_instance.rec_agent = RecorderAgent()
        jarvis_instance._respond("Starting Video Recording. Say 'Jarvis Stop Video' to end it.")
        jarvis_instance.rec_agent.start_video_recording("jarvis_video")
        return False

    if "record screen" in text or "start screen recording" in text:
        if jarvis_instance.rec_agent is None:
            jarvis_instance.rec_agent = RecorderAgent()
        jarvis_instance._respond("Starting Screen Recording. Say 'Jarvis Stop Screen Recording' to end it.")
        jarvis_instance.rec_agent.start_screen_recording("jarvis_screen")
        return False

    if "stop video" in text or "stop screen recording" in text or "stop recording" in text:
        if jarvis_instance.rec_agent is not None:
            jarvis_instance.rec_agent.stop_recording() 
            jarvis_instance._respond("Recording stopped.")
            jarvis_instance.rec_agent = None
        else:
            jarvis_instance._respond("No active recording is running.")
        return False

    if "record voice" in text or "record audio" in text:
        rec_agent = RecorderAgent()
        jarvis_instance._respond("Recording started. Please press ENTER in the terminal window to stop.")
        
        # This runs in a thread but blocks the mic logic, so we wait for Key Press
        file = rec_agent.start_audio_recording("jarvis_audio")
        
        # Since we used 'input()' inside the agent (simulated), we ask for name now
        jarvis_instance._respond("Recording saved. What should I name this file?")
        new_name = jarvis_instance._force_listen()
        if new_name:
            old_path = file
            new_path = file.replace("jarvis_audio", new_name.replace(" ", "_"))
            os.rename(old_path, new_path)
            jarvis_instance._respond(f"Renamed to {new_name}.wav")
        return False
        
    return None
