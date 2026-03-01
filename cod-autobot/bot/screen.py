"""
screen.py — Screen Detection Engine for CoD AutoBot
Uses OpenCV template matching to find buttons, icons, and UI elements on screen.
"""

import os
import time
import numpy as np
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False


@dataclass
class Match:
    """Represents a found UI element on screen."""
    name: str
    x: int          # center x
    y: int          # center y
    confidence: float
    w: int
    h: int

    def center(self) -> Tuple[int, int]:
        return (self.x, self.y)


class ScreenDetector:
    def __init__(self, templates_dir: str = "templates",
                 threshold: float = 0.85,
                 log_callback=None):
        self.templates_dir = templates_dir
        self.threshold = threshold
        self.log = log_callback or print
        self._templates: Dict[str, np.ndarray] = {}
        self._load_templates()

    # ─────────────────────────── TEMPLATES ───────────────────────────

    def _load_templates(self):
        """Load all PNG templates from templates directory."""
        if not os.path.isdir(self.templates_dir):
            self.log(f"[Screen] Templates dir not found: {self.templates_dir}")
            return
        for fname in os.listdir(self.templates_dir):
            if fname.endswith(".png"):
                name = fname.replace(".png", "")
                path = os.path.join(self.templates_dir, fname)
                img = cv2.imread(path, cv2.IMREAD_COLOR)
                if img is not None:
                    self._templates[name] = img
        self.log(f"[Screen] Loaded {len(self._templates)} templates")

    def reload_templates(self):
        self._templates.clear()
        self._load_templates()

    def add_template(self, name: str, image: np.ndarray):
        """Add a template programmatically (e.g. captured from screen)."""
        self._templates[name] = image

    # ─────────────────────────── MATCHING ────────────────────────────

    def find(self, screen: np.ndarray, template_name: str,
             threshold: float = None) -> Optional[Match]:
        """Find a single template on screen. Returns best match or None."""
        if not CV2_OK:
            return None
        thresh = threshold or self.threshold
        tpl = self._templates.get(template_name)
        if tpl is None:
            return None

        result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= thresh:
            h, w = tpl.shape[:2]
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2
            return Match(name=template_name, x=cx, y=cy,
                        confidence=float(max_val), w=w, h=h)
        return None

    def find_all(self, screen: np.ndarray, template_name: str,
                 threshold: float = None) -> List[Match]:
        """Find all occurrences of a template on screen."""
        if not CV2_OK:
            return []
        thresh = threshold or self.threshold
        tpl = self._templates.get(template_name)
        if tpl is None:
            return []

        result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= thresh)
        h, w = tpl.shape[:2]
        matches = []

        for pt in zip(*locations[::-1]):
            cx = pt[0] + w // 2
            cy = pt[1] + h // 2
            conf = float(result[pt[1], pt[0]])
            matches.append(Match(template_name, cx, cy, conf, w, h))

        # Non-max suppression — deduplicate nearby matches
        return self._nms(matches, overlap=0.5)

    def find_any(self, screen: np.ndarray, names: List[str],
                 threshold: float = None) -> Optional[Match]:
        """Find the first matching template from a list of names."""
        for name in names:
            m = self.find(screen, name, threshold)
            if m:
                return m
        return None

    def exists(self, screen: np.ndarray, template_name: str,
               threshold: float = None) -> bool:
        return self.find(screen, template_name, threshold) is not None

    # ─────────────────────────── COLOR DETECTION ─────────────────────

    def find_color_region(self, screen: np.ndarray,
                          lower_hsv: tuple, upper_hsv: tuple,
                          min_area: int = 500) -> Optional[Tuple[int,int]]:
        """Find a colored region by HSV range. Returns center or None."""
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            if cv2.contourArea(c) >= min_area:
                M = cv2.moments(c)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)
        return None

    # ─────────────────────────── SCREEN STATE ────────────────────────

    def detect_screen_state(self, screen: np.ndarray) -> str:
        """
        Identify which game screen is currently shown.
        Returns a string like 'city', 'map', 'research', 'battle', etc.
        """
        # Map view detection (green terrain visible)
        GREEN_LOWER = (35, 40, 40)
        GREEN_UPPER = (85, 255, 255)
        green = self.find_color_region(screen, GREEN_LOWER, GREEN_UPPER, 50000)
        if green:
            return "map"

        # Check for known screen-specific templates
        state_templates = {
            "city":     ["city_hall_btn", "barracks_icon", "city_bg"],
            "research": ["research_title", "college_icon"],
            "battle":   ["battle_result", "victory_text", "defeat_text"],
            "march":    ["march_btn", "dispatch_btn"],
            "goblin":   ["goblin_title", "goblin_merchant"],
            "quest":    ["quest_title", "daily_quest"],
            "alliance": ["alliance_tab", "alliance_title"],
        }
        for state, templates in state_templates.items():
            for tpl in templates:
                if tpl in self._templates and self.exists(screen, tpl):
                    return state

        return "unknown"

    # ─────────────────────────── OCR REGION ──────────────────────────

    def crop_region(self, screen: np.ndarray,
                    x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        """Crop a region from the screen for further processing."""
        return screen[y1:y2, x1:x2]

    def debug_save(self, screen: np.ndarray, match: Match, path: str):
        """Save debug image with match rectangle drawn."""
        debug = screen.copy()
        x1 = match.x - match.w // 2
        y1 = match.y - match.h // 2
        x2 = match.x + match.w // 2
        y2 = match.y + match.h // 2
        cv2.rectangle(debug, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(debug, f"{match.name} {match.confidence:.2f}",
                   (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
        cv2.imwrite(path, debug)

    # ─────────────────────────── UTILS ───────────────────────────────

    def _nms(self, matches: List[Match], overlap: float) -> List[Match]:
        """Non-maximum suppression to remove duplicate detections."""
        if not matches:
            return []
        matches.sort(key=lambda m: m.confidence, reverse=True)
        kept = []
        for m in matches:
            too_close = False
            for k in kept:
                dx = abs(m.x - k.x)
                dy = abs(m.y - k.y)
                if dx < m.w * overlap and dy < m.h * overlap:
                    too_close = True
                    break
            if not too_close:
                kept.append(m)
        return kept
