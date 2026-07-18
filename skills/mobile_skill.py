import os
import re
import time
import subprocess
import threading
import xml.etree.ElementTree as ET

# ── CONFIG ──────────────────────────────────────────────────────────────────
# Default phone IP – update this whenever your phone gets a new IP on the LAN.
# The ADB port shown under  Settings → Developer Options → Wireless Debugging
# is your CONNECTION port (not the pairing port).
DEFAULT_PHONE_IP   = "192.168.1.10"
DEFAULT_PHONE_PORT = "41407"          # last known working port — update if it changes

ADB_PATH = os.path.join(
    os.environ.get("USERPROFILE", "C:\\Users\\DELL"),
    "AppData", "Local", "Arduino15", "packages", "arduino",
    "tools", "adb", "32.0.0", "adb.exe"
)

# State shared across calls
_last_connected_target: str | None = None    # remembers last successful target
_reconnect_lock = threading.Lock()


# ── TRIGGERS ─────────────────────────────────────────────────────────────────
def get_triggers():
    return [
        # explicit connect / reconnect
        r"\b(?:mobile|phone)\s+connect\b",
        r"\bconnect\s+(?:my\s+)?(?:mobile|phone)\b",
        r"\breconnect\s+(?:my\s+)?(?:mobile|phone)\b",
        r"\bconnect\s+(?:jarvis\s+(?:to\s+)?)?(?:mobile|phone)\b",
        r"\bjarvis\s+connect\s+(?:mobile|phone)\b",
        r"\bpair\s+(?:my\s+)?(?:mobile|phone)\b",
        # control commands (require existing connection)
        r"\b(?:mobile|phone)\s+open\b",
        r"\b(?:mobile|phone)\s+click\b",
        r"\b(?:mobile|phone)\s+text\b",
        r"\b(?:mobile|phone)\s+key\b",
        r"\b(?:mobile|phone)\s+swipe\b",
        r"\b(?:mobile|phone)\s+screenshot\b",
    ]


# ── HELPERS ──────────────────────────────────────────────────────────────────
def _find_adb() -> str:
    """Locate adb executable."""
    if os.path.exists(ADB_PATH):
        return ADB_PATH
    # Generic fallbacks
    fallbacks = [
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local",
                     "Android", "Sdk", "platform-tools", "adb.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local",
                     "Programs", "Android", "Sdk", "platform-tools", "adb.exe"),
        "C:\\Android\\platform-tools\\adb.exe",
    ]
    for p in fallbacks:
        if os.path.exists(p):
            return p
    return "adb"  # last-resort: hope it's on PATH


