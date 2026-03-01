"""
goblin.py — Goblin Market Module for CoD AutoBot
Handles Goblin Merchant visits: buys optimal items, skips bad deals, scraps duplicates.

BUY RULES:
  ✅ Speedups (ALL types) — always buy regardless of discount
  ✅ Hero Tokens (Epic/Legendary) — buy if ≥25% discount
  ⚡ Resources for resources (e.g. 40k Wood → 50k Gold) — only if ≥40% discount
  ⚡ Resource items (8h/24h boosts) — only if ≥50% discount AND paying resources
  ⚡ Ore/resources for Gems — only if ≥60% discount

SKIP RULES:
  ❌ Gold for Gems — terrible value, never
  ❌ Any item <25% discount (except speedups)
  ❌ Merchant re-roll more than 1 free refresh
"""

import time
from bot.base_module import BotModule


class GoblinModule(BotModule):

    # Items that are always worth buying
    ALWAYS_BUY = [
        "goblin_speedup_1min",
        "goblin_speedup_5min",
        "goblin_speedup_15min",
        "goblin_speedup_60min",
        "goblin_speedup_3h",
        "goblin_speedup_8h",
        "goblin_speedup_24h",
    ]

    # Items to buy ONLY if discount meets threshold
    CONDITIONAL_BUY = [
        # (template_name,  min_discount_pct, pay_with_gems_allowed)
        ("goblin_epic_hero_token",      25, False),
        ("goblin_legendary_hero_token", 25, True),   # legendary worth Gems at 25%+
        ("goblin_resource_boost_8h",    50, False),  # only with resources
        ("goblin_resource_boost_24h",   50, False),
        ("goblin_wood_bundle",          40, False),
        ("goblin_ore_bundle",           60, True),   # 60%+ only for gems
        ("goblin_gold_bundle",          60, False),
        ("goblin_mana_bundle",          50, False),
    ]

    # Items to NEVER buy
    NEVER_BUY = [
        "goblin_gold_for_gems",    # buying Gold with Gems — terrible
        "goblin_gems_direct",      # buying Gems with Gems (wtf)
        "goblin_speedup_for_gems_low",  # <25% off speedup for Gems
    ]

    def __init__(self, adb, screen, config, log_callback=None):
        super().__init__(adb, screen, config, log_callback)
        self.free_refresh_only = config.get("goblin_free_refresh_only", True)
        self._last_visit = 0
        self._visits_today = 0

    def run_once(self):
        if not self.enabled:
            return

        img = self.safe_screenshot()
        if img is None:
            return

        # Check if Goblin Merchant notification is visible
        if not self.screen.exists(img, "goblin_merchant_notification"):
            return

        self.log("[Goblin] 🟢 Goblin Merchant has arrived!")
        self._handle_merchant_visit()

    def _handle_merchant_visit(self):
        """Full flow for handling a Goblin Merchant visit."""
        self.go_to_city()
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None:
            return

        # Tap Goblin Market building (Hall Lv.6+)
        if not self.tap_if_found(img, "goblin_market_building"):
            self.log("[Goblin] ❌ Goblin Market building not found")
            return
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None:
            return

        # Tap "Visit Merchant" button
        if not self.tap_if_found(img, "visit_merchant_btn"):
            self.log("[Goblin] ❌ Merchant visit button not found")
            self.adb.press_back()
            return
        self.wait(1.2)

        # Process the merchant shop
        self._process_shop_items()

        # Free refresh once
        img = self.safe_screenshot()
        if img is not None and self.screen.exists(img, "free_refresh_btn"):
            self.log("[Goblin] 🔄 Using FREE refresh...")
            self.tap_if_found(img, "free_refresh_btn")
            self.wait(1.0)
            self._process_shop_items()

        # Close merchant
        self.adb.press_back()
        self._visits_today += 1
        self.log(f"[Goblin] ✅ Merchant visit complete (visit #{self._visits_today} today)")

        # Also check if scrapping is needed
        self._check_scrap_items()

    def _process_shop_items(self):
        """Scan visible merchant items and buy eligible ones."""
        img = self.safe_screenshot()
        if img is None:
            return

        bought = 0

        # Always buy speedups first
        for template in self.ALWAYS_BUY:
            img = self.safe_screenshot()
            if img is None:
                break
            if self.tap_if_found(img, template):
                self.wait(0.4)
                img = self.safe_screenshot()
                if img is not None:
                    if self.tap_if_found(img, "confirm_buy_btn"):
                        bought += 1
                        self.log(f"[Goblin] ✅ Bought: Speedup (always buy)")
                        self.wait(0.4)
                        self.dismiss_popups()

        # Conditional items — check discount before buying
        for template, min_discount, gems_ok in self.CONDITIONAL_BUY:
            img = self.safe_screenshot()
            if img is None:
                break

            item_match = self.screen.find(img, template)
            if not item_match:
                continue

            # Check discount label near the item
            discount = self._read_discount(img, item_match.x, item_match.y)
            self.log(f"[Goblin] Found {template}: {discount}% discount")

            if discount < min_discount:
                self.log(f"[Goblin] ⏭️ Skipping {template} — only {discount}% off (need {min_discount}%+)")
                continue

            # Check cost type — skip if Gems cost and not allowed
            cost_is_gems = self._cost_is_gems(img, item_match.x, item_match.y)
            if cost_is_gems and not gems_ok:
                self.log(f"[Goblin] ⏭️ Skipping {template} — costs Gems and gems_ok=False")
                continue

            # Buy it
            self.adb.tap(item_match.x, item_match.y)
            self.wait(0.4)
            img = self.safe_screenshot()
            if img is not None:
                if self.tap_if_found(img, "confirm_buy_btn"):
                    bought += 1
                    self.log(f"[Goblin] ✅ Bought: {template} at {discount}% off!")
                    self.wait(0.4)
                    self.dismiss_popups()

        # Never-buy check — log if these appear so we don't accidentally tap
        img = self.safe_screenshot()
        if img is not None:
            for template in self.NEVER_BUY:
                if self.screen.exists(img, template):
                    self.log(f"[Goblin] 🚫 Skipping {template} — on NEVER BUY list")

        self.log(f"[Goblin] 📦 Session: {bought} items purchased")

    def _read_discount(self, screen_img, item_x: int, item_y: int) -> int:
        """
        Read the discount percentage shown on a merchant item.
        Looks for the red/orange discount badge near the item.
        Returns 0 if no discount detected or OCR not available.
        """
        # In a real implementation this would:
        # 1. Crop region around (item_x, item_y) looking for discount badge
        # 2. Use pytesseract OCR to read the number (e.g. "-60%")
        # 3. Parse and return the integer

        # Without OCR: use color detection for the discount badge
        # Orange badge = discount present; check badge presence
        # For now return 0 (conservative — won't buy without confirmed discount)
        return 0  # TODO: implement OCR or badge color detection

    def _cost_is_gems(self, screen_img, item_x: int, item_y: int) -> bool:
        """Check if the item's cost indicator shows Gems (diamond icon)."""
        # Crop region near cost display and look for Gem icon template
        img = self.safe_screenshot()
        if img is None:
            return False
        # Look for gem icon within the item's cost area
        return self.screen.exists(img, "gems_cost_icon")

    def _check_scrap_items(self):
        """
        Check if there are duplicate hero tokens or artifacts to scrap.
        Scrapping gives Universal Hero Tokens and Artifact Tokens.
        """
        img = self.safe_screenshot()
        if img is None:
            return

        # Tap "Scrap" tab in Goblin Market if visible
        if self.tap_if_found(img, "scrap_tab"):
            self.wait(0.8)
            img = self.safe_screenshot()
            if img is not None:
                # Scrap all duplicates
                if self.tap_if_found(img, "scrap_all_btn"):
                    self.wait(0.5)
                    img = self.safe_screenshot()
                    if img is not None:
                        self.tap_if_found(img, "confirm_scrap_btn")
                        self.wait(0.5)
                        self.log("[Goblin] ♻️ Duplicate items scrapped for Universal Tokens!")
                    self.dismiss_popups()
