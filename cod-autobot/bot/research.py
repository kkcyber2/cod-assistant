"""
research.py — Auto Research Module for CoD AutoBot
Manages the College of Order research queue following optimal CoD priority order.
Never leaves queue idle. Economy-first strategy, minimum Military for T4 unlock.
"""

import time
from bot.base_module import BotModule


class ResearchModule(BotModule):
    """
    Research Priority (in order):
    ECONOMY TREE:
      1. Architecture I & II       (+50% build speed — research FIRST)
      2. Scholarship I & II        (+25% research speed — ASAP)
      3. Stamina I & II            (+600 CP storage)
      4. Logging Techniques        (Wood boost)
      5. Forestry                  (Wood gather speed)
      6. Ore Prospecting           (Ore boost)
      7. Ore Smelting              (Ore gather speed)
      8. Gold Processing (x5)      (Mint production)
      9. Gold Mining (x5)          (Gold gather from map)
      10. Mana Prospering          (Unlock Mana gathering)
      11. Container Upgrade        (Bigger march load)

    MILITARY TREE (minimum path to T4 only):
      1. Conscription I & II       (+20% train speed — early)
      2. Military Leadership I     (+hero XP from Darklings)
      3. Intelligence Gathering 5/5 (T4 requirement)
      4. Pathfinding 2 to 7/10    (T4 requirement — stop at 7!)
      5. T4 troops (your type)    (Main power spike)

    RULE: Never max Military before finishing Economy.
    """

    RESEARCH_QUEUE = [
        # (tree, research_name, max_level, priority_note)
        ("economy",  "Architecture I",         1, "CRITICAL - build speed"),
        ("economy",  "Architecture II",        1, "CRITICAL - build speed"),
        ("economy",  "Scholarship I",          1, "CRITICAL - research speed"),
        ("economy",  "Scholarship II",         1, "CRITICAL - research speed"),
        ("military", "Conscription I",         1, "Train speed - do early"),
        ("military", "Conscription II",        1, "Train speed - do early"),
        ("military", "Military Leadership I",  1, "Hero XP boost from Darklings"),
        ("economy",  "Stamina I",              1, "CP storage"),
        ("economy",  "Stamina II",             1, "CP storage"),
        ("economy",  "Logging Techniques",     5, "Wood production"),
        ("economy",  "Forestry",               5, "Wood gather speed"),
        ("economy",  "Ore Prospecting",        5, "Ore production"),
        ("economy",  "Ore Smelting",           5, "Ore gather speed"),
        ("economy",  "Gold Processing",        5, "Mint Gold production"),
        ("economy",  "Gold Mining",            5, "Gold gather from map"),
        ("economy",  "Mana Prospering",        1, "Unlock Mana gathering"),
        ("economy",  "Container Upgrade",      5, "March load capacity"),
        ("military", "Intelligence Gathering", 5, "T4 path REQUIRED - max to 5"),
        ("military", "Pathfinding 2",          7, "T4 path - STOP at 7/10"),
        ("military", "T4 Infantry",            1, "T4 unlock - power spike!"),
        ("military", "T4 Mounted",             1, "T4 unlock"),
        ("military", "T4 Marksmen",            1, "T4 unlock"),
        ("military", "T4 Magic",               1, "T4 unlock"),
        # After T4 — go back and max everything
        ("economy",  "Supply Chain I",         5, "Late game economy"),
        ("economy",  "Supply Chain II",        5, "Late game economy"),
        ("military", "Military Leadership II", 1, "More hero XP"),
        ("military", "T4 Flying",              1, "LAST - needs all other T4"),
    ]

    def __init__(self, adb, screen, config, log_callback=None):
        super().__init__(adb, screen, config, log_callback)
        self.research_focus = config.get("research_focus", "economy_first")
        self.use_second_queue = config.get("research_second_queue", True)
        self.wait_for_helps = config.get("research_wait_helps", True)
        self._queue_index = 0        # current position in RESEARCH_QUEUE
        self._queue2_index = None    # second queue position
        self._last_check = 0
        self._check_interval = 300   # check every 5 minutes

    def run_once(self):
        if not self.enabled:
            return

        now = time.time()
        if now - self._last_check < self._check_interval:
            return

        self.log("[Research] 🔬 Checking research queue...")

        # Navigate to College of Order
        if not self._open_college():
            return

        # Check if queue 1 is empty
        img = self.safe_screenshot()
        if img is None:
            self.adb.press_back()
            return

        q1_empty = self.screen.exists(img, "research_q1_empty")
        q2_empty = self.screen.exists(img, "research_q2_empty")

        if q1_empty:
            self.log("[Research] Queue 1 empty — filling...")
            self._queue_next_research(queue=1)

        if self.use_second_queue and q2_empty:
            self.log("[Research] Queue 2 empty — filling...")
            self._queue_next_research(queue=2)

        if not q1_empty and not q2_empty:
            self.log("[Research] Both queues busy — nothing to do")

        self._last_check = now
        self.adb.press_back()
        self.wait(0.8)

    def _open_college(self) -> bool:
        """Navigate to College of Order building."""
        self.go_to_city()
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None:
            return False

        # Tap College of Order building
        if not self.tap_if_found(img, "college_building"):
            # Fallback: try known position (varies by city layout)
            self.adb.tap(760, 520)
        self.wait(1.2)

        img = self.safe_screenshot()
        if img is None:
            return False

        # Verify we opened the right building
        if self.screen.exists(img, "research_title"):
            return True

        self.log("[Research] ❌ Could not open College of Order")
        self.adb.press_back()
        return False

    def _queue_next_research(self, queue: int = 1):
        """Find and start the next research item from the priority queue."""
        item = self._get_next_item(queue)
        if not item:
            self.log("[Research] ⚠️ Research queue fully completed!")
            return

        tree, name, max_level, note = item
        self.log(f"[Research] Queuing: {name} ({tree}) — {note}")

        img = self.safe_screenshot()
        if img is None:
            return

        # Switch to correct tree tab
        if tree == "economy":
            self.tap_if_found(img, "economy_tree_tab") or self.adb.tap(480, 240)
        else:
            self.tap_if_found(img, "military_tree_tab") or self.adb.tap(680, 240)
        self.wait(0.8)

        # Find and tap research item
        # Template name maps to research button on the tree
        template = f"research_{name.lower().replace(' ', '_').replace('/', '_')}"
        img = self.safe_screenshot()
        if img is None:
            return

        found = self.tap_if_found(img, template)
        if not found:
            self.log(f"[Research] ⚠️ Template not found: {template} — scroll and retry")
            # Scroll down to find research
            self.adb.swipe_up(300)
            self.wait(0.5)
            img = self.safe_screenshot()
            if img is not None:
                found = self.tap_if_found(img, template)

        if not found:
            self.log(f"[Research] ❌ Could not locate {name} on tree")
            return

        self.wait(0.8)
        img = self.safe_screenshot()
        if img is None:
            return

        # Research popup — tap Research/Start button
        if self.tap_if_found(img, "start_research_btn"):
            self.wait(0.5)
            img = self.safe_screenshot()
            if img is not None:
                # Confirm (speedup prompt may appear)
                if self.screen.exists(img, "use_speedup_prompt"):
                    # Don't use speedups automatically unless on Research building
                    self.tap_if_found(img, "skip_speedup_btn") or self.adb.press_back()
                else:
                    self.tap_if_found(img, "confirm_btn") or self.adb.tap(960, 640)
                    self.wait(0.5)
                    self.log(f"[Research] ✅ {name} started in Queue {queue}!")
                    self._advance_queue(queue)
        else:
            self.log(f"[Research] ❌ Could not start research for {name}")

    def _get_next_item(self, queue: int):
        """Get the next research item for the given queue slot."""
        idx = self._queue_index if queue == 1 else (self._queue2_index or self._queue_index + 1)
        if idx >= len(self.RESEARCH_QUEUE):
            return None
        return self.RESEARCH_QUEUE[idx]

    def _advance_queue(self, queue: int):
        """Move to next item in research queue."""
        if queue == 1:
            self._queue_index = min(self._queue_index + 1, len(self.RESEARCH_QUEUE) - 1)
        else:
            if self._queue2_index is None:
                self._queue2_index = self._queue_index + 1
            else:
                self._queue2_index = min(self._queue2_index + 1, len(self.RESEARCH_QUEUE) - 1)

    def get_progress_pct(self) -> float:
        """Return overall research progress as percentage."""
        return min(100.0, (self._queue_index / len(self.RESEARCH_QUEUE)) * 100)

    def get_current_research_name(self) -> str:
        if self._queue_index < len(self.RESEARCH_QUEUE):
            return self.RESEARCH_QUEUE[self._queue_index][1]
        return "Complete!"
