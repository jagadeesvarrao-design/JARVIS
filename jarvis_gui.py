import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import os
from jarvis import JARVIS
import json
import random
import threading
import datetime 
import re
import requests
import pythoncom
from proactive_module import ProactiveAgent
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QDesktopWidget, QDialog, 
                             QLineEdit, QFormLayout, QFileDialog, QMessageBox, QFrame, 
                             QGraphicsOpacityEffect) # Added QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve # Added Animation classes
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap

# Import Backend
from jarvis import JARVIS
# ========================================================
# 🖼️ HOLOGRAM POPUP (Display Images)
# ========================================================
class HologramPopup(QDialog):
    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Hologram: {query}")
        self.setFixedSize(600, 400)
        self.setStyleSheet("background-color: #050505; border: 2px solid cyan;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        
        # Image Label
        self.img_label = QLabel("INITIALIZING HOLOGRAM...")
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("color: cyan; font-family: Consolas; font-size: 14px;")
        layout.addWidget(self.img_label)
        
        # Close Button
        btn = QPushButton("CLOSE PROJECTION")
        btn.setStyleSheet("background-color: #004444; color: cyan; font-weight: bold; border: 1px solid cyan;")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)
        
        # Fetch Image in background
        self.fetch_image(query)

    def fetch_image(self, query):
        try:
            # Use Bing's Thumbnail API (Reliable & Free)
            url = f"https://tse2.mm.bing.net/th?q={query}&w=600&h=400&c=7&rs=1&p=0&dpr=3&pid=1.7&mkt=en-IN&adlt=moderate"
            data = requests.get(url, timeout=5).content
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.img_label.setPixmap(pixmap.scaled(580, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            self.img_label.setText(f"VISUAL ERROR: {e}")

# ========================================================
# 📊 DASHBOARD LOGGER
# ========================================================
def log_to_dashboard(type, message):
    """Writes logs to jarvis_logs.json for the Streamlit Dashboard"""
    log_file = "jarvis_logs.json"
    entry = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "type": type, # "user", "jarvis", or "task"
        "message": message
    }
    
    data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except: pass
        
    data.append(entry)
    
    # Keep only last 50 logs to prevent lag
    if len(data) > 50: data = data[-50:]
        
    tmp_file = log_file + ".tmp"
    try:
        with open(tmp_file, "w") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_file, log_file)
    except Exception as e:
        print(f"Error writing dashboard log: {e}")

# ========================================================
# 🔧 WORKER THREAD (Backend Connection + Audio Fix)
# ========================================================
class JarvisThread(QThread):
    state_signal = pyqtSignal(str)
    text_signal = pyqtSignal(str) # Signal to send text to GUI
    image_signal = pyqtSignal(str) # ✨ NEW: Signal to show image

    def __init__(self):
        super().__init__()
        self.jarvis = None 

    def run(self):
        # ✨ MAGIC LINE: Audio Permission for Thread
        pythoncom.CoInitialize()
        self.jarvis = JARVIS()
        
        # Connect JARVIS functions to GUI
        self.original_respond = self.jarvis._respond
        self.original_listen = self.jarvis._listen_for_command
        self.original_process = self.jarvis.process_command

        # Override JARVIS methods with GUI wrappers
        self.jarvis._respond = self.gui_respond
        self.jarvis._listen_for_command = self.gui_listen
        self.jarvis.process_command = self.gui_process_wrapper

        self.state_signal.emit("idle")
        self.jarvis.run()
        pythoncom.CoUninitialize()

    def gui_respond(self, text):
        """Called when JARVIS speaks"""
        self.state_signal.emit("talking")
        
        # 1. CHECK FOR IMAGE TAGS (Regex)
        image_pattern = r"\[(?:SIMPLE_IMAGE_REQUEST|Image of|IMAGE).*?:?\s*(.*?)\]"
        match = re.search(image_pattern, text, re.IGNORECASE)
        
        clean_text = text
        if match:
            query = match.group(1)
            # Remove the tag from spoken text
            clean_text = re.sub(image_pattern, "", text).strip()
            # Signal GUI to show image
            self.image_signal.emit(query)

        # 2. Update Chat & Log
        self.text_signal.emit(f"🤖 {clean_text}") 
        
        # ✨ LOG TO DASHBOARD
        log_to_dashboard("jarvis", clean_text)
        
        # 3. Speak (Clean text only)
        self.original_respond(clean_text)
        self.state_signal.emit("idle")

    def gui_listen(self):
        """Called when JARVIS listens"""
        self.state_signal.emit("listening")
        return self.original_listen()
    
    def gui_process_wrapper(self, text):
        """Called when User speaks"""
        self.state_signal.emit("thinking")
        self.text_signal.emit(f"👤 {text}")
        
        # ✨ LOG TO DASHBOARD
        log_to_dashboard("user", text)
        
        return self.original_process(text)

    def set_attachment(self, path):
        if self.jarvis:
            # We inject the variable directly into the JARVIS instance
            self.jarvis.attachment_path = path

