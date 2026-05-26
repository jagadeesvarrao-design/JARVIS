import json
import os

class MemorySystem:
    def __init__(self, filename="memory.json"):
        self.filename = filename
        self.data = self._load_memory()

    def _load_memory(self):
        if not os.path.exists(self.filename):
            return {"facts": []}
        try:
            with open(self.filename, 'r') as f:
                content = json.load(f)
                if isinstance(content, dict) and "facts" in content:
                    return content
                return {"facts": []}
        except:
            return {"facts": []}

    def remember_fact(self, text):
        # FIX: Removes all variations of the command word
        clean_fact = text.replace("remember that", "").replace("remember", "").strip()
        
        # Capitalize and save
        clean_fact = clean_fact.capitalize()
        
        if not clean_fact:
            return "I didn't catch what to remember."

        self.data["facts"].append(clean_fact)
        self._save_memory()
        return f"Saved: '{clean_fact}'"

    def recall(self):
        if not self.data["facts"]:
            return None
        return " | ".join(self.data["facts"])

    def _save_memory(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)