#!/usr/bin/env python3
"""
main.py — CoD AutoBot Entry Point
Call of Dragons Automation Suite for BlueStacks

Usage:
    python main.py           # Launch GUI app
    python main.py --nogui   # Run bot headless (no GUI)
    python main.py --test    # Test ADB connection only

Requirements:
    pip install PyQt5 opencv-python Pillow

ADB Setup (BlueStacks):
    1. In BlueStacks settings → Advanced → Enable Android Debug Bridge (ADB)
    2. Download Android Platform Tools from developer.android.com
    3. Add adb to your PATH
    4. Run: adb connect 127.0.0.1:5555
    5. Run: adb devices  (should show 127.0.0.1:5555 as connected)
"""

import sys
import os
import json
import argparse

# Add project root to path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def load_config():
    path = os.path.join(ROOT, "config", "default_config.json")
    with open(path) as f:
        return json.load(f)


def run_gui():
    """Launch the PyQt5 GUI desktop app."""
    from gui.app import run_gui as _run_gui
    _run_gui()


def run_headless():
    """Run the bot without GUI (terminal only)."""
    import time
    from bot.scheduler import BotScheduler

    config = load_config()

    def log(msg):
        print(f"[BOT] {msg}")

    print("=" * 60)
    print("  CoD AutoBot — Headless Mode")
    print("  Call of Dragons • BlueStacks ADB")
    print("=" * 60)

    scheduler = BotScheduler(config, log_callback=log)

    if not scheduler.start():
        print("❌ Failed to start bot. Check ADB connection.")
        sys.exit(1)

    print("✅ Bot running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(30)
            stats = scheduler.get_stats()
            print(f"\n[STATS] Uptime: {stats['uptime']} | "
                  f"Gold: {stats['gold_gathered']:,} | "
                  f"Kills: {stats['kills']} | "
                  f"Research: {stats['current_research']}")
    except KeyboardInterrupt:
        print("\n⏹ Stopping bot...")
        scheduler.stop()
        print("Bot stopped.")


def test_adb():
    """Test ADB connection to BlueStacks."""
    from bot.adb import ADBController

    print("Testing ADB connection to BlueStacks...")
    adb = ADBController(log_callback=print)
    if adb.connect():
        print("✅ Connected!")
        print("Taking test screenshot...")
        img = adb.screenshot()
        if img is not None:
            import cv2
            cv2.imwrite("test_screenshot.png", img)
            print(f"✅ Screenshot saved: test_screenshot.png ({img.shape[1]}x{img.shape[0]})")
        else:
            print("❌ Screenshot failed")
        adb.disconnect()
    else:
        print("❌ Connection failed")
        print("\nTroubleshooting:")
        print("  1. Open BlueStacks → Settings → Advanced → Enable ADB")
        print("  2. Download Platform Tools: https://developer.android.com/tools/releases/platform-tools")
        print("  3. Add adb.exe to PATH")
        print("  4. Try: adb connect 127.0.0.1:5555")
        print("  5. Try port 5554 or 5037 if 5555 doesn't work")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoD AutoBot")
    parser.add_argument("--nogui",  action="store_true", help="Run headless (no GUI)")
    parser.add_argument("--test",   action="store_true", help="Test ADB connection only")
    args = parser.parse_args()

    if args.test:
        test_adb()
    elif args.nogui:
        run_headless()
    else:
        run_gui()
