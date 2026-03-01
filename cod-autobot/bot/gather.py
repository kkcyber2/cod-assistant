"""
gather.py — Auto Gather Module for CoD AutoBot
Automatically sends legions to Wood, Ore, Gold, and Mana nodes on the map.
Respects alliance territory bonus, march slot limits, and storage thresholds.
"""

import time
import random
from bot.base_module import BotModule


class GatherModule(BotModule):
    """
    Auto Gather Logic:
    1. Open map view
    2. Use Search/Filter to find resource tiles by type & level
    3. Tap highest-level available tile
    4. Select best gathering hero (Kella=Gold, Pan=Wood, Chakcha=Ore, Indis=Mana)
    5. Remove secondary commander for max efficiency
    6. Send march
    7. Repeat for each available march slot
    8. Track march return times and re-send when returned
    """

    GATHER_HEROES = {
        "gold": "Kella",
        "wood": "Pan",
        "ore":  "Chakcha",
        "mana": "Indis",
        "any":  "Kella",   # fallback
    }

    # Resource node search filter button positions (1920x1080)
    RESOURCE_FILTERS = {
        "gold": (680, 420),
        "wood": (760, 420),
        "ore":  (840, 420),
        "mana": (920, 420),
    }

    def __init__(self, adb, screen, config, log_callback=None):
        super().__init__(adb, screen, config, log_callback)
        self.active_marches = 0
        self.max_marches = config.get("gather_marches", 5)
        self.mode = config.get("gather_mode", "smart")
        self.min_node_level = config.get("gather_min_level", 3)
        self.alliance_territory_only = config.get("gather_alliance_only", True)
        self.use_single_commander = config.get("gather_single_commander", True)
        self.gather_mana = config.get("gather_mana", True)
        self._march_timers = []  # timestamps when each march finishes

    def run_once(self):
        """Execute one gather cycle."""
        if not self.enabled:
            return

        self.log("[Gather] 🌾 Starting gather cycle...")

        # Check how many march slots are available
        available_slots = self._count_available_slots()
        if available_slots == 0:
            self.log("[Gather] All march slots busy — waiting for returns")
            return

        self.log(f"[Gather] {available_slots} march slot(s) available")

        # Determine resource priority order
        resources = self._get_resource_priority()

        # Send marches for available slots
        marches_sent = 0
        for resource in resources:
            if marches_sent >= available_slots:
                break
            if self._send_gather_march(resource):
                marches_sent += 1
                time.sleep(1.5)

        self.log(f"[Gather] ✅ Cycle complete — {marches_sent} marches dispatched")

    def _get_resource_priority(self) -> list:
        """Return resource types in priority order based on config mode."""
        if self.mode == "gold_priority":
            order = ["gold", "ore", "wood"]
        elif self.mode == "wood_priority":
            order = ["wood", "ore", "gold"]
        elif self.mode == "ore_priority":
            order = ["ore", "gold", "wood"]
        elif self.mode == "mana_priority":
            order = ["mana", "gold", "ore", "wood"]
        else:  # smart auto — cycle all types
            order = ["gold", "wood", "ore", "mana"]

        if not self.gather_mana and "mana" in order:
            order.remove("mana")

        # Multiply list to fill all march slots
        return (order * 3)[:self.max_marches]

    def _send_gather_march(self, resource_type: str) -> bool:
        """
        Full flow to send one gathering march to a resource node.
        Returns True if march successfully dispatched.
        """
        img = self.safe_screenshot()
        if img is None:
            return False

        state = self.screen.detect_screen_state(img)

        # 1. Navigate to map if in city
        if state == "city":
            self.log(f"[Gather] Opening world map...")
            if not self.tap_if_found(img, "map_btn"):
                # Try the minimap icon at bottom right
                self.adb.tap(1820, 980)
            self.wait(2.0)
            img = self.safe_screenshot()
            if img is None:
                return False

        # 2. Open resource search
        self.log(f"[Gather] Searching for {resource_type} nodes (Lv.{self.min_node_level}+)...")
        if not self.tap_if_found(img, "magnifier_btn"):
            self.adb.tap(1800, 560)  # Search icon top-right of map
        self.wait(0.8)

        img = self.safe_screenshot()
        if img is None:
            return False

        # 3. Select resource type filter
        filter_pos = self.RESOURCE_FILTERS.get(resource_type, self.RESOURCE_FILTERS["gold"])
        self.adb.tap(*filter_pos)
        self.wait(0.5)

        # Set minimum level filter
        self._set_level_filter(self.min_node_level)
        self.wait(0.3)

        # Tap search/confirm
        self.tap_if_found(img, "search_confirm_btn") or self.adb.tap(960, 680)
        self.wait(1.5)

        img = self.safe_screenshot()
        if img is None:
            return False

        # 4. Tap the first result tile in search results list
        if not self.tap_if_found(img, "search_result_first"):
            self.adb.tap(340, 300)  # First result in list
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None:
            return False

        # 5. Tap the "Gather" button on the tile info popup
        if not self.tap_if_found(img, "gather_btn"):
            self.log(f"[Gather] ❌ Could not find Gather button for {resource_type}")
            self.adb.press_back()
            return False
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None:
            return False

        # 6. Select gathering hero
        hero_name = self.GATHER_HEROES.get(resource_type, "Kella")
        self.log(f"[Gather] Selecting hero: {hero_name}")
        hero_found = self.tap_if_found(img, f"hero_{hero_name.lower()}")
        if not hero_found:
            # Tap first available hero slot
            self.adb.tap(400, 550)
        self.wait(0.5)

        # 7. Remove secondary commander if enabled
        if self.use_single_commander:
            img = self.safe_screenshot()
            if img is not None:
                self.tap_if_found(img, "remove_secondary_btn")
                self.wait(0.3)

        # 8. Tap Dispatch / March button
        img = self.safe_screenshot()
        if img is None:
            return False

        if self.tap_if_found(img, "dispatch_btn") or self.tap_if_found(img, "march_btn"):
            self.log(f"[Gather] ✅ March dispatched to {resource_type} node with {hero_name}")
            self._march_timers.append(time.time() + 1800)  # assume ~30min return
            self.active_marches += 1
            self.wait(1.0)
            self.adb.press_back()
            self.wait(0.5)
            return True

        self.log(f"[Gather] ❌ Could not dispatch march for {resource_type}")
        self.adb.press_back()
        return False

    def _count_available_slots(self) -> int:
        """Count how many march slots are currently free."""
        now = time.time()
        self._march_timers = [t for t in self._march_timers if t > now]
        busy = len(self._march_timers)
        available = max(0, self.max_marches - busy)
        return available

    def _set_level_filter(self, min_level: int):
        """Interact with level filter UI to set minimum node level."""
        # Level filter stepper — tap '-' or '+' buttons to reach desired level
        # Positions vary by resolution; these are 1920x1080 estimates
        level_plus_btn = (810, 480)
        for _ in range(min_level - 1):  # Start is Lv.1, tap + to reach min
            self.adb.tap(*level_plus_btn)
            time.sleep(0.15)

    def on_storage_full(self):
        """Called when city storage approaches capacity — recall marches."""
        self.log("[Gather] ⚠️ Storage near full — recalling gather marches")
        img = self.safe_screenshot()
        if img is None:
            return
        # Tap recall all marches button if visible
        self.tap_if_found(img, "recall_march_btn")
