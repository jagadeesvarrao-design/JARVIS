import os
import re
import time
import urllib.parse

def get_triggers():
    return [r"\bwhatsapp\b"]

def execute(jarvis_instance, text, original_text, match=None):
    import pyautogui
    jarvis_instance._respond("Recipient?")
    name = jarvis_instance._force_listen()
    if not name:
        return False
    
    # 1. Get Number
    contact = jarvis_instance.contacts.get_contact(name)
    phone = None
    if contact and "phone" in contact:
        phone = contact["phone"]
    else:
        jarvis_instance._respond(f"I need the number for {name}. Please enter it.")
        phone = pyautogui.prompt(text=f"Enter Number for {name}:", title="WhatsApp")
    
    if not phone:
        return False
    
    jarvis_instance._respond("Message?")
    msg = jarvis_instance._force_listen()
    
    if msg:
        jarvis_instance._respond("Opening WhatsApp Desktop...")
        # 2. Use Windows Protocol to open the App directly
        # Ensure number format (remove + if user typed it, we add it safely)
        clean_phone = phone.replace("+", "").replace(" ", "")
        
        # Command to open WhatsApp App
        os.system(f"start whatsapp://send?phone={clean_phone}&text={urllib.parse.quote(msg)}")
        
        # 3. Press Enter to send (Wait for app to load)
        time.sleep(2) # Wait 2 seconds for app to open
        pyautogui.press('enter')
        jarvis_instance._respond("Message sent.")
    return False
