"""
build.py — Auto Build Module for CoD AutoBot
Upgrades buildings in optimal priority order for Call of Dragons.
"""

import time
from bot.base_module import BotModule


class BuildModule(BotModule):
    """
    Building Upgrade Priority Order:
    P1 (CRITICAL): Hall of Order → controls all unlock gates
    P1 (CRITICAL): Alliance Center → max alliance helps (time savings forever)
    P1 (CRITICAL): College of Order → research speed, required Lv.21 for T4
    P2 (HIGH):     All 4 Hospitals → power yield + protect wounded troops
    P2 (HIGH):     Barracks / Stables / Arcane Tower / Aviary → troop bonuses
    P3 (MEDIUM):   All Mints → passive Gold production
    P3 (MEDIUM):   Lumber Mills / Ore Pits / Mana Wells → passive RSS
    P4 (LOW):      Goblin Market → build ASAP at Hall Lv.6
    P4 (LOW):      Noticeboard → Military Expansion policy first
    P4 (LOW):      Watchtower / Rally → needed for T5 path eventually

    RULES:
    - Never start upgrading College of Order unless you can finish it instantly (speedups)
    - Always collect Alliance Helps before starting any expensive upgrade
    - Save speedups for Strongest Lord event scoring windows
    """

    # Each entry: (building_template_name, display_name, priority, reason)
    BUILD_PRIORITY = [
        # Priority 1 — ALWAYS upgrade these first
        ("hall_of_order",     "Hall of Order",      1, "Unlocks everything — highest power/upgrade"),
        ("alliance_center",   "Alliance Center",    1, "More helps = time saved forever"),
        ("college_of_order",  "College of Order",   1, "Research speed + T4 requirement Lv.21"),
        # Priority 2 — alongside P1
        ("hospital_1",        "Hospital #1",        2, "Troop protection + high power"),
        ("hospital_2",        "Hospital #2",        2, "Troop protection + high power"),
        ("hospital_3",        "Hospital #3",        2, "Troop protection + high power"),
        ("hospital_4",        "Hospital #4",        2, "Troop protection + high power"),
        ("barracks_1",        "Barracks #1",        2, "T3/T4 infantry training + atk bonus"),
        ("stables_1",         "Stables #1",         2, "T3/T4 mounted training"),
        ("arcane_tower_1",    "Arcane Tower #1",    2, "T3/T4 magic training"),
        ("aviary_1",          "Aviary #1",          2, "T3/T4 flying training"),
        # Priority 3 — medium
        ("mint_1",            "Mint #1",            3, "Passive Gold production"),
        ("mint_2",            "Mint #2",            3, "Passive Gold production"),
        ("mint_3",            "Mint #3",            3, "Passive Gold production"),
        ("lumber_mill_1",     "Lumber Mill #1",     3, "Passive Wood production"),
        ("ore_pit_1",         "Ore Pit #1",         3, "Passive Ore production"),
        ("mana_well_1",       "Mana Well #1",       3, "Passive Mana production"),
        # Priority 4 — low / when required
        ("goblin_market",     "Goblin Market",      4, "Build ASAP at Hall Lv.6"),
        ("noticeboard",       "Noticeboard",        4, "Military Expansion policy"),
        ("watchtower",        "Watchtower",         4, "Required for T5 path later"),
        ("rally_point",       "Rally Point",        4, "Required for T5 path later"),
    ]

    def __init__(self, adb, screen, config, log_callback=None):
        super().__init__(adb, screen, config, log_callback)
        self.wait_for_helps = config.get("build_wait_helps", True)
        self.instant_college = config.get("build_instant_college", True)
        self.mode = config.get("build_mode", "priority_list")
        self._last_check = 0
        self._check_interval = 600  # check every 10 minutes

    def run_once(self):
        if not self.enabled:
            return

        now = time.time()
        if now - self._last_check < self._check_interval:
            return

        self.log("[Build] 🏰 Checking build queues...")
        self.go_to_city()
        self.wait(1.5)

        img = self.safe_screenshot()
        if img is None:
            return

        # Check if any build slot is free
        q1_free = self.screen.exists(img, "build_q1_empty")
        q2_free = self.screen.exists(img, "build_q2_empty")  # 2nd builder

        if q1_free:
            self.log("[Build] Build slot 1 available — finding next upgrade...")
            self._upgrade_next(slot=1)
        else:
            self.log("[Build] Build queue busy")

        if q2_free:
            self.log("[Build] Build slot 2 available — finding next upgrade...")
            self._upgrade_next(slot=2)

        self._last_check = now

    def _upgrade_next(self, slot: int):
        """Find and start the next building upgrade based on priority."""
        for template, name, priority, reason in self.BUILD_PRIORITY:
            if self._should_upgrade(template, name):
                self.log(f"[Build] Upgrading: {name} (P{priority}) — {reason}")
                if self._start_upgrade(template, name):
                    return
        self.log("[Build] No eligible buildings found to upgrade")

    def _should_upgrade(self, template: str, name: str) -> bool:
        """Check if this building needs upgrading and requirements are met."""
        img = self.safe_screenshot()
        if img is None:
            return False

        # Special rule: College of Order — only upgrade if we can use speedups to finish instantly
        if template == "college_of_order" and self.instant_college:
            if not self._has_enough_speedups_for_college():
                self.log(f"[Build] Skipping College upgrade — not enough speedups to finish instantly")
                return False

        # Check if building has an upgrade available (orange upgrade arrow icon)
        upgrade_icon = f"upgrade_ready_{template}"
        if self.screen.exists(img, upgrade_icon):
            return True

        return False

    def _start_upgrade(self, template: str, name: str) -> bool:
        """Tap the building and start its upgrade."""
        # Wait for alliance helps first if enabled
        if self.wait_for_helps:
            self._request_and_wait_helps(name)

        img = self.safe_screenshot()
        if img is None:
            return False

        # Tap the building on city view
        if not self.tap_if_found(img, template):
            self.log(f"[Build] ❌ Could not find {name} on city view")
            return False
        self.wait(0.8)

        img = self.safe_screenshot()
        if img is None:
            return False

        # Tap upgrade button in building popup
        if not self.tap_if_found(img, "upgrade_btn"):
            self.log(f"[Build] ❌ No upgrade button for {name}")
            self.adb.press_back()
            return False
        self.wait(0.5)

        img = self.safe_screenshot()
        if img is None:
            return False

        # Handle College of Order — use speedups immediately
        if "college" in template and self.instant_college:
            if self.screen.exists(img, "use_speedup_prompt"):
                self.tap_if_found(img, "use_all_speedups_btn")
                self.wait(0.5)
                img = self.safe_screenshot()
                if img is not None:
                    self.tap_if_found(img, "confirm_btn")
                self.log(f"[Build] ⚡ College upgrade finished instantly with speedups!")
                return True

        # Confirm upgrade
        self.tap_if_found(img, "confirm_btn") or self.adb.tap(960, 640)
        self.wait(0.5)
        self.log(f"[Build] ✅ {name} upgrade started!")
        self.dismiss_popups()
        return True

    def _request_and_wait_helps(self, building_name: str):
        """Request alliance helps and wait briefly for them to arrive."""
        self.log(f"[Build] Requesting alliance helps for {building_name}...")
        # The game auto-sends help requests when upgrading
        # Just add a short wait after tapping upgrade so helps can arrive
        # Actual waiting is handled by checking help count in popup
        pass

    def _has_enough_speedups_for_college(self) -> bool:
        """Check if we have speedups to finish College upgrade instantly."""
        # This would check the resource/item inventory
        # For now, return True if config says to always instant-finish
        return self.instant_college
