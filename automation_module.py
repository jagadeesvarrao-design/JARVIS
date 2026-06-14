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
                os.system(f'taskkill /f /im "{app_name}.exe"')
                return f"Terminated {app_name}"
            except:
                return f"Could not find a running app named {app_name}."

    # =================================================================
    # 2. SMART MUSIC & TYPING (Upgraded)
    # =================================================================
    def play_music(self, command):
        """
        Searches YouTube programmatically for the song/video, applies smart query refinement
        rules, retrieves the top video URL, and launches it directly in Microsoft Edge App Mode.
        """
        import urllib.request
        import urllib.parse
        import re
        import os
        import time
        import json

        def parse_published_to_days(published_text):
            if not published_text:
                return 99999
            published_text = published_text.lower()
            # Match strings like "3 weeks ago", "1 day ago", "10 hours ago", etc.
            match = re.search(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', published_text)
            if not match:
                return 99999
            val = int(match.group(1))
            unit = match.group(2)
            if "second" in unit:
                return val / (24.0 * 3600.0)
            elif "minute" in unit:
                return val / 1440.0
            elif "hour" in unit:
                return val / 24.0
            elif "day" in unit:
                return val
            elif "week" in unit:
                return val * 7
            elif "month" in unit:
                return val * 30
            elif "year" in unit:
                return val * 365
            return 99999

        def parse_views_to_number(view_text):
            if not view_text:
                return 0
            # e.g., "217,649,287 views" or "169K views" or "1.5M views"
            view_text = view_text.lower().replace(',', '').replace('views', '').strip()
            match = re.search(r'([\d\.]+)\s*([kmb]?)', view_text)
            if not match:
                return 0
            val = float(match.group(1))
            multiplier = match.group(2)
            if multiplier == 'k':
                return int(val * 1000)
            elif multiplier == 'm':
                return int(val * 1000000)
            elif multiplier == 'b':
                return int(val * 100000000)
            return int(val)

        # Clean the input command
        song = command.lower().strip()
        # Remove prefixes like "play", "search for", "search", etc.
        song = re.sub(r'^(play|search\s+for|search|please\s+play|please|jarvis\s+play|jarvis)\s+', '', song)
        # Remove suffixes like "on youtube", "in youtube", "on yt", "youtube", "yt"
        song = re.sub(r'\s+(on\s+youtube|in\s+youtube|on\s+yt|youtube|yt)$', '', song)
        song = song.strip()
        
        if not song: 
            return "What should I play, Sir?"

        # --- SMART QUERY REFINEMENT RULES ---
        is_sad_songs = False
        is_general_lang_songs = False
        search_query = song

        # Common languages list to identify language-specific queries
        languages = [
            'telugu', 'hindi', 'english', 'tamil', 'kannada', 'malayalam', 
            'punjabi', 'bhojpuri', 'bengali', 'marathi', 'gujarati', 'urdu', 
            'spanish', 'korean', 'japanese'
        ]

        # Rule 1 & 2 checking
        if re.search(r'\bsad\s+songs?\b', song):
            is_sad_songs = True
            search_query = song
            print(f"🎵 Rule 2 applied: Sad songs search. Query: '{search_query}'")
        elif "song" in song or "songs" in song or "music" in song:
            lang = next((l for l in languages if l in song), None)
            if lang:
                is_general_lang_songs = True
                search_query = f"latest new release {lang} songs"
            else:
                # E.g. "play songs", "play some music"
                cleaned_words = [w for w in song.split() if w not in ["some", "a", "any", "kind", "of"]]
                cleaned_phrase = " ".join(cleaned_words)
                if cleaned_phrase in ["songs", "song", "music"]:
                    is_general_lang_songs = True
                    search_query = "latest new release songs"
                else:
                    search_query = song
            print(f"🎵 Rule 1 applied: General/Language song search. Query: '{search_query}'")
        else:
            # Rule 3: Specific song name query
            search_query = song
            print(f"🎵 Rule 3 applied: Specific song search. Query: '{search_query}'")

        # Programmatic YouTube lookup using ytInitialData JSON
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
                
            # Extract ytInitialData
            match = re.search(r"var ytInitialData = (\{.*?\});", html)
            if not match:
                match = re.search(r"window\['ytInitialData'\] = (\{.*?\});", html)
                
            if match:
                data = json.loads(match.group(1))
                
                # Recursive finder for videoRenderer
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
            print(f"⚠️ Programmatic YouTube lookup failed: {e}")

        # Process found videos
        selected_video_id = None
        parsed_videos = []
        
        if videos:
            for video in videos:
                video_id = video.get('videoId')
                if not video_id:
                    continue
                title = video.get('title', {}).get('runs', [{}])[0].get('text', 'No Title')
                
                view_text = video.get('viewCountText', {}).get('simpleText', '')
                if not view_text:
                    view_text = video.get('viewCountText', {}).get('runs', [{}])[0].get('text', '')
                views = parse_views_to_number(view_text)
                
                published_text = video.get('publishedTimeText', {}).get('simpleText', '')
                age_days = parse_published_to_days(published_text)
                
                parsed_videos.append({
                    'id': video_id,
                    'title': title,
                    'views': views,
                    'age_days': age_days,
                    'published': published_text,
                    'view_text': view_text
                })

        # Apply sorting/selection logic based on request type
        if parsed_videos:
            if is_sad_songs:
                # Sort by views descending (most views first)
                parsed_videos.sort(key=lambda x: x['views'], reverse=True)
                selected_video_id = parsed_videos[0]['id']
                print(f"🎯 Selected (Sad Song - Most Views): '{parsed_videos[0]['title']}' with {parsed_videos[0]['view_text']}")
            elif is_general_lang_songs:
                # Sort by age_days ascending (most recently released first)
                parsed_videos.sort(key=lambda x: x['age_days'])
                selected_video_id = parsed_videos[0]['id']
                print(f"🎯 Selected (Language Song - Recently Released): '{parsed_videos[0]['title']}' published {parsed_videos[0]['published']}")
            else:
                # Specific song name -> take the first search result
                selected_video_id = parsed_videos[0]['id']
                print(f"🎯 Selected (Specific Song): '{parsed_videos[0]['title']}'")
                
            video_url = f"https://www.youtube.com/watch?v={selected_video_id}"

        # Fallback to regex if parsing fails or yields no videos
        if not video_url:
            print("Fallback to regex matching...")
            try:
                video_ids = re.findall(r"watch\?v=(\S{11})", html)
                if video_ids:
                    # Deduplicate and pick the first unique video ID
                    unique_ids = []
                    for vid in video_ids:
                        if vid not in unique_ids:
                            unique_ids.append(vid)
                    if unique_ids:
                        video_url = f"https://www.youtube.com/watch?v={unique_ids[0]}"
            except Exception as re_err:
                print(f"⚠️ Fallback regex matching failed: {re_err}")

        # Launch the video
        if video_url:
            print(f"🎯 Playing video URL: {video_url}")
            os.system(f'start msedge --app="{video_url}"')
            return f"Playing song on YouTube: {song}"
        else:
            # Ultimate Fallback to search results page
            fallback_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
            os.system(f'start msedge --app="{fallback_url}"')
            return f"Opening YouTube search results for: {song}"

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