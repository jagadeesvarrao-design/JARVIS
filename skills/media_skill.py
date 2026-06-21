import re

def get_triggers():
    return [
        r"\bplay\b.*\bmusic\b",
        r"^play\s+.+",
        r"\b(?:volume|mute|pause|next track|previous track)\b"
    ]

def execute(jarvis_instance, text, original_text, match=None):
    if any(x in text for x in ["volume", "mute", "pause", "next track", "previous track"]):
        jarvis_instance.automation.media_control(text)
        return False
        
    if "play" in text and "music" in text:
        jarvis_instance._respond("Playing on YouTube...")
        jarvis_instance.automation.play_music(text)
        return False
        
    if text.startswith("play") and len(text.split()) <= 6:
        jarvis_instance._respond("Playing...")
        jarvis_instance.automation.play_music(text)
        return False
        
    return None