# ========================================================
# 👁️ AVATAR WIDGET (Face + Mouth)
# ========================================================
class FaceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 100) # Size of the Face Box
        self.state = "idle"
        self.color = QColor(0, 255, 255) # Cyan
        self.mouth_height = 2
        
        # Blink & Look Logic
        self.pupil_x = 0
        self.pupil_y = 0
        self.blink_h = 0
        self.is_blinking = False
        
        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        
        self.mood_timer = QTimer(self)
        self.mood_timer.timeout.connect(self.random_mood)
        self.mood_timer.start(2000)

    def set_state(self, state):
        self.state = state
        if state == "idle": self.color = QColor(0, 255, 255)
        elif state == "listening": self.color = QColor(0, 255, 100)
        elif state == "talking": self.color = QColor(255, 50, 50)
        elif state == "thinking": self.color = QColor(180, 0, 255)
        self.update()

    def random_mood(self):
        if self.state == "idle":
            if random.random() > 0.7: self.is_blinking = True
            self.pupil_x = random.randint(-5, 5)
        elif self.state == "listening":
            self.pupil_x = 0

    def animate(self):
        # Blink Animation
        if self.is_blinking:
            self.blink_h += 10
            if self.blink_h >= 40: self.is_blinking = False
        else:
            if self.blink_h > 0: self.blink_h -= 10
            
        # Mouth Talking Animation (Waveform)
        if self.state == "talking":
            self.mouth_height = random.randint(5, 25)
        else:
            self.mouth_height = 2
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Eyes
        eye_w, eye_h = 35, 25 - (self.blink_h / 2)
        if eye_h < 2: eye_h = 2
        
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        
        # Left Eye
        painter.drawRoundedRect(QRectF(25 + self.pupil_x, 30, eye_w, eye_h), 10, 10)
        # Right Eye
        painter.drawRoundedRect(QRectF(80 + self.pupil_x, 30, eye_w, eye_h), 10, 10)
        
        # Draw Mouth (Digital Waveform)
        center_x = 70
        mouth_y = 80
        painter.setPen(QPen(self.color, 3))
        
        if self.state == "talking":
            # Draw a jagged voice line
            points = [
                QPointF(center_x - 30, mouth_y),
                QPointF(center_x - 15, mouth_y - self.mouth_height),
                QPointF(center_x, mouth_y + self.mouth_height),
                QPointF(center_x + 15, mouth_y - self.mouth_height),
                QPointF(center_x + 30, mouth_y)
            ]
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i+1])
        else:
            # Flat line
            painter.drawLine(center_x - 20, mouth_y, center_x + 20, mouth_y)

