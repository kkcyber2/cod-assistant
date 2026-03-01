# 🐉 CoD AutoBot — Call of Dragons Automation Suite

Complete automation bot for **Call of Dragons** (by Farlight Games) running on **BlueStacks**.

---

## 📁 Project Structure

```
cod-autobot/
├── main.py                    ← Entry point (run this)
├── requirements.txt           ← Python dependencies
│
├── bot/
│   ├── adb.py                 ← ADB connection (BlueStacks comms)
│   ├── screen.py              ← OpenCV image detection engine
│   ├── base_module.py         ← Base class all modules inherit from
│   ├── gather.py              ← Auto Gather (Gold/Wood/Ore/Mana nodes)
│   ├── fight.py               ← Auto Fight (Darkling hunting)
│   ├── claim.py               ← Auto Claim (all daily rewards)
│   ├── research.py            ← Auto Research (economy-first tree)
│   ├── build.py               ← Auto Build (Hall of Order priority)
│   ├── goblin.py              ← Goblin Market buyer
│   └── scheduler.py           ← Orchestrates all modules
│
├── gui/
│   └── app.py                 ← PyQt5 Desktop GUI application
│
├── templates/                 ← PNG screenshots of buttons (YOU ADD THESE)
│   └── README_templates.txt   ← Instructions for capturing templates
│
├── config/
│   └── default_config.json    ← All bot settings
│
└── logs/                      ← Bot activity logs (auto-created)
```

---

## ⚡ Quick Setup

### Step 1 — Install Python
Download Python 3.10+ from https://python.org

### Step 2 — Install Dependencies
```bash
cd cod-autobot
pip install -r requirements.txt
```

### Step 3 — Setup BlueStacks ADB
1. Open BlueStacks
2. Go to **Settings → Advanced → Android Debug Bridge (ADB)** → Enable it
3. Note the ADB port shown (usually **5555**)

### Step 4 — Install Android Platform Tools (ADB)
1. Download from: https://developer.android.com/tools/releases/platform-tools
2. Extract the zip
3. Add the folder to your system **PATH**
4. Test: open terminal and run `adb version`

### Step 5 — Connect ADB
```bash
adb connect 127.0.0.1:5555
adb devices
# Should show: 127.0.0.1:5555   device
```

### Step 6 — Add Button Templates (CRITICAL)
The bot uses **image matching** to find buttons on screen.
You need to provide screenshots of the buttons it looks for.

```bash
# Test ADB and take a screenshot first
python main.py --test
# This saves test_screenshot.png — open it and crop button images
```

See `templates/README_templates.txt` for the full list of templates needed.

### Step 7 — Launch the Bot
```bash
# GUI mode (recommended)
python main.py

# Headless mode (no GUI)
python main.py --nogui

# Test ADB only
python main.py --test
```

---

## 🖼️ Templates — How to Add Them

Templates are small PNG screenshots of UI buttons the bot needs to recognize.

**How to capture a template:**
1. Run `python main.py --test` → saves `test_screenshot.png`
2. Open the screenshot in Paint / Photoshop / any editor
3. Crop tightly around the button/icon you want
4. Save as `templates/button_name.png`

**Required templates (start with these):**
```
templates/
├── map_btn.png               ← The map/globe icon button
├── magnifier_btn.png         ← Search/magnifier button on map
├── gather_btn.png            ← "Gather" button on resource tile popup
├── dispatch_btn.png          ← "Dispatch" / "March" button
├── march_btn.png             ← March confirmation button
├── attack_btn.png            ← "Attack" button on Darkling popup
├── quest_icon.png            ← Quest scroll icon (top-left)
├── quest_claim_btn.png       ← Orange "Claim" button on quests
├── alliance_btn.png          ← Alliance flag button
├── college_building.png      ← College of Order building
├── hall_of_order.png         ← Hall of Order building
├── hospital_building.png     ← Hospital building
├── upgrade_btn.png           ← Orange "Upgrade" button
├── confirm_btn.png           ← "Confirm" / "OK" button
├── popup_close.png           ← X close button on popups
├── heal_all_btn.png          ← "Heal All" button in hospital
├── research_title.png        ← Research screen title
├── start_research_btn.png    ← "Research" start button
├── goblin_merchant_notification.png ← Goblin arrival indicator
```

**Pro tip:** Set BlueStacks to **1920×1080** resolution before capturing templates.
Settings → Display → Resolution → 1920×1080

---

## ⚙️ Configuration

Edit `config/default_config.json` or use the GUI Settings tab:

```json
{
  "adb_host": "127.0.0.1",
  "adb_port": 5555,

  "click_delay": 0.35,       // seconds between actions
  "random_offset": 6,        // pixel randomness on clicks
  "match_threshold": 0.85,   // image match sensitivity (0.5-1.0)
  "anti_ban": true,

  "enable_gather": true,
  "gather_marches": 5,
  "gather_mode": "smart",    // smart / gold_priority / wood_priority
  "gather_min_level": 3,

  "enable_fight": true,
  "fight_min_level": 8,
  "fight_max_level": 20,

  "enable_research": true,
  "research_focus": "economy_first"
}
```

---

## 🧠 How It Works

```
1. ADB connects to BlueStacks (port 5555)
       ↓
2. Screenshot taken via: adb exec-out screencap -p
       ↓
3. OpenCV scans screenshot for known button templates
   e.g. "gather_btn.png" found at (850, 440) with 94% confidence
       ↓
4. Bot taps: adb shell input tap 850 440
       ↓
5. Wait → screenshot → repeat cycle
```

The scheduler runs all modules on a rotating timer:
- **Gather**: check every 30 seconds
- **Fight**: run every 3 minutes
- **Claim**: check every 20 minutes
- **Research**: check every 5 minutes
- **Build**: check every 10 minutes
- **Goblin Market**: check every 60 seconds (notification-based)

---

## ⚠️ Important Notes

1. **Templates are required** — the bot cannot click buttons it cannot see
2. **Resolution must match** — capture templates at same resolution as bot runs
3. **Keep BlueStacks in foreground** or use ADB screenshot (works in background)
4. **Anti-Ban mode** adds random delays and pauses to avoid detection
5. **Never run during alliance wars/KvK** — you could accidentally attack allies

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `adb not found` | Add Platform Tools folder to PATH |
| `Connection refused` | Enable ADB in BlueStacks settings |
| `Screenshot is None` | Check `adb devices` shows device |
| `Button not found` | Recapture template at current resolution |
| Bot clicks wrong spots | Set BlueStacks to 1920×1080 |
| Low match rate | Lower `match_threshold` to 0.75 |

---

## 📋 Research Priority (Built-In)

The bot follows this order automatically:

**Economy (do first):**
Architecture I&II → Scholarship I&II → Stamina I&II → Logging → Ore → Gold Processing ×5 → Gold Mining ×5 → Mana Prospering → Container Upgrade

**Military (minimum for T4):**
Conscription I&II → Military Leadership I → Intelligence Gathering (5/5) → Pathfinding 2 (7/10 only) → T4 unlock

**Rule:** Never max Military before finishing Economy tree.

---

*Made for Call of Dragons by Farlight Games*
*Use responsibly. Game TOS applies.*
