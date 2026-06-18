import os
import time

class VisionSystem:
    def __init__(self):
        self.last_frame = None
        print("👁️ Vision Core Loaded")

    def _gdi_capture(self):
        import win32gui
        import win32ui
        import win32con
        import win32api
        from PIL import Image

        # Grab a handle to the main desktop window
        hdesktop = win32gui.GetDesktopWindow()
        width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        
        # Create a compatible device context in memory
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        mem_dc = img_dc.CreateCompatibleDC()
        
        # Create compatible bitmap and select it into memory DC
        screenshot = win32ui.CreateBitmap()
        screenshot.CreateCompatibleBitmap(img_dc, width, height)
        mem_dc.SelectObject(screenshot)
        
        # BitBlt copies screen block to memory device context
        mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)
        
        # Get raw bitmap bits and format as BGRX image
        bmpinfo = screenshot.GetInfo()
        bmpstr = screenshot.GetBitmapBits(True)
        
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        # Clean up Win32 GDI handles to prevent GDI resource leaks
        mem_dc.DeleteDC()
        win32gui.DeleteObject(screenshot.GetHandle())
        win32gui.ReleaseDC(hdesktop, desktop_dc)
        return img

    def capture_image(self):
        """Original manual capture for specific commands."""
        try:
            img = self.capture_screen_to_memory()
            path = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop', 'temp_vision.png')
            if img:
                img.save(path)
                return path
        except Exception as e:
            print(f"Capture Image Error: {e}")
        return ""
        
    def capture_screen_to_memory(self):
        """Captures the screen instantly into RAM using native GDI."""
        try:
            return self._gdi_capture()
        except Exception as e:
            print(f"Memory Capture Error: {e}")
            return None
        
    def has_screen_changed(self, threshold=5000):
        """
        Detects if the screen has changed significantly using fast PIL downsampling.
        Returns True if changed, False if static.
        """
        from PIL import Image
        try:
            img = self.capture_screen_to_memory()
            if not img:
                return False
                
            # Downsample image to 160x90 and convert to L (grayscale)
            small_img = img.resize((160, 90), Image.Resampling.BILINEAR).convert('L')
            current_gray = list(small_img.getdata())
            
            if self.last_frame is None:
                self.last_frame = current_gray
                return True # First run counts as a change
                
            # Compute absolute differences and count non-zero changes
            non_zero_count = sum(1 for a, b in zip(self.last_frame, current_gray) if abs(a - b) > 30)
            
            # Update last_frame
            self.last_frame = current_gray
            
            # Scale threshold down to match 160x90 downsampled resolution
            scaled_threshold = max(1, threshold // 64)
            
            return non_zero_count > scaled_threshold
        except Exception as e:
            print(f"Screen Change Detection Error: {e}")
            return False