import os
import shutil
# --- PATH FINDER ---
def get_desktop_path():
    return os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop')

# --- GLOBAL SEARCH ---
def find_folder_globally(folder_name):
    folder_name = folder_name.lower() 
    user_path = os.environ['USERPROFILE']
    
    search_dirs = [
        get_desktop_path(),
        os.path.join(user_path, "Documents"),
        os.path.join(user_path, "Downloads"),
        os.path.join(user_path, "Pictures"),
        os.path.join(user_path, "Music"),
        os.path.join(user_path, "Videos")
    ]
    
    for root in search_dirs:
        if not os.path.exists(root): continue
        possible_path = os.path.join(root, folder_name) 
        if os.path.exists(possible_path): return possible_path

        try:
            for item in os.listdir(root):
                if item.lower() == folder_name and os.path.isdir(os.path.join(root, item)):
                    return os.path.join(root, item)
        except: pass
    
    return None

def get_triggers():
    return ["create folder", "create file", "open folder", "delete folder"]

def execute(jarvis_instance, text, original_text, match=None):
    if "create folder" in text:
        name = text.replace("create folder", "").strip()
        path = os.path.join(get_desktop_path(), name)
        if not os.path.exists(path):
            os.makedirs(path)
            jarvis_instance._respond(f"Created {name}.")
            os.startfile(path)
        else:
            jarvis_instance._respond(f"Folder {name} already exists.")
        return False

    if "create file" in text:
        if " inside " in text:
            parts = text.replace("create file", "").split(" inside ")
            file_name = parts[0].strip()
            folder_name = parts[1].strip()
            folder_path = find_folder_globally(folder_name)
            if folder_path:
                full_path = os.path.join(folder_path, f"{file_name}.txt")
                with open(full_path, "w") as f: 
                    f.write("")
                jarvis_instance._respond(f"Created {file_name} inside {folder_name}.")
                os.startfile(full_path)
            else: 
                jarvis_instance._respond(f"Folder {folder_name} not found.")
        else:
            name = text.replace("create file", "").strip()
            path = os.path.join(get_desktop_path(), f"{name}.txt")
            with open(path, "w") as f: 
                f.write("")
            jarvis_instance._respond(f"Created {name}.")
            os.startfile(path)
        return False

    if "open folder" in text:
        name = text.replace("open folder", "").strip()
        path = find_folder_globally(name)
        if path:
            jarvis_instance._respond("Opening.")
            os.startfile(path)
        else: 
            jarvis_instance._respond("Not found.")
        return False

    if "delete folder" in text:
        name = text.replace("delete folder", "").strip()
        path = os.path.join(get_desktop_path(), name)
        if os.path.exists(path):
            jarvis_instance._respond(f"Delete {name}?")
            confirm = jarvis_instance._force_listen(retries=2) or ""
            if any(w in confirm.lower() for w in ["yes", "delete", "sure"]):
                try:
                    def on_rm_error(func, path, exc_info):
                        os.chmod(path, 128)
                        os.unlink(path)
                    shutil.rmtree(path, onerror=on_rm_error)
                    jarvis_instance._respond("Deleted.")
                except: 
                    jarvis_instance._respond("Could not delete.")
        else:
            jarvis_instance._respond(f"Folder {name} does not exist.")
        return False

    return None
