import os
import time
import ctypes

# Lazy loaded win32 libraries
win32gui = None
win32con = None
win32process = None
win32com_client = None

def _lazy_win32():
    global win32gui, win32con, win32process, win32com_client
    if win32gui is None:
        import win32gui
        import win32con
        import win32process
        import win32com.client as win32com_client

class ApplicationController:
    def __init__(self):
        print("🛠️ Automation Module Loaded")

    # =================================================================
    # 🔍 WINDOW SENSOR (Optimized using Win32 API)
    # =================================================================
    def get_active_window_title(self):
        """Reads the title of the window you are currently using"""
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value.lower()

    def get_open_windows(self):
        """Returns titles of all currently open and visible windows using native Win32 API"""
        _lazy_win32()
        try:
            titles = []
            def enum_windows_callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and len(title.strip()) > 0:
                        if title not in titles:
                            titles.append(title)
            win32gui.EnumWindows(enum_windows_callback, None)
            return titles
        except Exception as e:
            print(f"Error listing windows: {e}")
            return []

    def activate_window(self, app_name):
        """Locates an open window by name and brings it to the foreground"""
        _lazy_win32()
        print(f"🔍 Searching for window matching: '{app_name}'")
        try:
            found_hwnds = []
            def enum_windows_callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if app_name.lower() in title.lower():
                        found_hwnds.append((hwnd, title))
            
            win32gui.EnumWindows(enum_windows_callback, None)
            
            if found_hwnds:
                hwnd, title = found_hwnds[0]
                print(f"🎯 Found window: '{title}'. Activating...")
                
                # If minimized, restore it
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    
                # Bring to foreground (ALT toggle workaround for Windows focus lock)
                shell = win32com_client.Dispatch("WScript.Shell")
                shell.SendKeys('%') 
                win32gui.SetForegroundWindow(hwnd)
                return f"Activated window '{title}'."
            return f"Could not find any open window matching '{app_name}'."
        except Exception as e:
            return f"Error activating window: {e}"

    def close_window_gracefully(self, app_name):
        """Locates an open window by name and closes it gracefully"""
        _lazy_win32()
        print(f"❌ Closing window matching: '{app_name}'")
        try:
            found_hwnds = []
            def enum_windows_callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if app_name.lower() in title.lower():
                        found_hwnds.append((hwnd, title))
                        
            win32gui.EnumWindows(enum_windows_callback, None)
            
            if found_hwnds:
                hwnd, title = found_hwnds[0]
                print(f"🎯 Closing window: '{title}'")
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return f"Closed window '{title}' gracefully."
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
            os.system("start msedge --app=https://www.youtube.com")
            return "Opening YouTube App."

        # 1. Custom Browser Fixes
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
            # 3. Fallback to Windows Search
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(app_name)
            time.sleep(0.5)
            pyautogui.press('enter')
            return f"Attempting to launch {app_name}."

    def close_app(self, command):
        """Smart Closing: Distinguishes between Browser Tabs and Apps"""
        import pyautogui
        app_name = command.replace("close", "").strip().lower()
        print(f"❌ Closing: {app_name}")

        # 1. BROWSER TABS
        browser_keywords = ["youtube", "google", "tab", "browser", "search", "gmail", "whatsapp"]
        if any(word in app_name for word in browser_keywords):
            pyautogui.hotkey('ctrl', 'w')
            return f"Closed tab for {app_name}."

        # 2. Try native close
        res = self.close_window_gracefully(app_name)
        if "Closed window" in res:
            return res

        # 3. SYSTEM APPS
        if "code" in app_name or "visual studio" in app_name:
            os.system("taskkill /f /im Code.exe")
            return "Closed VS Code."
            
        try:
            from AppOpener import close as app_closer
            app_closer(app_name, match_closest=True, throw_error=True)
            return f"Closed {app_name}."
        except:
            try:
                os.system(f'taskkill /f /im "{app_name}.exe"')
                return f"Terminated {app_name}"
            except:
                return f"Could not find a running app named {app_name}."

    # =================================================================
    # 2. SMART MUSIC & TYPING
    # =================================================================
    def play_music(self, command):
        import urllib.request
        import urllib.parse
        import re
        import json

        def parse_published_to_days(published_text):
            if not published_text:
                return 99999
            published_text = published_text.lower()
            match = re.search(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', published_text)
            if not match:
                return 99999
            val = int(match.group(1))
            unit = match.group(2)
            if "second" in unit: return val / (24.0 * 3600.0)
            elif "minute" in unit: return val / 1440.0
            elif "hour" in unit: return val / 24.0
            elif "day" in unit: return val
            elif "week" in unit: return val * 7
            elif "month" in unit: return val * 30
            elif "year" in unit: return val * 365
            return 99999

        def parse_views_to_number(view_text):
            if not view_text: return 0
            view_text = view_text.lower().replace(',', '').replace('views', '').strip()
            match = re.search(r'([\d\.]+)\s*([kmb]?)', view_text)
            if not match: return 0
            val = float(match.group(1))
            multiplier = match.group(2)
            if multiplier == 'k': return int(val * 1000)
            elif multiplier == 'm': return int(val * 1000000)
            elif multiplier == 'b': return int(val * 100000000)
            return int(val)

        song = command.lower().strip()
        song = re.sub(r'^(play|search\s+for|search|please\s+play|please|jarvis\s+play|jarvis)\s+', '', song)
        song = re.sub(r'\s+(on\s+youtube|in\s+youtube|on\s+yt|youtube|yt)$', '', song)
        song = song.strip()
        
        if not song: 
            return "What should I play, Sir?"

        is_sad_songs = False
        is_general_lang_songs = False
        search_query = song

        languages = [
            'telugu', 'hindi', 'english', 'tamil', 'kannada', 'malayalam', 
            'punjabi', 'bhojpuri', 'bengali', 'marathi', 'gujarati', 'urdu', 
            'spanish', 'korean', 'japanese'
        ]

        if re.search(r'\bsad\s+songs?\b', song):
            is_sad_songs = True
            search_query = song
        elif "song" in song or "songs" in song or "music" in song:
            lang = next((l for l in languages if l in song), None)
            if lang:
                is_general_lang_songs = True
                search_query = f"latest new release {lang} songs"
            else:
                cleaned_words = [w for w in song.split() if w not in ["some", "a", "any", "kind", "of"]]
                cleaned_phrase = " ".join(cleaned_words)
                if cleaned_phrase in ["songs", "song", "music"]:
                    is_general_lang_songs = True
                    search_query = "latest new release songs"
                else:
                    search_query = song
        else:
            search_query = song

        video_url = None
        html = ""
        videos = []
        try:
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            
            req = urllib.request.Request(
                search_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            match = re.search(r"var ytInitialData = (\{.*?\});", html)
            if not match:
                match = re.search(r"window\['ytInitialData'\] = (\{.*?\});", html)
                
            if match:
                data = json.loads(match.group(1))
                
                def find_videos(obj):
                    res_vids = []
                    if isinstance(obj, dict):
                        if 'videoRenderer' in obj:
                            res_vids.append(obj['videoRenderer'])
                        for k, v in obj.items():
                            res_vids.extend(find_videos(v))
                    elif isinstance(obj, list):
                        for item in obj:
                            res_vids.extend(find_videos(item))
                    return res_vids
                
                videos = find_videos(data)
        except Exception as e:
            print(f"⚠️ YouTube lookup failed: {e}")

        selected_video_id = None
        parsed_videos = []
        
        if videos:
            for video in videos:
                video_id = video.get('videoId')
                if not video_id: continue
                title = video.get('title', {}).get('runs', [{}])[0].get('text', 'No Title')
                view_text = video.get('viewCountText', {}).get('simpleText', '')
                if not view_text:
                    view_text = video.get('viewCountText', {}).get('runs', [{}])[0].get('text', '')
                views = parse_views_to_number(view_text)
                published_text = video.get('publishedTimeText', {}).get('simpleText', '')
                age_days = parse_published_to_days(published_text)
                
                parsed_videos.append({
                    'id': video_id, 'title': title, 'views': views,
                    'age_days': age_days, 'published': published_text, 'view_text': view_text
                })

        if parsed_videos:
            if is_sad_songs:
                parsed_videos.sort(key=lambda x: x['views'], reverse=True)
                selected_video_id = parsed_videos[0]['id']
            elif is_general_lang_songs:
                parsed_videos.sort(key=lambda x: x['age_days'])
                selected_video_id = parsed_videos[0]['id']
            else:
                selected_video_id = parsed_videos[0]['id']
            video_url = f"https://www.youtube.com/watch?v={selected_video_id}"

        if not video_url:
            try:
                video_ids = re.findall(r"watch\?v=(\S{11})", html)
                if video_ids:
                    unique_ids = []
                    for vid in video_ids:
                        if vid not in unique_ids: unique_ids.append(vid)
                    if unique_ids:
                        video_url = f"https://www.youtube.com/watch?v={unique_ids[0]}"
            except Exception as re_err:
                print(f"⚠️ Fallback regex failed: {re_err}")

        if video_url:
            os.system(f'start msedge --app="{video_url}"')
            return f"Playing song on YouTube: {song}"
        else:
            fallback_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
            os.system(f'start msedge --app="{fallback_url}"')
            return f"Opening YouTube search results for: {song}"

    def type_text(self, text):
        import pyautogui
        clean_text = text.replace("write", "").replace("type", "").strip()
        time.sleep(1.0)
        try:
            from pywinauto.keyboard import send_keys
            escaped_text = ""
            for char in clean_text:
                if char == '{': escaped_text += '{{}'
                elif char == '}': escaped_text += '{}}'
                else: escaped_text += char
            send_keys(escaped_text, with_spaces=True)
            return "Typed using pywinauto."
        except Exception as e:
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
    # 4. MASTER SYSTEM AUTOMATION
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
            elif "minimise" in command: pyautogui.hotkey('win', 'd')
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

            # --- Screenshots ---
            elif "screenshot" in command:
                filename = f"screenshot_{int(time.time())}.png"
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
            elif "brightness" in command: pyautogui.press('f3')
            elif "fullscreen" in command: pyautogui.press('f11')

            # --- Media Controls ---
            elif "volume up" in command: 
                pyautogui.press("volumeup", presses=5)
                return "Volume increased."
            elif "volume down" in command: 
                pyautogui.press("volumedown", presses=5)
                return "Volume decreased."
            elif "mute" in command: 
                pyautogui.press("volumemute")
                return "Volume muted/unmuted."
            elif "play" in command or "pause" in command or "stop" in command: 
                pyautogui.press("playpause")
                return "Playback toggled."
            elif "next" in command: 
                pyautogui.press("nexttrack")
                return "Next track playing."
            elif "previous" in command: 
                pyautogui.press("prevtrack")
                return "Previous track playing."

            # --- App Launching ---
            elif "open notepad" in command or "notepad" in command: 
                os.system("start notepad")
                return "Notepad opened."
            elif "open calculator" in command or "calculator" in command: 
                os.system("start calc")
                return "Calculator opened."
            elif "open paint" in command or "paint" in command: 
                os.system("start mspaint")
                return "Paint opened."
            elif "open command prompt" in command or "open cmd" in command: 
                os.system("start cmd")
                return "Command Prompt opened."

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