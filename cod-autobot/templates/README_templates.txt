HOW TO CAPTURE TEMPLATES FOR CoD AutoBot
==========================================

Templates are small PNG screenshots of buttons the bot needs to find on screen.
WITHOUT TEMPLATES THE BOT CANNOT WORK.

STEP 1: SET BLUESTACKS RESOLUTION
- BlueStacks Settings → Display → Resolution → 1920 x 1080 (REQUIRED)
- DPI: 240

STEP 2: TAKE A FULL SCREENSHOT
- Run: python main.py --test
- This saves "test_screenshot.png" in the project root
- OR: use the GUI → Settings → "Test Screenshot" button

STEP 3: CROP EACH BUTTON
- Open test_screenshot.png in any image editor
- Crop TIGHTLY around each button/icon below
- Save as the exact filename shown (e.g. "map_btn.png")
- Save all files into the templates/ folder

TIPS:
- Crop as tightly as possible (no extra background)
- The button must be clearly visible (not grayed out)
- Capture when button is in its normal (not pressed) state
- For buildings, capture when visible on city view

==========================================
REQUIRED TEMPLATES (capture these first)
==========================================

NAVIGATION:
  map_btn.png               - The globe/map icon in city view (bottom bar)
  city_btn.png              - The city icon in map view (bottom bar)
  magnifier_btn.png         - Search/magnifier icon on map (top-right)

GATHER:
  gather_btn.png            - "Gather" button on resource tile popup
  dispatch_btn.png          - "Dispatch" or "March" button
  march_btn.png             - March confirmation button
  recall_march_btn.png      - Recall march button

FIGHT:
  attack_btn.png            - "Attack" button on Darkling info popup
  filter_darkling.png       - Darkling filter in search panel
  victory_text.png          - "Victory!" text on battle result screen
  defeat_text.png           - "Defeat" text on battle result screen
  wounded_indicator.png     - Red wounded troop indicator on city
  heal_all_btn.png          - "Heal All" button inside Hospital
  hospital_building.png     - Hospital building on city view

QUESTS & CLAIMS:
  quest_icon.png            - Quest scroll icon (usually top-left)
  quest_claim_btn.png       - Orange "Claim" reward button
  claim_all_quests_btn.png  - "Claim All" button in quest panel
  titans_legacy_icon.png    - Titan's Legacy event icon
  titan_chest_ready.png     - Chest when 6 daily challenges complete
  open_chest_btn.png        - "Open" chest button

ALLIANCE:
  alliance_btn.png          - Alliance flag button (bottom bar)
  territory_tab.png         - "Territory" tab in Alliance panel
  alliance_gifts_tab.png    - "Gifts" tab in Alliance panel
  help_all_btn.png          - "Help All" button in Alliance
  alliance_claim_all_btn.png - Claim All for territory resources

SHOP/MEMBERSHIP:
  shop_btn.png              - Shop/store icon button
  membership_tab.png        - "Honorary Membership" tab in shop
  membership_daily_claim_btn.png - Daily claim button in membership
  honor_shop_tab.png        - Honor/VIP shop tab

BUILDINGS:
  college_building.png      - College of Order building (city view)
  hall_of_order.png         - Hall of Order building (city view)
  alliance_center.png       - Alliance Center building
  goblin_market_building.png - Goblin Market building

RESEARCH:
  research_title.png        - Research screen header/title
  economy_tree_tab.png      - "Economy" tab in research screen
  military_tree_tab.png     - "Military" tab in research screen
  start_research_btn.png    - "Research" / "Start" button on research popup
  research_q1_empty.png     - Empty Queue 1 slot indicator
  research_q2_empty.png     - Empty Queue 2 slot indicator

BUILD:
  upgrade_btn.png           - Orange "Upgrade" button in building popup
  build_q1_empty.png        - Empty build slot 1 indicator
  confirm_btn.png           - "Confirm" / "OK" / "Yes" button
  popup_close.png           - "X" close button on popups
  popup_ok.png              - "OK" button on simple popups

GOBLIN MARKET:
  goblin_merchant_notification.png - Goblin arrival notification icon
  goblin_market_building.png - Goblin Market building
  visit_merchant_btn.png    - "Visit Merchant" button
  free_refresh_btn.png      - "Refresh" button (when it's free)
  confirm_buy_btn.png       - Buy confirmation button
  gems_cost_icon.png        - Gem diamond icon in cost display
  scrap_tab.png             - "Scrap" tab in Goblin Market

MAIL:
  mail_notification.png     - Mail icon with notification dot
  mail_icon.png             - Mail/envelope icon
  system_mail_tab.png       - "System" tab in mailbox
  claim_all_mail_btn.png    - Claim all mail rewards button

==========================================
OPTIONAL (for better accuracy)
==========================================

  search_confirm_btn.png    - Confirm/Search button after filter setup
  search_result_first.png   - First item in search results list
  sort_by_level_btn.png     - Sort by level button in search results
  darkling_key_drop.png     - Darkling Key item drop icon
  speedup_drop.png          - Speedup item drop icon
  mail_notification.png     - Red dot on mail icon
  alliance_gold_claim.png   - Gold resource claim in Alliance Territory
  alliance_wood_claim.png   - Wood resource claim
  alliance_ore_claim.png    - Ore resource claim
  alliance_mana_claim.png   - Mana resource claim

==========================================
HERO TEMPLATES (for gathering & combat)
==========================================
  hero_kella.png            - Kella hero portrait (Gold gathering)
  hero_pan.png              - Pan hero portrait (Wood gathering)
  hero_chakcha.png          - Chakcha hero portrait (Ore gathering)
  hero_indis.png            - Indis hero portrait (Mana gathering)
  hero_combat_slot.png      - First hero slot in combat dispatch screen
  remove_secondary_btn.png  - Remove secondary commander button
