import os
import time
import webbrowser
import ctypes

class ApplicationController:
    def __init__(self):
        print("🛠️ Automation Module Loaded")

    # =================================================================
    # 🔍 WINDOW SENSOR (New Feature)
    # =================================================================
    def get_active_window_title(self):
        """Reads the title of the window you are currently using"""
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value.lower()

    def get_open_windows(self):
        """Returns titles of all currently open and visible windows using pywinauto"""
        try:
            from pywinauto import Desktop
            windows = Desktop(backend="uia").windows()
            titles = []
            for w in windows:
                try:
                    title = w.window_text()
                    if w.is_visible() and title and len(title.strip()) > 0:
                        if title not in titles:
                            titles.append(title)
                except:
                    continue
            return titles
        except Exception as e:
            print(f"Error listing windows: {e}")
            return []

    def activate_window(self, app_name):
        """Locates an open window by name and brings it to the foreground"""
        print(f"🔍 Searching for window matching: '{app_name}'")
        try:
            from pywinauto import Desktop
            windows = Desktop(backend="uia").windows()
            for w in windows:
                try:
                    title = w.window_text()
                    if app_name.lower() in title.lower() and w.is_visible():
                        print(f"🎯 Found window: '{title}'. Activating...")
                        w.set_focus()
                        return f"Activated window '{title}'."
                except:
                    continue
            return f"Could not find any open window matching '{app_name}'."
        except Exception as e:
            return f"Error activating window: {e}"

    def close_window_gracefully(self, app_name):
        """Locates an open window by name and closes it gracefully"""
        print(f"❌ Closing window matching: '{app_name}'")
        try:
            from pywinauto import Desktop
            windows = Desktop(backend="uia").windows()
            for w in windows:
                try:
                    title = w.window_text()
                    if app_name.lower() in title.lower() and w.is_visible():
                        print(f"🎯 Closing window: '{title}'")
                        w.close()
                        return f"Closed window '{title}' gracefully."
                except:
                    continue
            return f"Could not find any open window matching '{app_name}'."
        except Exception as e:
            return f"Error closing window: {e}"

    # =================================================================
    # 1. SMART APP MANAGEMENT (Open/Close)
    # =================================================================
    def open_app(self, command):
        """Opens an application using AppOpener, System Command, or Search"""
        import pyautogui
        app_name = command.replace("open", "").strip().lower()
        if not app_name: return "What app?"
        
        print(f"📂 Launching: {app_name}")

        # --- NEW: YouTube App Specific Fix ---
        if "youtube" in app_name:
            # Forces the 'App View' (No URL bar, standalone window)
            os.system("start msedge --app=https://www.youtube.com")
            return "Opening YouTube App."

        # 1. Custom Browser Fixes (faster than AppOpener)
        if "chrome" in app_name:
            os.system("start chrome")
            return "Opening Chrome."
        if "edge" in app_name or "browser" in app_name:
            os.system("start msedge")
            return "Opening Edge."
        
        # 2. Try AppOpener
        try:
            from AppOpener import open as app_opener
            app_opener(app_name, match_closest=True, throw_error=True)
            return f"Opened {app_name}."
        except:
            # 3. Fallback to Windows Search (The "Hacker" way)
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(app_name)
            time.sleep(0.5)
            pyautogui.press('enter')
            return f"Attempting to launch {app_name}."

    def close_app(self, command):
        """Smart Closing: Distinguishes between Browser Tabs and Apps, uses pywinauto graceful close first"""
        import pyautogui
        app_name = command.replace("close", "").strip().lower()
        print(f"❌ Closing: {app_name}")

        # 1. BROWSER TABS (The Fix for "Close YouTube")
        browser_keywords = ["youtube", "google", "tab", "browser", "search", "gmail", "whatsapp"]
        if any(word in app_name for word in browser_keywords):
            pyautogui.hotkey('ctrl', 'w')
            return f"Closed tab for {app_name}."

        # 2. Try pywinauto graceful close
        res = self.close_window_gracefully(app_name)
        if "Closed window" in res:
            return res

        # 3. SYSTEM APPS (Safety Fix)
        if "code" in app_name or "visual studio" in app_name:
            os.system("taskkill /f /im Code.exe")
            return "Closed VS Code."
            
        try:
            from AppOpener import close as app_closer
            app_closer(app_name, match_closest=True, throw_error=True)
            return f"Closed {app_name}."
        except:
            try:
                # Force Kill if AppOpener fails
                os.system(f"taskkill /f /im {app_name}.exe")
                return f"Terminated {app_name}"
            except:
                return f"Could not find a running app named {app_name}."

    # =================================================================
    # 2. SMART MUSIC & TYPING (Upgraded)
    # =================================================================
    def play_music(self, command):
        """
        1. If YouTube is OPEN: Types in the search bar.
        2. If YouTube is CLOSED: Opens the YouTube APP.
        """
        import pyautogui
        song = command.lower()
        remove_words = ["play", "on youtube", "song", "music", "video", "please", "search", "for"]
        for word in remove_words:
            song = song.replace(word, "")
        song = song.strip()
        
        if not song: return "What should I play?"

        # Check Active Window
        current_window = self.get_active_window_title()
        print(f"👀 Current Window: {current_window}")

        # SCENARIO A: YouTube is ALREADY on screen (Existing Window)
        if "youtube" in current_window:
            print("✅ YouTube is active. Using Hotkeys.")
            pyautogui.press('/') # Focus Search Bar
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'a') # Select existing text
            pyautogui.press('backspace')  # Clear it
            pyautogui.write(song, interval=0.05) # Type new song
            time.sleep(0.2)
            pyautogui.press('enter') # Search
            return f"Searching for {song} on existing screen."

        # SCENARIO B: YouTube is NOT open (Launch App)
        else:
            print("🚀 YouTube not active. Launching App.")
            search_url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
            os.system(f"start msedge --app={search_url}")
            return f"Opening YouTube App for {song}."

    def type_text(self, text):
        import pyautogui
        clean_text = text.replace("write", "").replace("type", "").strip()
        time.sleep(1.0) # Buffer to let you switch windows
        try:
            from pywinauto.keyboard import send_keys
            # Escape braces which have special meaning in pywinauto send_keys
            escaped_text = ""
            for char in clean_text:
                if char == '{':
                    escaped_text += '{{}'
                elif char == '}':
                    escaped_text += '{}}'
                else:
                    escaped_text += char
            send_keys(escaped_text, with_spaces=True)
            return "Typed using pywinauto."
        except Exception as e:
            print(f"pywinauto typing failed: {e}. Falling back to pyautogui.")
            pyautogui.write(clean_text, interval=0.05) 
            return "Typed using pyautogui fallback."

    # =================================================================
    # 3. MEDIA CONTROLS
    # =================================================================
    def media_control(self, command):
        import pyautogui
        command = command.lower()
        if "volume up" in command: pyautogui.press("volumeup", presses=5)
        elif "volume down" in command: pyautogui.press("volumedown", presses=5)
        elif "mute" in command: pyautogui.press("volumemute")
        elif "play" in command or "pause" in command or "stop" in command: pyautogui.press("playpause")
        elif "next" in command: pyautogui.press("nexttrack")
        elif "previous" in command: pyautogui.press("prevtrack")
        return "Media command executed."

    # =================================================================
    # 4. MASTER SYSTEM AUTOMATION (Your Original Full List)
    # =================================================================
    def perform_action(self, command):
        import pyautogui
        command = command.lower()
        try:
            # --- Browser & Tabs ---
            if "new tab" in command: pyautogui.hotkey('ctrl', 't')
            elif "close tab" in command: pyautogui.hotkey('ctrl', 'w')
            elif "switch tab" in command: pyautogui.hotkey('ctrl', 'tab')
            elif "previous tab" in command: pyautogui.hotkey('ctrl', 'shift', 'tab')
            elif "new window" in command: pyautogui.hotkey('ctrl', 'n')
            elif "incognito" in command: pyautogui.hotkey('ctrl', 'shift', 'n')
            elif "refresh" in command: pyautogui.press('f5')
            elif "home page" in command: pyautogui.hotkey('alt', 'home')
            elif "back" in command: pyautogui.hotkey('alt', 'left')
            elif "forward" in command: pyautogui.hotkey('alt', 'right')
            
            # --- Zoom & Scroll ---
            elif "zoom in" in command: pyautogui.hotkey('ctrl', '+')
            elif "zoom out" in command: pyautogui.hotkey('ctrl', '-')
            elif "reset zoom" in command: pyautogui.hotkey('ctrl', '0')
            elif "scroll down" in command: pyautogui.scroll(-500)
            elif "scroll up" in command: pyautogui.scroll(500)
            elif "scroll to top" in command: pyautogui.hotkey('ctrl', 'home')
            elif "scroll to bottom" in command: pyautogui.hotkey('ctrl', 'end')

            # --- Window Management ---
            elif "minimise" in command and "window" in command: pyautogui.hotkey('win', 'down')
            elif "maximise" in command: pyautogui.hotkey('win', 'up')
            elif "minimise" in command: pyautogui.hotkey('win', 'd') # Desktop
            elif "close window" in command: pyautogui.hotkey('alt', 'f4')
            elif "switch window" in command: pyautogui.hotkey('alt', 'tab')
            elif "lock screen" in command: pyautogui.hotkey('win', 'l')
            elif "show desktop" in command: pyautogui.hotkey('win', 'd')
            
            # --- Editing Shortcuts ---
            elif "select all" in command: pyautogui.hotkey('ctrl', 'a')
            elif "copy" in command: pyautogui.hotkey('ctrl', 'c')
            elif "paste" in command: pyautogui.hotkey('ctrl', 'v')
            elif "delete" in command: pyautogui.press('delete')
            elif "enter" in command: pyautogui.press('enter')
            elif "save" in command: pyautogui.hotkey('ctrl', 's')
            elif "undo" in command: pyautogui.hotkey('ctrl', 'z')
            elif "redo" in command: pyautogui.hotkey('ctrl', 'y')
            elif "clear text" in command: pyautogui.press('backspace', presses=50)

            # --- Screenshots (Improved Logic) ---
            elif "screenshot" in command:
                # Saves with timestamp to prevent overwriting
                filename = f"screenshot_{int(time.time())}.png"
                # Tries to save to Desktop
                path = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', filename)
                if not os.path.exists(os.path.dirname(path)):
                    path = os.path.join(os.environ['USERPROFILE'], 'Desktop', filename)
                
                pyautogui.screenshot(path)
                return f"Screenshot saved."

            # --- System Tools ---
            elif "task manager" in command: pyautogui.hotkey('ctrl', 'shift', 'esc')
            elif "file explorer" in command: pyautogui.hotkey('win', 'e')
            elif "settings" in command: pyautogui.hotkey('win', 'i')
            elif "run dialog" in command: pyautogui.hotkey('win', 'r')
            elif "clipboard" in command: pyautogui.hotkey('win', 'v')
            elif "emoji" in command: pyautogui.hotkey('win', '.')
            elif "control panel" in command: 
                pyautogui.hotkey('win', 'r'); time.sleep(0.5); pyautogui.write('control'); pyautogui.press('enter')

            # --- Accessibility Tools ---
            elif "magnifier" in command: pyautogui.hotkey('win', 'plus')
            elif "narrator" in command: pyautogui.hotkey('win', 'ctrl', 'enter')
            elif "keyboard" in command and "screen" in command: pyautogui.hotkey('win', 'ctrl', 'o')
            
            # --- Hardware ---
            elif "brightness" in command: pyautogui.press('f3') # Generic fallback
            elif "fullscreen" in command: pyautogui.press('f11')

            # --- Folders ---
            elif "downloads folder" in command: os.startfile(os.path.join(os.environ['USERPROFILE'], 'Downloads'))
            elif "documents folder" in command: os.startfile(os.path.join(os.environ['USERPROFILE'], 'Documents'))
            elif "pictures folder" in command: os.startfile(os.path.join(os.environ['USERPROFILE'], 'Pictures'))
            elif "music folder" in command: os.startfile(os.path.join(os.environ['USERPROFILE'], 'Music'))
            elif "videos folder" in command: os.startfile(os.path.join(os.environ['USERPROFILE'], 'Videos'))
            elif "recycle bin" in command: os.system("start shell:RecycleBinFolder")

            return "Action performed."

        except Exception as e:
            return f"Error executing action: {e}"