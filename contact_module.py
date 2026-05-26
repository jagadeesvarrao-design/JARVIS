import json
import os

class ContactManager:
    def __init__(self, filename="contacts.json"):
        self.filename = filename
        self.contacts = self._load_contacts()

    def _load_contacts(self):
        """Loads contacts from the JSON file. Creates one if missing."""
        if not os.path.exists(self.filename):
            return {}
        
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading contacts: {e}")
            return {}

    def get_contact(self, name):
        """Searches for a contact by name (case-insensitive)."""
        name = name.lower().strip()
        
        # 1. Direct Match
        if name in self.contacts:
            return self.contacts[name]
        
        # 2. Partial Match (e.g., "Dad" matches "My Dad")
        for stored_name, info in self.contacts.items():
            if name in stored_name:
                return info
                
        return None

    def add_contact(self, name, phone=None, email=None):
        """Saves a new contact."""
        name = name.lower().strip()
        
        if name not in self.contacts:
            self.contacts[name] = {}
        
        if phone:
            self.contacts[name]["phone"] = phone
        if email:
            self.contacts[name]["email"] = email
            
        self._save_contacts()
        print(f"✅ Contact '{name}' saved.")

    def _save_contacts(self):
        """Writes the contact list to the file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.contacts, f, indent=4)
        except Exception as e:
            print(f"❌ Could not save contacts: {e}")

# simple test block
if __name__ == "__main__":
    cm = ContactManager()
    # cm.add_contact("mom", phone="+919999999999")
    # print(cm.get_contact("mom"))
        
   