def _run_adb(args: list, timeout: int = 12):
    adb_bin = _find_adb()
    try:
        res = subprocess.run(
            [adb_bin] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def _toast(title: str, message: str, icon: str = "info"):
    """Show a Windows 10/11 toast notification (best-effort)."""
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast(
            title, message,
            icon_path=None, duration=6, threaded=True
        )
        return
    except Exception:
        pass
    # Fallback: PowerShell balloon-tip notification
    try:
        ps_cmd = (
            f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
            f"ContentType = WindowsRuntime] | Out-Null; "
            f"$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
            f"[Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
            f"$t.GetElementsByTagName('text')[0].AppendChild($t.CreateTextNode('{title}')); "
            f"$t.GetElementsByTagName('text')[1].AppendChild($t.CreateTextNode('{message}')); "
            f"$notif = [Windows.UI.Notifications.ToastNotification]::new($t); "
            f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('JARVIS').Show($notif)"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def _is_device_connected() -> bool:
    """Return True if at least one device shows as 'device' in adb devices."""
    ok, out, _ = _run_adb(["devices"])
    return any(line.endswith("device") for line in out.split("\n"))


# ── CORE: AUTO-RECONNECT ─────────────────────────────────────────────────────
def _auto_reconnect(jarvis_instance, target: str) -> bool:
    """
    Try adb connect <target>.
    Speaks and shows a toast for success or failure.
    Returns True on success.
    """
    global _last_connected_target

    jarvis_instance._respond(f"Attempting wireless connection to {target} ...")

    ok, out, err = _run_adb(["connect", target])
    output_lower = (out + err).lower()

    if ok and ("connected to" in output_lower or "already connected" in output_lower):
        msg = f"Connected to your mobile at {target}."
        jarvis_instance._respond(msg)
        _toast("✅ JARVIS – Mobile Connected", f"Successfully connected to {target}", "info")
        _last_connected_target = target
        return True
    elif "cannot connect" in output_lower or "connection refused" in output_lower:
        msg = (
            "Connection refused. Make sure Wireless Debugging is ON "
            "and both devices are on the same Wi-Fi."
        )
        jarvis_instance._respond(msg)
        _toast("❌ JARVIS – Connection Failed",
               f"Could not reach {target}. Check Wireless Debugging.", "warning")
        return False
    elif "failed to authenticate" in output_lower:
        msg = "Authentication failed. Please allow the RSA key popup on your phone screen."
        jarvis_instance._respond(msg)
        _toast("🔐 JARVIS – Auth Required", "Tap 'Allow' on your phone to approve.", "warning")
        return False
    else:
        detail = out or err or "Unknown error"
        msg = f"Failed to connect. Detail: {detail}"
        jarvis_instance._respond(msg)
        _toast("❌ JARVIS – Mobile Failed", detail[:120], "error")
        return False


# ── MAIN ENTRY POINT ─────────────────────────────────────────────────────────
def execute(jarvis_instance, text: str, original_text: str, match=None):
    global _last_connected_target
    text_l = text.lower()

    # ── 1. CONNECT / RECONNECT ────────────────────────────────────────────
    connect_keywords = {"connect", "reconnect", "pair"}
    if any(k in text_l for k in connect_keywords):

        # If already connected, say so and offer to skip
        if _is_device_connected():
            jarvis_instance._respond(
                "Your mobile is already connected, sir. No action needed."
            )
            _toast("📱 JARVIS – Already Connected",
                   "Mobile device is already online.", "info")
            return True

        # Try to extract IP:PORT from the spoken command
        ip_match = re.search(r'([\d\.]+:\d+)', text_l)
        if ip_match:
            target = ip_match.group(1)
        elif _last_connected_target:
            target = _last_connected_target
            jarvis_instance._respond(
                f"Reconnecting to last known address: {target}"
            )
        else:
            target = f"{DEFAULT_PHONE_IP}:{DEFAULT_PHONE_PORT}"
            jarvis_instance._respond(
                f"No address provided, sir. Trying default: {target}"
            )

        _auto_reconnect(jarvis_instance, target)
        return True

    # ── Device check before any control commands ──────────────────────────
    if not _is_device_connected():
        jarvis_instance._respond(
            "No mobile device is connected. Say 'connect my mobile' first."
        )
        return True

    # ── 2. OPEN APP ───────────────────────────────────────────────────────
    if "open" in text_l:
        app_match = re.search(r'open\s+(.*)', text_l)
        if app_match:
            app_name = app_match.group(1).strip()
            packages = {
                "chrome":        "com.android.chrome",
                "whatsapp":      "com.whatsapp",
                "youtube":       "com.google.android.youtube",
                "camera":        "com.oneplus.camera",
                "settings":      "com.android.settings",
                "calculator":    "com.oneplus.calculator",
                "spotify":       "com.spotify.music",
                "instagram":     "com.instagram.android",
                "maps":          "com.google.android.apps.maps",
                "gmail":         "com.google.android.gm",
                "clock":         "com.android.deskclock",
                "gallery":       "com.oneplus.gallery",
                "files":         "com.android.documentsui",
            }
            package = packages.get(app_name, app_name)
            jarvis_instance._respond(f"Launching {app_name} on your phone...")
            ok, out, err = _run_adb(
                ["shell", "monkey", "-p", package,
                 "-c", "android.intent.category.LAUNCHER", "1"]
            )
            if ok:
                jarvis_instance._respond(f"{app_name.capitalize()} opened.")
                _toast("📱 JARVIS", f"{app_name.capitalize()} opened on phone.", "info")
            else:
                jarvis_instance._respond(f"Could not open {app_name}.")
        return True

    # ── 3. CLICK ELEMENT ──────────────────────────────────────────────────
    if "click" in text_l:
        click_match = re.search(r'click\s+(.*)', text_l)
        if click_match:
            target_label = click_match.group(1).strip()
            jarvis_instance._respond(f"Scanning screen for '{target_label}'...")
            _run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
            local_xml = os.path.join(os.environ.get("TEMP", "C:\\temp"), "window_dump.xml")
            ok, _, _ = _run_adb(["pull", "/sdcard/window_dump.xml", local_xml])
            if not ok:
                jarvis_instance._respond("Failed to pull UI layout from phone.")
                return True
            try:
                root = ET.parse(local_xml).getroot()
                found = None
                def find_node(node):
                    nonlocal found
                    if found: return
                    tv = node.attrib.get("text", "").lower()
                    dv = node.attrib.get("content-desc", "").lower()
                    if target_label in tv or target_label in dv:
                        b = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',
                                     node.attrib.get("bounds", ""))
                        if b:
                            found = ((int(b.group(1))+int(b.group(3)))//2,
                                     (int(b.group(2))+int(b.group(4)))//2)
                    for c in node: find_node(c)
                find_node(root)
                if found:
                    jarvis_instance._respond(
                        f"Clicking '{target_label}' at {found[0]},{found[1]}."
                    )
                    _run_adb(["shell", "input", "tap", str(found[0]), str(found[1])])
                else:
                    jarvis_instance._respond(
                        f"Could not find '{target_label}' on the screen."
                    )
            except Exception as e:
                jarvis_instance._respond(f"XML parse error: {e}")
            finally:
                try: os.remove(local_xml)
                except: pass
        return True

    # ── 4. TYPE TEXT ──────────────────────────────────────────────────────
    if "text" in text_l:
        tm = re.search(r'text\s+(.*)', text_l)
        if tm:
            val = tm.group(1).strip().replace(" ", "%s")
            jarvis_instance._respond(f"Typing on mobile...")
            _run_adb(["shell", "input", "text", val])
        return True

    # ── 5. KEY PRESS ─────────────────────────────────────────────────────
    if "key" in text_l:
        km = re.search(r'key\s+(.*)', text_l)
        if km:
            key_name = km.group(1).strip()
            keycodes = {
                "back": "4", "home": "3", "menu": "82",
                "power": "26", "enter": "66",
                "volume up": "24", "volume down": "25",
                "mute": "164", "recent": "187",
            }
            code = keycodes.get(key_name)
            if code:
                jarvis_instance._respond(f"Pressing {key_name}...")
                _run_adb(["shell", "input", "keyevent", code])
            else:
                jarvis_instance._respond(f"Unknown key '{key_name}'.")
        return True

    # ── 6. SWIPE ─────────────────────────────────────────────────────────
    if "swipe" in text_l:
        dm = re.search(r'swipe\s+(.*)', text_l)
        if dm:
            direction = dm.group(1).strip()
            gestures = {
                "up":    ["540", "1500", "540",  "500", "400"],
                "down":  ["540",  "500", "540", "1500", "400"],
                "left":  ["900",  "960", "200",  "960", "400"],
                "right": ["200",  "960", "900",  "960", "400"],
            }
            coords = gestures.get(direction)
            if coords:
                jarvis_instance._respond(f"Swiping {direction}...")
                _run_adb(["shell", "input", "swipe"] + coords)
            else:
                jarvis_instance._respond("Unknown direction. Use: up, down, left, right.")
        return True

    # ── 7. SCREENSHOT ────────────────────────────────────────────────────
    if "screenshot" in text_l:
        jarvis_instance._respond("Capturing your phone's screen...")
        ok, _, _ = _run_adb(["shell", "screencap", "-p", "/sdcard/jarvis_screen.png"])
        if ok:
            dest = os.path.join(
                os.environ.get("USERPROFILE", "C:\\Users\\DELL"),
                "OneDrive", "Desktop", "mobile_screenshot.png"
            )
            pull_ok, _, _ = _run_adb(["pull", "/sdcard/jarvis_screen.png", dest])
            if pull_ok:
                jarvis_instance._respond(
                    "Screenshot saved to your Desktop successfully."
                )
                _toast("📸 JARVIS – Screenshot", "Saved to Desktop.", "info")
                try: os.startfile(dest)
                except: pass
            else:
                jarvis_instance._respond("Failed to transfer the screenshot.")
        else:
            jarvis_instance._respond("Failed to capture screenshot on phone.")
        return True

    return False
