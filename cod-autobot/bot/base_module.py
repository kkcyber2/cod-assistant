"""
base_module.py — Base class for all CoD AutoBot task modules
All automation modules (gather, fight, claim, etc.) inherit from this.
"""

import time
import random
import threading
from typing import Optional
from bot.adb import ADBController
from bot.screen import ScreenDetector


class BotModule:
    """Base class for all automation task modules."""

    def __init__(self, adb: ADBController, screen: ScreenDetector,
                 config: dict, log_callback=None):
        self.adb = adb
        self.screen = screen
        self.config = config
        self.log = log_callback or print
        self.enabled = False
        self.running = False
        self._stop_event = threading.Event()

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def stop(self):
        self._stop_event.set()
        self.running = False

    # ─────────────────────────── HELPERS ─────────────────────────────

    def wait(self, seconds: float, jitter: float = 0.2):
        """Sleep with optional random jitter for human-like timing."""
        actual = seconds + random.uniform(-jitter, jitter)
        time.sleep(max(0.05, actual))

    def tap_if_found(self, screen_img, template_name: str,
                     threshold: float = None) -> bool:
        """Find template and tap it if found. Returns True if tapped."""
        match = self.screen.find(screen_img, template_name, threshold)
        if match:
            self.adb.tap(match.x, match.y)
            self.log(f"[{self.__class__.__name__}] Tapped: {template_name} "
                    f"({match.x},{match.y}) conf={match.confidence:.2f}")
            return True
        return False

    def wait_for_screen(self, template_name: str,
                        timeout: float = 10.0,
                        interval: float = 0.5) -> bool:
        """Wait until a template appears on screen. Returns True if found."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            img = self.adb.screenshot()
            if img is not None and self.screen.exists(img, template_name):
                return True
            time.sleep(interval)
        self.log(f"[{self.__class__.__name__}] Timeout waiting for: {template_name}")
        return False

    def safe_screenshot(self):
        """Take screenshot with retry on failure."""
        for attempt in range(3):
            img = self.adb.screenshot()
            if img is not None:
                return img
            time.sleep(0.5)
        self.log(f"[{self.__class__.__name__}] ❌ Screenshot failed after 3 retries")
        return None

    def dismiss_popups(self, screen_img=None):
        """Dismiss common popups: OK, Close, X buttons."""
        if screen_img is None:
            screen_img = self.safe_screenshot()
        if screen_img is None:
            return
        for btn in ["popup_ok", "popup_close", "popup_x",
                    "confirm_btn", "cancel_warn"]:
            if self.tap_if_found(screen_img, btn):
                self.wait(0.5)
                break

    def go_to_city(self):
        """Navigate back to city view."""
        img = self.safe_screenshot()
        if img is None:
            return
        state = self.screen.detect_screen_state(img)
        if state == "city":
            return
        # Try back button first
        self.adb.press_back()
        self.wait(1.0)
        img = self.safe_screenshot()
        if img is None:
            return
        # Tap city button in map view
        self.tap_if_found(img, "city_btn")
        self.wait(1.5)

    def run_once(self):
        """Override in subclass — main logic for one execution cycle."""
        raise NotImplementedError
