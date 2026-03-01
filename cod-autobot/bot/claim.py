"""
claim.py — Auto Claim Module for CoD AutoBot
Collects all daily rewards: quests, alliance resources, gifts, membership, Titan chest, mail.
"""

import time
from bot.base_module import BotModule


class ClaimModule(BotModule):
    """
    Auto Claim covers:
    - Daily Quests (top-left scroll icon)
    - Side Quests
    - Titan's Legacy Chest (6 daily challenges → chest)
    - Alliance Territory Resources (Gold, Wood, Ore, Mana tab)
    - Alliance Gift Bags
    - Alliance Helps (click help for all allies)
    - Honorary Membership daily reward
    - Membership Store weekly items (CP tokens, speedups, medals)
    - Mailbox system rewards
    - Dark Chest opening with Darkling Keys
    """

    def __init__(self, adb, screen, config, log_callback=None):
        super().__init__(adb, screen, config, log_callback)
        self.claim_daily_quests   = config.get("claim_daily_quests", True)
        self.claim_alliance_rss   = config.get("claim_alliance_rss", True)
        self.claim_alliance_gifts = config.get("claim_alliance_gifts", True)
        self.claim_alliance_helps = config.get("claim_alliance_helps", True)
        self.claim_membership     = config.get("claim_membership", True)
        self.claim_membership_shop= config.get("claim_membership_shop", True)
        self.claim_titan_chest    = config.get("claim_titan_chest", True)
        self.claim_mail           = config.get("claim_mail", True)
        self._last_claim_time = 0
        self._claim_interval = config.get("claim_interval_mins", 30) * 60

    def run_once(self):
        if not self.enabled:
            return

        now = time.time()
        if now - self._last_claim_time < self._claim_interval:
            return

        self.log("[Claim] 🎁 Starting claim cycle...")
        self.go_to_city()
        self.wait(1.5)

        if self.claim_daily_quests:   self._claim_daily_quests()
        if self.claim_titan_chest:    self._claim_titan_legacy()
        if self.claim_alliance_rss:   self._claim_alliance_resources()
        if self.claim_alliance_gifts: self._claim_alliance_gifts()
        if self.claim_alliance_helps: self._do_alliance_helps()
        if self.claim_membership:     self._claim_membership_daily()
        if self.claim_membership_shop:self._buy_membership_shop_items()
        if self.claim_mail:           self._claim_mail()

        self._last_claim_time = now
        self.log("[Claim] ✅ All claim tasks completed")

    # ──────────────── DAILY QUESTS ────────────────

    def _claim_daily_quests(self):
        """Tap quest icon → claim all completed quests."""
        self.log("[Claim] Claiming Daily & Side Quests...")
        img = self.safe_screenshot()
        if img is None: return

        # Quest icon — usually top-left scroll/book icon
        if not self.tap_if_found(img, "quest_icon"):
            self.adb.tap(68, 340)   # approximate position
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None: return

        # Tap "Claim All" or claim each completed quest
        if not self.tap_if_found(img, "claim_all_quests_btn"):
            # Claim individual quests — look for orange claim buttons
            claimed = 0
            for _ in range(8):  # up to 8 quests
                img = self.safe_screenshot()
                if img is None: break
                if self.tap_if_found(img, "quest_claim_btn"):
                    claimed += 1
                    self.wait(0.5)
                else:
                    break
            self.log(f"[Claim] Claimed {claimed} quest reward(s)")

        # Side quests tab
        self.tap_if_found(img, "side_quests_tab")
        self.wait(0.5)
        img = self.safe_screenshot()
        if img is not None:
            self.tap_if_found(img, "claim_all_quests_btn")
            self.wait(0.5)

        self.dismiss_popups()
        self.adb.press_back()
        self.wait(0.8)

    # ──────────────── TITAN'S LEGACY ────────────────

    def _claim_titan_legacy(self):
        """Open Titan's Legacy → collect Daily Challenge chest."""
        self.log("[Claim] Checking Titan's Legacy chest...")
        img = self.safe_screenshot()
        if img is None: return

        # Titan's Legacy icon (usually right-side events panel)
        if not self.tap_if_found(img, "titans_legacy_icon"):
            self.adb.tap(1830, 450)
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None: return

        # Check if chest is ready (6 challenges completed)
        if self.screen.exists(img, "titan_chest_ready"):
            self.tap_if_found(img, "titan_chest_ready")
            self.wait(0.8)
            img = self.safe_screenshot()
            if img is not None:
                self.tap_if_found(img, "open_chest_btn") or self.adb.tap(960, 700)
                self.wait(1.0)
                self.dismiss_popups()
                self.log("[Claim] ✅ Titan's Legacy chest opened — Rune EXP + Keys claimed!")
        else:
            self.log("[Claim] Titan chest not ready yet")

        self.adb.press_back()
        self.wait(0.5)

    # ──────────────── ALLIANCE RESOURCES ────────────────

    def _claim_alliance_resources(self):
        """Alliance → Territory tab → Claim Gold, Wood, Ore, Mana."""
        self.log("[Claim] Claiming Alliance Territory resources...")
        img = self.safe_screenshot()
        if img is None: return

        # Open Alliance (flag icon, usually bottom bar)
        if not self.tap_if_found(img, "alliance_btn"):
            self.adb.tap(230, 1040)
        self.wait(1.2)

        img = self.safe_screenshot()
        if img is None: return

        # Go to Territory tab
        self.tap_if_found(img, "territory_tab") or self.adb.tap(450, 200)
        self.wait(0.8)

        img = self.safe_screenshot()
        if img is None: return

        # Claim each resource type
        for resource in ["alliance_gold_claim", "alliance_wood_claim",
                         "alliance_ore_claim", "alliance_mana_claim"]:
            self.tap_if_found(img, resource)
            self.wait(0.3)
            img = self.safe_screenshot()
            if img is None: break

        # Generic claim all button
        img = self.safe_screenshot()
        if img is not None:
            if self.tap_if_found(img, "alliance_claim_all_btn"):
                self.wait(0.5)
                self.dismiss_popups()
                self.log("[Claim] ✅ Alliance Territory resources claimed!")

        self.adb.press_back()
        self.wait(0.5)

    # ──────────────── ALLIANCE GIFTS ────────────────

    def _claim_alliance_gifts(self):
        """Alliance → Gifts tab → Claim all gift bags."""
        self.log("[Claim] Collecting Alliance gift bags...")
        img = self.safe_screenshot()
        if img is None: return

        if not self.tap_if_found(img, "alliance_btn"):
            self.adb.tap(230, 1040)
        self.wait(1.2)

        img = self.safe_screenshot()
        if img is None: return

        # Gifts tab
        self.tap_if_found(img, "alliance_gifts_tab") or self.adb.tap(620, 200)
        self.wait(0.8)

        img = self.safe_screenshot()
        if img is None: return

        # Claim all gifts
        if self.tap_if_found(img, "claim_all_gifts_btn"):
            self.wait(0.5)
            self.log("[Claim] ✅ Alliance gift bags claimed!")
        else:
            self.log("[Claim] No new alliance gifts available")

        self.adb.press_back()
        self.wait(0.5)

    # ──────────────── ALLIANCE HELPS ────────────────

    def _do_alliance_helps(self):
        """Tap the Help button to assist alliance members with builds/research."""
        self.log("[Claim] Providing Alliance helps...")
        img = self.safe_screenshot()
        if img is None: return

        if not self.tap_if_found(img, "alliance_btn"):
            self.adb.tap(230, 1040)
        self.wait(1.2)

        img = self.safe_screenshot()
        if img is None: return

        # Help All button
        helps_given = 0
        if self.tap_if_found(img, "help_all_btn"):
            self.wait(0.5)
            helps_given = 30  # max helps
            self.log(f"[Claim] ✅ Alliance Help All clicked — up to 30 helps given")
        else:
            # Individually help if no "Help All"
            for _ in range(30):
                img = self.safe_screenshot()
                if img is None: break
                if self.tap_if_found(img, "individual_help_btn"):
                    helps_given += 1
                    self.wait(0.2)
                else:
                    break
            self.log(f"[Claim] ✅ {helps_given} individual helps given")

        self.adb.press_back()
        self.wait(0.5)

    # ──────────────── MEMBERSHIP ────────────────

    def _claim_membership_daily(self):
        """Store → Honorary Membership → Claim daily reward."""
        self.log("[Claim] Claiming Membership daily reward...")
        img = self.safe_screenshot()
        if img is None: return

        # Open Store/Shop
        self.tap_if_found(img, "shop_btn") or self.adb.tap(100, 1040)
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None: return

        # Honorary Membership tab
        self.tap_if_found(img, "membership_tab")
        self.wait(0.8)

        img = self.safe_screenshot()
        if img is None: return

        if self.tap_if_found(img, "membership_daily_claim_btn"):
            self.wait(0.5)
            self.dismiss_popups()
            self.log("[Claim] ✅ Membership daily reward claimed!")
        else:
            self.log("[Claim] Membership daily already claimed today")

        self.adb.press_back()
        self.wait(0.5)

    # ──────────────── MEMBERSHIP SHOP ────────────────

    def _buy_membership_shop_items(self):
        """
        Buy weekly membership shop items (resets Mon 0 UTC):
        - CP Recovery tokens
        - 5-min speedups
        - Epic/Legendary Hero Medals
        Only buys with resources (Gold/Wood/Ore), never with Gems.
        """
        self.log("[Claim] Buying Membership Shop weekly items...")
        img = self.safe_screenshot()
        if img is None: return

        self.tap_if_found(img, "shop_btn") or self.adb.tap(100, 1040)
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None: return

        self.tap_if_found(img, "honor_shop_tab")
        self.wait(0.8)

        # Items to buy: CP recovery, 5min speedups, epic medals, legendary medals
        priority_items = [
            "shop_cp_recovery",
            "shop_5min_speedup",
            "shop_epic_medal",
            "shop_legendary_medal",
        ]

        bought = 0
        for item in priority_items:
            img = self.safe_screenshot()
            if img is None: break
            if self.tap_if_found(img, item):
                self.wait(0.4)
                img = self.safe_screenshot()
                if img is not None:
                    # Only confirm if cost is resources not Gems
                    if not self.screen.exists(img, "gems_cost_icon"):
                        self.tap_if_found(img, "confirm_btn")
                        self.wait(0.3)
                        bought += 1
                    else:
                        self.adb.press_back()

        self.log(f"[Claim] ✅ Membership shop: {bought} item(s) purchased with resources")
        self.adb.press_back()
        self.wait(0.5)

    # ──────────────── MAIL ────────────────

    def _claim_mail(self):
        """Check mailbox and claim any system reward mails."""
        img = self.safe_screenshot()
        if img is None: return

        # Mail icon (envelope, usually top area)
        if not self.screen.exists(img, "mail_notification"):
            return  # No new mail

        self.log("[Claim] Checking mailbox for reward mails...")
        self.tap_if_found(img, "mail_icon") or self.adb.tap(1700, 80)
        self.wait(1.0)

        img = self.safe_screenshot()
        if img is None: return

        # System mail tab → claim all
        self.tap_if_found(img, "system_mail_tab")
        self.wait(0.5)

        img = self.safe_screenshot()
        if img is None: return

        if self.tap_if_found(img, "claim_all_mail_btn"):
            self.wait(0.5)
            self.log("[Claim] ✅ Mail rewards claimed!")

        self.adb.press_back()
        self.wait(0.5)
