import os
import re
import smtplib
import config
from email.message import EmailMessage

def get_triggers():
    # Matches commands that have both 'send' and 'email' in any order
    return [
        r"\bsend\b.*\bemail\b",
        r"\bemail\b.*\bsend\b"
    ]

def execute(jarvis_instance, text, original_text, match=None):
    import pyautogui
    # Check Config First
    if not hasattr(config, 'EMAIL_USER') or not config.EMAIL_USER:
        jarvis_instance._respond("Error. Email credentials missing in config file.")
        return False

    jarvis_instance._respond("Recipient?")
    name = jarvis_instance._force_listen()
    if not name:
        return False
    
    # Get Email Address
    email_addr = None
    contact = jarvis_instance.contacts.get_contact(name)
    if contact and "email" in contact:
        email_addr = contact["email"]
    else:
        jarvis_instance._respond(f"I need the email for {name}. Please enter it.")
        email_addr = pyautogui.prompt(text=f"Enter Email for {name}:", title="Email")
    
    if not email_addr:
        return False

    jarvis_instance._respond("Subject?")
    subj = jarvis_instance._force_listen() or "No Subject"
    
    jarvis_instance._respond("Message?")
    body = jarvis_instance._force_listen() or "Sent via Jarvis"

    # Ask for Attachment
    jarvis_instance._respond("Do you want to attach a file? Say yes or no.")
    attach_resp = jarvis_instance._force_listen()
    
    if attach_resp and "yes" in attach_resp.lower():
        jarvis_instance._respond("Please select the file on screen.")
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw() # Hide empty window
        jarvis_instance.attachment_path = filedialog.askopenfilename(title="Select Attachment")
        root.destroy()
    
    jarvis_instance._respond("Sending...")
    
    try:
        msg = EmailMessage()
        msg['Subject'] = subj
        msg['From'] = config.EMAIL_USER
        msg['To'] = email_addr
        msg.set_content(body)

        if getattr(jarvis_instance, "attachment_path", None) and os.path.exists(jarvis_instance.attachment_path):
            with open(jarvis_instance.attachment_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(jarvis_instance.attachment_path)
                msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
            print(f"📎 Attached: {jarvis_instance.attachment_path}")

        smtp_server = getattr(config, "SMTP_SERVER", "smtp.gmail.com")
        smtp_port = getattr(config, "SMTP_PORT", 465)
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
            smtp.login(config.EMAIL_USER, config.EMAIL_PASS)
            smtp.send_message(msg)

        jarvis_instance._respond("Email sent successfully.")
        jarvis_instance.attachment_path = None 
    except Exception as e:
        print(f"❌ Email Error: {e}")
        jarvis_instance._respond("Failed. Please check your internet or password.")
    return False