# ========================================================
# 📇 MASTER CONTACT DATABASE (WhatsApp & Gmail)
# ========================================================
class AddContactDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Database")
        self.setFixedSize(350, 250)
        # Sci-Fi Style Form
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; border: 2px solid cyan; }
            QLabel { color: cyan; font-weight: bold; font-family: Arial; }
            QLineEdit { background-color: #333; color: white; padding: 5px; border: 1px solid #555; }
            QPushButton { background-color: #005555; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #007777; }
        """)
        
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit(self)
        self.phone_input = QLineEdit(self)
        self.phone_input.setPlaceholderText("+91...")
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("example@gmail.com")
        
        layout.addRow("Name (Required):", self.name_input)
        layout.addRow("Phone (WhatsApp):", self.phone_input)
        layout.addRow("Email (Gmail):", self.email_input)
        
        btn = QPushButton("💾 SAVE TO SYSTEM", self)
        btn.clicked.connect(self.save_contact)
        layout.addRow(btn)
        
    def save_contact(self):
        name = self.name_input.text().strip().lower() # Save as lowercase key
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        
        if name:
            file_path = "contacts.json"
            data = {}
            
            # 1. Load Existing Data
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                except: data = {}
            
            # 2. Update Logic (Don't overwrite if empty)
            if name not in data:
                data[name] = {"phone": "", "email": ""}
                
            if phone: data[name]["phone"] = phone
            if email: data[name]["email"] = email
            
            # 3. Save Back
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
                
            QMessageBox.information(self, "Database Updated", f"Contact '{name.title()}' saved successfully.\nPhone: {data[name]['phone']}\nEmail: {data[name]['email']}")
            self.close()
        else:
            QMessageBox.warning(self, "Input Error", "You must enter a Name.")

# ========================================================
# 🖥️ MAIN DOCK (The Command Center)
# ========================================================
class JarvisDock(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS COMMAND")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Position at Bottom
        screen = QDesktopWidget().screenGeometry()
        self.width = 900
        self.height = 140
        self.move((screen.width() - self.width) // 2, screen.height() - self.height - 40)
        self.resize(self.width, self.height)

        # Main Layout (Glass Bar)
        # We save this as self.container to apply effects to it
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 10, 10, 230);
                border: 2px solid cyan;
                border-radius: 20px;
            }
        """)
        
        # ===================================================
        # 👻 GHOST MODE SETUP (Opacity)
        # ===================================================
        self.opacity_effect = QGraphicsOpacityEffect(self.container)
        self.opacity_effect.setOpacity(1.0) # Start fully visible
        self.container.setGraphicsEffect(self.opacity_effect)
        
        # Animation
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(500) # 0.5 seconds fade duration
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        # ===================================================
        
        layout = QHBoxLayout(self.container)
        self.setCentralWidget(self.container)

        # 1. THE FACE (Left)
        self.face = FaceWidget()
        layout.addWidget(self.face)

        # 2. THE CHAT LOG (Center)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #00ffff;
            font-family: Consolas;
            font-size: 13px;
        """)
        self.chat_display.setPlaceholderText("SYSTEM ONLINE. WAITING FOR COMMAND...")
        layout.addWidget(self.chat_display)

        # 3. CONTROL PANEL (Right)
        btn_layout = QVBoxLayout()
        
        # Add Contact Button
        self.btn_contact = QPushButton("➕ Update DB")
        self.btn_contact.setToolTip("Add Phone or Email")
        self.btn_contact.setStyleSheet("""
            QPushButton { background-color: #004444; color: cyan; border: 1px solid cyan; border-radius: 5px; padding: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #006666; }
        """)
        self.btn_contact.clicked.connect(self.open_add_contact)
        
        # Attach File Button
        self.btn_attach = QPushButton("📎 Attach File")
        self.btn_attach.setToolTip("Select file for Email")
        self.btn_attach.setStyleSheet("""
            QPushButton { background-color: #004444; color: white; border: 1px solid white; border-radius: 5px; padding: 5px; }
            QPushButton:hover { background-color: #006666; }
        """)
        self.btn_attach.clicked.connect(self.attach_file)
        
        # Status Label
        self.lbl_attach = QLabel("No Attachment")
        self.lbl_attach.setStyleSheet("color: gray; font-size: 10px; border: none; background: transparent;")
        self.lbl_attach.setAlignment(Qt.AlignCenter)
        
        btn_layout.addWidget(self.btn_contact)
        btn_layout.addWidget(self.btn_attach)
        btn_layout.addWidget(self.lbl_attach)
        
        layout.addLayout(btn_layout)

        # Backend Thread
        self.thread = JarvisThread()
        # ✨ Connect signal to update_state instead of face directly to handle Ghost Mode
        self.thread.state_signal.connect(self.update_state) 
        self.thread.text_signal.connect(self.update_chat)
        self.thread.image_signal.connect(self.show_hologram) # ✨ CONNECT IMAGE SIGNAL
        self.thread.start()

    # ===================================================
    # 👻 GHOST MODE LOGIC (States & Hover)
    # ===================================================
    def update_state(self, state):
        self.face.set_state(state)
        
        if state == "idle":
            # Fade Out (Dim) to 20%
            self.anim.setStartValue(self.opacity_effect.opacity())
            self.anim.setEndValue(0.2)
            self.anim.start()
        else:
            # Fade In (Bright) to 100%
            self.anim.setStartValue(self.opacity_effect.opacity())
            self.anim.setEndValue(1.0)
            self.anim.start()

    def enterEvent(self, event):
        # Mouse Hover -> Brighten
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Mouse Leave -> Return to appropriate brightness
        if self.face.state == "idle":
            self.anim.setStartValue(self.opacity_effect.opacity())
            self.anim.setEndValue(0.2)
            self.anim.start()
        super().leaveEvent(event)
    # ===================================================

    def update_chat(self, text):
        self.chat_display.append(text)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def open_add_contact(self):
        dialog = AddContactDialog(self)
        dialog.exec_()

    def attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Attachment")
        if file_path:
            file_name = os.path.basename(file_path)
            self.lbl_attach.setText(f"📎 {file_name}")
            self.lbl_attach.setStyleSheet("color: yellow; font-size: 11px; border: none; background: transparent;")
            # Send to backend
            self.thread.set_attachment(file_path)

    def show_hologram(self, query):
        # Create and show the popup image
        self.popup = HologramPopup(query, self)
        self.popup.show()
# ========================================================
# 🚀 SYSTEM BOOTUP (GUI + Proactive Vision Thread)
# ========================================================
def run_proactive():
    """Wrapper to safely initialize Windows Audio in a background thread"""
    import pythoncom
    pythoncom.CoInitialize()
    proactive_brain = ProactiveAgent()
    proactive_brain.start_monitoring()

if __name__ == "__main__":
    # 1. Start the Proactive Vision & Health Monitor in the background
    vision_thread = threading.Thread(target=run_proactive)
    vision_thread.daemon = True # Ensures it closes when JARVIS closes
    vision_thread.start()

    # 2. Launch the GUI
    app = QApplication(sys.argv)
    gui = JarvisDock()
    gui.show()
    sys.exit(app.exec_())