import pyautogui
import os
import time
import io
import mss
import cv2
import numpy as np
from PIL import Image

class VisionSystem:
    def __init__(self):
        print("👁️ Vision Core Loaded")
        # Initialize fast screen capture
        self.sct = mss.mss()
        self.last_frame = None

    def capture_image(self):
        """Original manual capture for specific commands."""
        path = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', 'temp_vision.png')
        pyautogui.screenshot(path)
        return path
        
    def capture_screen_to_memory(self):
        """Captures the screen instantly into RAM (no file saving). Used for background looping."""
        try:
            # Grab the primary monitor
            monitor = self.sct.monitors[1] 
            sct_img = self.sct.grab(monitor)
            
            # Convert directly to PIL Image for the AI model
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            print(f"Memory Capture Error: {e}")
            return None
        
    def has_screen_changed(self, threshold=5000):
        """
        Detects if the screen has changed significantly.
        Returns True if changed, False if static.
        """
        current_frame = self.capture_screen_to_memory()
        if current_frame is None:
            return False
            
        # Convert to grayscale for efficient comparison
        frame_np = np.array(current_frame)
        current_gray = cv2.cvtColor(frame_np, cv2.COLOR_RGB2GRAY)
        
        if self.last_frame is None:
            self.last_frame = current_gray
            return True # First run counts as a change
            
        # Compute absolute difference
        diff = cv2.absdiff(self.last_frame, current_gray)
        # Count pixels that have changed beyond a small noise threshold
        non_zero_count = np.count_nonzero(diff > 30)
        
        # Update last_frame
        self.last_frame = current_gray
        
        # Only return True if changes are significant (e.g., > 5000 pixels)
        return non_zero_count > threshold