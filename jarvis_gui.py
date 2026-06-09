import sys
# Initialize QApplication first to set up COM in STA mode for PyQt
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import os
import json
import random
import threading
import datetime 
import re
import requests
import pythoncom
from proactive_module import ProactiveAgent
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QDesktopWidget, QDialog, 
                             QLineEdit, QFormLayout, QFileDialog, QMessageBox, QFrame, 
                             QGraphicsOpacityEffect) # Added QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve, QRect # Added Animation classes
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QCursor

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
        self.setStyleSheet("background-color: #000000; border: 2px solid #333333;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        
        # Image Label
        self.img_label = QLabel("INITIALIZING HOLOGRAM...")
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("color: #ffffff; font-family: Consolas; font-size: 14px;")
        layout.addWidget(self.img_label)
        
        # Close Button
        btn = QPushButton("CLOSE PROJECTION")
        btn.setStyleSheet("background-color: #222222; color: #ffffff; font-weight: bold; border: 1px solid #444444;")
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
        self.color = QColor(240, 240, 240) # White/Silver
        self.mouth_height = 2
        
        # Blink & Look Logic
        self.pupil_x = 0
        self.pupil_y = 0
        self.blink_h = 0
        self.is_blinking = False
        
        # Breathing pulse for listening state
        self.pulse_val = 1.0
        self.pulse_dir = -1
        
        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        
        self.mood_timer = QTimer(self)
        self.mood_timer.timeout.connect(self.random_mood)
        self.mood_timer.start(2000)

    def set_state(self, state):
        self.state = state
        if state == "idle": self.color = QColor(240, 240, 240)
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
            
        # Pulse animation for listening state
        if self.state == "listening":
            self.pulse_val += self.pulse_dir * 0.04
            if self.pulse_val <= 0.4:
                self.pulse_val = 0.4
                self.pulse_dir = 1
            elif self.pulse_val >= 1.0:
                self.pulse_val = 1.0
                self.pulse_dir = -1
        else:
            self.pulse_val = 1.0
            
        self.update()

    def mousePressEvent(self, event):
        parent = self.parentWidget()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parentWidget()
        if parent and hasattr(parent, 'toggle_collapse'):
            parent.toggle_collapse()
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Eyes
        eye_w, eye_h = 35, 25 - (self.blink_h / 2)
        if eye_h < 2: eye_h = 2
        
        # Apply glow/pulse effect to color
        pulsed_color = QColor(self.color)
        if self.state == "listening":
            pulsed_color.setAlpha(int(255 * self.pulse_val))
            
        painter.setBrush(QBrush(pulsed_color))
        painter.setPen(Qt.NoPen)
        
        # Left Eye
        painter.drawRoundedRect(QRectF(25 + self.pupil_x, 30, eye_w, eye_h), 10, 10)
        # Right Eye
        painter.drawRoundedRect(QRectF(80 + self.pupil_x, 30, eye_w, eye_h), 10, 10)
        
        # Draw Mouth (Digital Waveform)
        center_x = 70
        mouth_y = 80
        
        pen_color = QColor(self.color)
        if self.state == "listening":
            pen_color.setAlpha(int(255 * self.pulse_val))
        painter.setPen(QPen(pen_color, 3))
        
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
            QDialog { background-color: #0a0a0a; border: 2px solid #333333; }
            QLabel { color: #ffffff; font-weight: bold; font-family: Arial; }
            QLineEdit { background-color: #222; color: white; padding: 5px; border: 1px solid #444; }
            QPushButton { background-color: #222; color: white; padding: 8px; border-radius: 4px; font-weight: bold; border: 1px solid #444; }
            QPushButton:hover { background-color: #333; }
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

        # State flags
        self.is_expanded = False
        self.is_relocating = False

        # Screen calculations
        screen = QDesktopWidget().screenGeometry()
        self.collapsed_width = 320
        self.collapsed_height = 42
        self.expanded_width = 860
        self.expanded_height = 160
        
        # Initial position: floating Top-Center
        self.move((screen.width() - self.collapsed_width) // 2, 30)
        self.resize(self.collapsed_width, self.collapsed_height)

        # Main glassmorphic container
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 245);
                border: 2px solid #333333;
                border-radius: 20px;
            }
        """)
        self.setCentralWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(6, 6, 6, 6)

        # ----------------------------------------------------
        # 1. COLLAPSED VIEW LAYOUT
        # ----------------------------------------------------
        self.collapsed_widget = QWidget()
        collapsed_layout = QHBoxLayout(self.collapsed_widget)
        collapsed_layout.setContentsMargins(15, 0, 15, 0)

        # Status Dot
        self.lbl_status_dot = QLabel()
        self.lbl_status_dot.setFixedSize(12, 12)
        self.lbl_status_dot.setStyleSheet("background-color: #ffffff; border-radius: 6px;")

        # Status Text
        self.lbl_status_text = QLabel("JARVIS: ONLINE")
        self.lbl_status_text.setStyleSheet("color: #ffffff; font-family: Consolas; font-size: 11px; font-weight: bold; border: none; background: transparent;")

        # Clock Text
        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet("color: white; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
        
        collapsed_layout.addWidget(self.lbl_status_dot)
        collapsed_layout.addWidget(self.lbl_status_text)
        collapsed_layout.addStretch()
        collapsed_layout.addWidget(self.lbl_clock)

        self.main_layout.addWidget(self.collapsed_widget)

        # Clock Updater Timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        # ----------------------------------------------------
        # 2. EXPANDED CONSOLE LAYOUT
        # ----------------------------------------------------
        self.expanded_widget = QWidget()
        expanded_layout = QHBoxLayout(self.expanded_widget)
        expanded_layout.setContentsMargins(5, 0, 5, 0)

        # Face/Avatar Widget (Left)
        self.face = FaceWidget()
        expanded_layout.addWidget(self.face)

        # Center Console (Chat Logs & Silent Text Input line)
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(5, 0, 5, 0)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #ffffff;
            font-family: Consolas;
            font-size: 13px;
        """)
        self.chat_display.setPlaceholderText("SYSTEM ONLINE. WAITING FOR COMMAND...")

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Type silent command and press Enter...")
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(20, 20, 20, 180);
                border: 1px solid #333333;
                border-radius: 5px;
                color: #ffffff;
                font-family: Consolas;
                font-size: 12px;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #ffffff;
            }
        """)
        self.cmd_input.returnPressed.connect(self.submit_text_command)

        center_layout.addWidget(self.chat_display)
        center_layout.addWidget(self.cmd_input)
        expanded_layout.addLayout(center_layout, stretch=4)

        # Control Panel Widgets (Right)
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(5, 0, 5, 0)

        self.btn_contact = QPushButton("➕ Update DB")
        self.btn_contact.setToolTip("Add Phone or Email")
        self.btn_contact.setStyleSheet("""
            QPushButton { background-color: #222222; color: #ffffff; border: 1px solid #444444; border-radius: 5px; padding: 4px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #333333; }
        """)
        self.btn_contact.clicked.connect(self.open_add_contact)

        self.btn_attach = QPushButton("📎 Attach File")
        self.btn_attach.setToolTip("Select file for Email")
        self.btn_attach.setStyleSheet("""
            QPushButton { background-color: #004444; color: white; border: 1px solid white; border-radius: 5px; padding: 4px; font-size: 11px; }
            QPushButton:hover { background-color: #006666; }
        """)
        self.btn_attach.clicked.connect(self.attach_file)

        self.lbl_attach = QLabel("No Attachment")
        self.lbl_attach.setStyleSheet("color: gray; font-size: 10px; border: none; background: transparent;")
        self.lbl_attach.setAlignment(Qt.AlignCenter)

        self.btn_collapse = QPushButton("➖ Collapse")
        self.btn_collapse.setStyleSheet("""
            QPushButton { background-color: #440000; color: #ff5555; border: 1px solid #ff5555; border-radius: 5px; padding: 4px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #660000; }
        """)
        self.btn_collapse.clicked.connect(self.collapse)

        btn_layout.addWidget(self.btn_contact)
        btn_layout.addWidget(self.btn_attach)
        btn_layout.addWidget(self.lbl_attach)
        btn_layout.addWidget(self.btn_collapse)

        expanded_layout.addLayout(btn_layout, stretch=1)
        self.main_layout.addWidget(self.expanded_widget)

        # Hide the expanded components at initialization
        self.expanded_widget.hide()

        # ----------------------------------------------------
        # 3. ANIMATIONS & TIMERS SETUP
        # ----------------------------------------------------
        self.geom_anim = QPropertyAnimation(self, b"geometry")
        self.geom_anim.setDuration(250)
        self.geom_anim.setEasingCurve(QEasingCurve.InOutQuad)

        # 2-second hover timer for relocating
        self.relocate_hover_timer = QTimer(self)
        self.relocate_hover_timer.setSingleShot(True)
        self.relocate_hover_timer.timeout.connect(self.start_relocation)

        # Global mouse tracker loop for sticky drag
        self.relocate_tracking_timer = QTimer(self)
        self.relocate_tracking_timer.timeout.connect(self.track_cursor)

        # Connect GUI updates to backend Thread
        self.thread = JarvisThread()
        self.thread.state_signal.connect(self.update_state) 
        self.thread.text_signal.connect(self.update_chat)
        self.thread.image_signal.connect(self.show_hologram)
        self.thread.start()

    # --- CLOCK UPDATES ---
    def update_clock(self):
        self.lbl_clock.setText(datetime.datetime.now().strftime("%I:%M:%S %p"))

    # --- DRAG RELOCATION (2s Hover Sticky Follow) ---
    def start_relocation(self):
        if not self.is_expanded:
            self.is_relocating = True
            # Visual indicator: Magenta border
            self.container.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 0, 0, 245);
                    border: 2px solid magenta;
                    border-radius: 20px;
                }
            """)
            self.relocate_tracking_timer.start(15)

    def track_cursor(self):
        pos = QCursor.pos()
        self.move(pos.x() - self.width() // 2, pos.y() - self.height() // 2)

    def stop_relocation(self):
        self.is_relocating = False
        self.relocate_tracking_timer.stop()
        # Restore Cyan border
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 245);
                border: 2px solid #333333;
                border-radius: 20px;
            }
        """)

    # --- EVENT OVERRIDES ---
    def enterEvent(self, event):
        # Start hover relocation countdown if collapsed and not relocating
        if not self.is_expanded and not self.is_relocating:
            self.relocate_hover_timer.start(2000)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.relocate_hover_timer.stop()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.is_relocating:
            self.stop_relocation()
            event.accept()
        else:
            # Click collapsed pill to expand console
            if not self.is_expanded:
                self.expand()
                event.accept()
            else:
                super().mousePressEvent(event)

    # --- GEOMETRY TRANSITIONS ---
    def toggle_collapse(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        if self.is_expanded or self.is_relocating: return
        self.is_expanded = True
        
        current_geom = self.geometry()
        center_x = current_geom.x() + current_geom.width() // 2
        
        new_x = center_x - self.expanded_width // 2
        new_y = current_geom.y()
        
        self.geom_anim.stop()
        self.geom_anim.setStartValue(current_geom)
        self.geom_anim.setEndValue(QRect(new_x, new_y, self.expanded_width, self.expanded_height))
        
        self.collapsed_widget.hide()
        self.expanded_widget.show()
        self.geom_anim.start()

    def collapse(self):
        if not self.is_expanded: return
        self.is_expanded = False
        
        current_geom = self.geometry()
        center_x = current_geom.x() + current_geom.width() // 2
        
        new_x = center_x - self.collapsed_width // 2
        new_y = current_geom.y()
        
        self.geom_anim.stop()
        self.geom_anim.setStartValue(current_geom)
        self.geom_anim.setEndValue(QRect(new_x, new_y, self.collapsed_width, self.collapsed_height))
        
        self.expanded_widget.hide()
        self.collapsed_widget.show()
        self.geom_anim.start()

    # --- SILENT COMMAND INTERACTION ---
    def submit_text_command(self):
        text = self.cmd_input.text().strip()
        if text:
            self.cmd_input.clear()
            self.update_chat(f"👤 {text}")
            log_to_dashboard("user", text)
            
            # Execute command in background thread so GUI remains fluid
            def run_cmd():
                self.thread.gui_process_wrapper(text)
            import threading
            threading.Thread(target=run_cmd, daemon=True).start()

    # --- GUI COMPONENT UPDATES ---
    def update_state(self, state):
        self.face.set_state(state)
        self.lbl_status_text.setText(f"JARVIS: {state.upper()}")
        
        # Color codes matching system states
        if state == "idle":
            self.lbl_status_dot.setStyleSheet("background-color: #ffffff; border-radius: 6px;")
            self.lbl_status_text.setStyleSheet("color: #ffffff; font-family: Consolas; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        elif state == "listening":
            self.lbl_status_dot.setStyleSheet("background-color: #00ff64; border-radius: 6px;")
            self.lbl_status_text.setStyleSheet("color: #00ff64; font-family: Consolas; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        elif state == "talking":
            self.lbl_status_dot.setStyleSheet("background-color: #ff3232; border-radius: 6px;")
            self.lbl_status_text.setStyleSheet("color: #ff3232; font-family: Consolas; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        elif state == "thinking":
            self.lbl_status_dot.setStyleSheet("background-color: #b400ff; border-radius: 6px;")
            self.lbl_status_text.setStyleSheet("color: #b400ff; font-family: Consolas; font-size: 11px; font-weight: bold; border: none; background: transparent;")

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
    gui = JarvisDock()
    gui.show()
    sys.exit(app.exec_())