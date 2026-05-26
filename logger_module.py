import json
import os
from datetime import datetime

class ActivityLogger:
    def __init__(self, filename="jarvis_logs.json"):
        self.filename = filename
        # Create the log file if it doesn't exist
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)

    def log_message(self, role, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "role": role,
            "message": message
        }
        
        try:
            with open(self.filename, 'r+') as f:
                data = json.load(f)
                data.append(log_entry)
                f.seek(0)
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"📝 Logging Error: {e}")