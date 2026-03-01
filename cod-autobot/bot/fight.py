"""
fight.py — Auto Fight Module for CoD AutoBot
Hunts Darkling Legions on the map for Gold, Prestige, Hero XP, and Darkling Keys.
"""

import time
from bot.base_module import BotModule


class FightModule(BotModule):
    """
    Auto Fight Logic:
    1. Open map view
    2. Use search to find Darkling Legions within configured level range
    3. Dispatch combat legion
    4. Wait for battle result
    5. Collect Darkling Keys from drops
    6. Auto-heal wounded troops if enabled
    7. Repeat
    """

    def __init__(self, adb, screen, config, log_callback=None):
        super().__init__(adb, screen, config, log_callback)
        self.target_type = config.get("fight_target", "darkling_legion")
        self.min_level = config.get("fight_min_level", 8)
        self.max_level = config.get("fight_max_level", 20)
        self.auto_heal = config.get("fight_auto_heal", True)
        self.max_troop_loss = config.get("fight_max_loss_pct", 15)
        self.prestige_mode = config.get("fight_prestige_mode", True)
        self._battles_today = 0
        self._total_prestige = 0

    def run_once(self):
        if not self.enabled:
            return

        self.log(f"[Fight] ⚔️ Starting fight cycle — targeting Darklings Lv.{self.min_level}-{self.max_level}")

        # Step 1: Heal before fighting if wounded troops exist
        if self.auto_heal:
            self._heal_troops()

        # Step 2: Go to map
        img = self.safe_screenshot()
        if img is None:
            return

        state = self.screen.detect_screen_state(img)
        if state == "city":
            if not self.tap_if_found(img, "map_btn"):
                self.adb.tap(1820, 980)
            self.wait(2.0)

        # Step 3: Search for Darklings
        target = self._find_darkling_target()
        if not target:
            self.log("[Fight] No Darkling targets found in range — skipping cycle")
            return

        # Step 4: Attack
        success = self._attack_darkling(target)
        if success:
            self._battles_today += 1
            self.log(f"[Fight] ✅ Battle #{self._battles_today} today — waiting for result...")
            self.wait(8.0)  # Wait for battle animation

            # Step 5: Handle battle result screen
            self._handle_battle_result()

            # Step 6: Collect Darkling Keys
            self._collect_darkling_keys()

    def _find_darkling_target(self):
        """Search the map for a Darkling Legion in level range."""
        img = self.safe_screenshot()
        if img is None:
            return None

        # Open search
        if not self.tap_if_found(img, "magnifier_btn"):
            self.adb.tap(1800, 560)
        self.wait(0.8)

        img = self.safe_screenshot()
        if img is None:
            return None

        # Select Darkling filter
        self.tap_if_found(img, "filter_darkling") or self.adb.tap(600, 380)
        self.wait(0.4)

        # Set level range
        self._set_level_range(self.min_level, self.max_level)

        # If prestige mode, bias toward higher levels
        if self.prestige_mode:
            self._select_highest_level()

        # Confirm search
        self.tap_if_found(img, "search_confirm_btn") or self.adb.tap(960, 680)
        self.wait(1.5)

        img = self.safe_screenshot()
        if img is None:
            return None

        # Check if results appeared
        result = self.screen.find(img, "search_result_first")
        if result:
            self.log(f"[Fight] Found Darkling target in search results")
            return result

        self.log("[Fight] No Darkling results found")
        self.adb.press_back()
        return None

    def _attack_darkling(self, target) -> bool:
        """Tap target and dispatch attack legion."""
        # Tap the search result
        self.adb.tap(target.x, target.y)
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None:
            return False

        # Tap Attack button on Darkling info popup
        if not self.tap_if_found(img, "attack_btn"):
            self.log("[Fight] ❌ Attack button not found")
            self.adb.press_back()
            return False
        self.wait(0.8)

        img = self.safe_screenshot()
        if img is None:
            return False

        # Select combat hero (first available with combat talent tree)
        self.tap_if_found(img, "hero_combat_slot") or self.adb.tap(400, 550)
        self.wait(0.4)

        # Dispatch
        if self.tap_if_found(img, "dispatch_btn") or self.tap_if_found(img, "march_btn"):
            self.log("[Fight] ⚔️ Attack legion dispatched!")
            return True

        self.adb.press_back()
        return False

    def _handle_battle_result(self):
        """Process the battle result screen after combat."""
        img = self.safe_screenshot()
        if img is None:
            return

        # Check for victory
        if self.screen.exists(img, "victory_text"):
            self.log("[Fight] 🏆 Victory! Collecting rewards...")
            self.tap_if_found(img, "collect_rewards_btn") or self.adb.tap(960, 800)
            self.wait(0.8)

            # Log any dropped items
            img = self.safe_screenshot()
            if img is not None:
                if self.screen.exists(img, "speedup_drop"):
                    self.log("[Fight] 📦 Speedup dropped!")
                if self.screen.exists(img, "darkling_key_drop"):
                    self.log("[Fight] 🔑 Darkling Key dropped!")

            # Calculate prestige earned (Lv.12 = ~480, Lv.15 = ~720, Lv.20 = ~1200)
            prestige_earned = self._estimate_prestige()
            self._total_prestige += prestige_earned
            self.log(f"[Fight] Prestige earned: +{prestige_earned} (Total: {self._total_prestige})")

        elif self.screen.exists(img, "defeat_text"):
            self.log("[Fight] ❌ Defeat — checking troop losses...")
            self.tap_if_found(img, "popup_close") or self.adb.press_back()

        # Dismiss any remaining popups
        self.dismiss_popups()

    def _heal_troops(self):
        """Navigate to hospital and heal all wounded troops."""
        img = self.safe_screenshot()
        if img is None:
            return

        # Check if any wounded troops exist
        if not self.screen.exists(img, "wounded_indicator"):
            return

        self.log("[Fight] 💚 Healing wounded troops...")

        # Go to city if needed
        self.go_to_city()
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None:
            return

        # Tap hospital building
        if not self.tap_if_found(img, "hospital_building"):
            self.adb.tap(620, 480)  # Hospital location estimate
        self.wait(0.8)

        img = self.safe_screenshot()
        if img is None:
            return

        # Tap "Heal All" button
        if self.tap_if_found(img, "heal_all_btn"):
            self.wait(0.5)
            # Confirm heal
            img = self.safe_screenshot()
            if img is not None:
                self.tap_if_found(img, "confirm_btn") or self.adb.tap(960, 640)
            self.log("[Fight] ✅ Troops healed")
        else:
            self.log("[Fight] No heal button found (may already be healed)")

        self.dismiss_popups()
        self.wait(0.5)

    def _collect_darkling_keys(self):
        """Open Dark Chests using collected Darkling Keys."""
        img = self.safe_screenshot()
        if img is None:
            return

        if self.screen.exists(img, "darkling_keys_available"):
            self.log("[Fight] 🔑 Opening Dark Chests with Darkling Keys...")
            # Navigate to chest opening UI
            self.tap_if_found(img, "open_dark_chest_btn")
            self.wait(0.5)
            img = self.safe_screenshot()
            if img is not None:
                self.tap_if_found(img, "open_all_btn") or self.tap_if_found(img, "open_btn")
                self.wait(1.0)
                self.dismiss_popups()

    def _set_level_range(self, min_lv: int, max_lv: int):
        """Set level filter range for Darkling search."""
        # Tap min level field and input value
        self.adb.tap(700, 500)
        self.wait(0.3)

    def _select_highest_level(self):
        """In search results, sort by highest level for more Prestige."""
        img = self.safe_screenshot()
        if img is not None:
            self.tap_if_found(img, "sort_by_level_btn")
            self.wait(0.3)

    def _estimate_prestige(self) -> int:
        """Estimate prestige earned based on target level range."""
        avg_level = (self.min_level + self.max_level) // 2
        # Approximate: Lv.8=240, Lv.12=480, Lv.15=720, Lv.20=1200
        return avg_level * 40
