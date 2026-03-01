"""
adb.py — ADB Connection Layer for CoD AutoBot
Handles all BlueStacks communication: connect, screenshot, tap, swipe, key input
"""

import subprocess
import time
import random
import os
import threading
from typing import Optional, Tuple
import numpy as np

try:
    import cv2
    from PIL import Image
    import io
    ADB_IMPORTS_OK = True
except ImportError:
    ADB_IMPORTS_OK = False


class ADBController:
    def __init__(self, host: str = "127.0.0.1", port: int = 5555,
                 click_delay: float = 0.35, random_offset: int = 6,
                 log_callback=None):
        self.host = host
        self.port = port
        self.device = f"{host}:{port}"
        self.click_delay = click_delay
        self.random_offset = random_offset
        self.log = log_callback or print
        self.connected = False
        self._lock = threading.Lock()

    # ─────────────────────────── CONNECTION ───────────────────────────

    def connect(self) -> bool:
        """Connect to BlueStacks via ADB."""
        try:
            result = self._run(["adb", "connect", self.device])
            if "connected" in result.lower() or "already" in result.lower():
                self.connected = True
                self.log(f"[ADB] ✅ Connected to {self.device}")
                return True
            else:
                self.log(f"[ADB] ❌ Connection failed: {result}")
                self.connected = False
                return False
        except FileNotFoundError:
            self.log("[ADB] ❌ ADB not found. Install Android Platform Tools and add to PATH.")
            self.connected = False
            return False
        except Exception as e:
            self.log(f"[ADB] ❌ Error: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self._run(["adb", "disconnect", self.device])
        self.connected = False
        self.log(f"[ADB] Disconnected from {self.device}")

    def is_alive(self) -> bool:
        """Check if ADB connection is still active."""
        try:
            result = self._run(["adb", "-s", self.device, "shell", "echo", "ping"])
            return "ping" in result
        except:
            return False

    def reconnect(self) -> bool:
        self.log("[ADB] Attempting reconnect...")
        self.disconnect()
        time.sleep(2)
        return self.connect()

    # ─────────────────────────── SCREENSHOT ───────────────────────────

    def screenshot(self) -> Optional[np.ndarray]:
        """Capture screen from BlueStacks. Returns OpenCV BGR image or None."""
        with self._lock:
            try:
                result = subprocess.run(
                    ["adb", "-s", self.device, "exec-out", "screencap", "-p"],
                    capture_output=True, timeout=10
                )
                if result.returncode != 0:
                    return None
                img_array = np.frombuffer(result.stdout, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                return img
            except Exception as e:
                self.log(f"[ADB] Screenshot error: {e}")
                return None

    def screenshot_pil(self) -> Optional[Image.Image]:
        """Returns PIL Image version of screenshot."""
        img = self.screenshot()
        if img is None:
            return None
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def save_screenshot(self, path: str) -> bool:
        """Save screenshot to file."""
        img = self.screenshot()
        if img is None:
            return False
        cv2.imwrite(path, img)
        return True

    # ─────────────────────────── INPUT ───────────────────────────────

    def tap(self, x: int, y: int, human: bool = True):
        """Tap at coordinates with optional human-like randomness."""
        if human and self.random_offset > 0:
            x += random.randint(-self.random_offset, self.random_offset)
            y += random.randint(-self.random_offset, self.random_offset)
        self._run(["adb", "-s", self.device, "shell", "input", "tap", str(x), str(y)])
        if human:
            delay = self.click_delay + random.uniform(-0.05, 0.15)
            time.sleep(max(0.1, delay))

    def tap_region(self, x1: int, y1: int, x2: int, y2: int):
        """Tap a random point within a rectangular region."""
        x = random.randint(x1, x2)
        y = random.randint(y1, y2)
        self.tap(x, y)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        """Swipe from point A to point B."""
        self._run(["adb", "-s", self.device, "shell", "input", "swipe",
                   str(x1), str(y1), str(x2), str(y2), str(duration_ms)])
        time.sleep(0.3)

    def swipe_up(self, amount: int = 400):
        self.swipe(540, 700, 540, 700 - amount)

    def swipe_down(self, amount: int = 400):
        self.swipe(540, 400, 540, 400 + amount)

    def key(self, keycode: int):
        """Send keycode (e.g. 4 = back, 3 = home)."""
        self._run(["adb", "-s", self.device, "shell", "input", "keyevent", str(keycode)])
        time.sleep(0.2)

    def press_back(self):
        self.key(4)

    def press_home(self):
        self.key(3)

    # ─────────────────────────── INTERNAL ────────────────────────────

    def _run(self, cmd: list, timeout: int = 15) -> str:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=timeout)
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "timeout"
        except Exception as e:
            return str(e)
