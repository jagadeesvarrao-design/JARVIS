import os
import re
import time
import subprocess
import xml.etree.ElementTree as ET

def get_triggers():
    return [
        r"\b(?:mobile|phone) connect\b",
        r"\b(?:mobile|phone) open\b",
        r"\b(?:mobile|phone) click\b",
        r"\b(?:mobile|phone) text\b",
        r"\b(?:mobile|phone) key\b",
        r"\b(?:mobile|phone) swipe\b",
        r"\b(?:mobile|phone) screenshot\b"
    ]

def _find_adb():
    # Common ADB locations
    userprofile = os.environ.get('USERPROFILE', 'C:\\Users\\DELL')
    common_paths = [
        "adb",  # Assuming in PATH
        os.path.join(userprofile, "AppData\\Local\\Arduino15\\packages\\arduino\\tools\\adb\\32.0.0\\adb.exe"),
        os.path.join(userprofile, "AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"),
        os.path.join(userprofile, "AppData\\Local\\Programs\\Android\\Sdk\\platform-tools\\adb.exe"),
        "C:\\Android\\platform-tools\\adb.exe"
    ]
    for p in common_paths:
        if p == "adb":
            # Check if adb is globally available
            try:
                subprocess.run(["adb", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "adb"
            except FileNotFoundError:
                continue
        elif os.path.exists(p):
            return p
    return "adb"  # Default fallback

def _run_adb(args):
    adb_bin = _find_adb()
    try:
        res = subprocess.run([adb_bin] + args, capture_output=True, text=True, timeout=10)
        return res.returncode == 0, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout expired"
    except Exception as e:
        return False, "", str(e)

def execute(jarvis_instance, text, original_text, match=None):
    text = text.lower()
    
    # 1. CONNECT Command
    if "connect" in text:
        # Extract IP and Port if provided, e.g. "mobile connect 192.168.1.15:5555"
        ip_match = re.search(r'connect\s+([\d\.]+:\d+|[\d\.]+)', text)
        if ip_match:
            target = ip_match.group(1)
            # Default to port 5555 if only IP is provided
            if ":" not in target:
                target += ":5555"
            jarvis_instance._respond(f"Connecting wirelessly to {target}...")
            ok, out, err = _run_adb(["connect", target])
            if ok and "connected to" in out.lower():
                jarvis_instance._respond(f"Successfully connected to mobile device at {target}.")
            else:
                jarvis_instance._respond(f"Failed to connect. Make sure Wireless Debugging is enabled on your phone. Error: {out or err}")
        else:
            jarvis_instance._respond("Please specify the mobile IP address and port to connect (e.g., 'mobile connect 192.168.1.15:5555').")
        return True

    # Check if any device is connected first
    ok, out, _ = _run_adb(["devices"])
    lines = [l for l in out.strip().split("\n") if l.endswith("device")]
    if not lines:
        jarvis_instance._respond("No mobile device is connected. Please connect wirelessly first.")
        return True

    # 2. OPEN App Command
    if "open" in text:
        app_match = re.search(r'open\s+(.*)', text)
        if app_match:
            app_name = app_match.group(1).strip()
            # Map common names to packages
            packages = {
                "chrome": "com.android.chrome",
                "whatsapp": "com.whatsapp",
                "youtube": "com.google.android.youtube",
                "camera": "com.oneplus.camera", # OnePlus specific
                "camera stock": "com.android.camera",
                "settings": "com.android.settings",
                "calculator": "com.oneplus.calculator",
                "spotify": "com.spotify.music"
            }
            package = packages.get(app_name)
            if not package:
                # Attempt to guess package or start monkey on it
                package = app_name
            
            jarvis_instance._respond(f"Launching {app_name} on your phone...")
            ok, out, err = _run_adb(["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"])
            if not ok:
                # Fallback to general launch
                ok, _, _ = _run_adb(["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", package])
            
            if ok:
                jarvis_instance._respond(f"{app_name.capitalize()} opened successfully.")
            else:
                jarvis_instance._respond(f"Could not open package '{package}' on device.")
        return True

    # 3. CLICK element Command
    if "click" in text:
        click_match = re.search(r'click\s+(.*)', text)
        if click_match:
            target_label = click_match.group(1).strip()
            jarvis_instance._respond(f"Scanning screen for '{target_label}'...")
            
            # Dump UI hierarchy
            ok, _, _ = _run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
            if not ok:
                jarvis_instance._respond("Failed to inspect layout tree.")
                return True
                
            # Pull XML to local PC temp folder
            local_xml = os.path.join(os.environ.get('TEMP', 'C:\\temp'), "window_dump.xml")
            ok, _, _ = _run_adb(["pull", "/sdcard/window_dump.xml", local_xml])
            if not ok:
                jarvis_instance._respond("Failed to pull layout tree to PC.")
                return True

            # Parse XML and locate element
            try:
                tree = ET.parse(local_xml)
                root = tree.getroot()
                found_coords = None
                
                # Recursive search helper
                def find_node(node):
                    nonlocal found_coords
                    if found_coords:
                        return
                    
                    text_val = node.attrib.get('text', '').lower()
                    desc_val = node.attrib.get('content-desc', '').lower()
                    
                    if target_label in text_val or target_label in desc_val:
                        bounds = node.attrib.get('bounds', '')
                        # Bounds format: "[x1,y1][x2,y2]"
                        coords = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                        if coords:
                            x = (int(coords.group(1)) + int(coords.group(3))) // 2
                            y = (int(coords.group(2)) + int(coords.group(4))) // 2
                            found_coords = (x, y)
                            return
                            
                    for child in node:
                        find_node(child)
                
                find_node(root)
                
                if found_coords:
                    x, y = found_coords
                    jarvis_instance._respond(f"Clicking on '{target_label}' at coordinates {x}, {y}...")
                    _run_adb(["shell", "input", "tap", str(x), str(y)])
                else:
                    jarvis_instance._respond(f"Could not find any element matching '{target_label}' on the screen.")
            except Exception as e:
                jarvis_instance._respond(f"Failed parsing XML structure: {e}")
            finally:
                try:
                    os.remove(local_xml)
                except:
                    pass
        return True

    # 4. TEXT Input Command
    if "text" in text:
        text_match = re.search(r'text\s+(.*)', text)
        if text_match:
            input_val = text_match.group(1).strip()
            # Escape spaces for ADB input
            escaped_val = input_val.replace(" ", "%s")
            jarvis_instance._respond(f"Typing '{input_val}' on mobile...")
            _run_adb(["shell", "input", "text", escaped_val])
        return True

    # 5. KEY Press Command
    if "key" in text:
        key_match = re.search(r'key\s+(.*)', text)
        if key_match:
            key_name = key_match.group(1).strip()
            keycodes = {
                "back": "4",
                "home": "3",
                "menu": "82",
                "power": "26",
                "enter": "66",
                "volume up": "24",
                "volume down": "25"
            }
            code = keycodes.get(key_name)
            if code:
                jarvis_instance._respond(f"Pressing {key_name} key...")
                _run_adb(["shell", "input", "keyevent", code])
            else:
                jarvis_instance._respond(f"Unsupported key event '{key_name}'.")
        return True

    # 6. SWIPE Gesture Command
    if "swipe" in text:
        dir_match = re.search(r'swipe\s+(.*)', text)
        if dir_match:
            direction = dir_match.group(1).strip()
            # Assuming standard 1080x1920 viewport
            gestures = {
                "up": ["540", "1500", "540", "500", "500"],
                "down": ["540", "500", "540", "1500", "500"],
                "left": ["900", "960", "200", "960", "500"],
                "right": ["200", "960", "900", "960", "500"]
            }
            coords = gestures.get(direction)
            if coords:
                jarvis_instance._respond(f"Swiping {direction}...")
                _run_adb(["shell", "input", "swipe"] + coords)
            else:
                jarvis_instance._respond("Unknown direction. Supported directions: up, down, left, right.")
        return True

    # 7. SCREENSHOT Command
    if "screenshot" in text:
        jarvis_instance._respond("Capturing mobile screen...")
        ok, _, _ = _run_adb(["shell", "screencap", "-p", "/sdcard/screen.png"])
        if ok:
            local_png = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users\\DELL'), "OneDrive\\Desktop\\mobile_screenshot.png")
            pull_ok, _, _ = _run_adb(["pull", "/sdcard/screen.png", local_png])
            if pull_ok:
                jarvis_instance._respond("Screenshot saved successfully to your Desktop.")
                try:
                    os.startfile(local_png)
                except:
                    pass
            else:
                jarvis_instance._respond("Failed to transfer screenshot file.")
        else:
            jarvis_instance._respond("Failed to capture screenshot.")
        return True

    return False
