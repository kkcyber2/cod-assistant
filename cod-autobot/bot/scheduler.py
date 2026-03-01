"""
scheduler.py — Main Bot Scheduler for CoD AutoBot
Orchestrates all task modules, manages timing, handles errors and reconnects.
"""

import time
import threading
import traceback
from typing import Dict, Callable, Optional

from bot.adb import ADBController
from bot.screen import ScreenDetector
from bot.gather import GatherModule
from bot.fight import FightModule
from bot.claim import ClaimModule
from bot.research import ResearchModule
from bot.build import BuildModule
from bot.goblin import GoblinModule


class BotScheduler:
    """
    Runs all bot modules in a single background thread.
    Cycle loop:
      Every ~30s  : Gather check (dispatch waiting march slots)
      Every ~3min : Fight cycle
      Every ~20min: Claim cycle
      Every ~5min : Research check
      Every ~10min: Build check
      Every ~1min : Goblin merchant check (notification-based)
      Continuous  : Anti-ban idle pauses, reconnect checks
    """

    MODULE_INTERVALS = {
        "gather":   30,    # seconds
        "fight":    180,
        "claim":    1200,
        "research": 300,
        "build":    600,
        "goblin":   60,
    }

    def __init__(self, config: dict, log_callback: Callable = None):
        self.config = config
        self.log = log_callback or print
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_run: Dict[str, float] = {}
        self._stats = {
            "session_start": None,
            "gold_gathered": 0,
            "kills": 0,
            "claimed": 0,
            "power": config.get("starting_power", 0),
            "errors": 0,
            "cycles": 0,
        }

        # Init ADB
        self.adb = ADBController(
            host=config.get("adb_host", "127.0.0.1"),
            port=config.get("adb_port", 5555),
            click_delay=config.get("click_delay", 0.35),
            random_offset=config.get("random_offset", 6),
            log_callback=self.log,
        )

        # Init Screen Detector
        self.screen = ScreenDetector(
            templates_dir=config.get("templates_dir", "templates"),
            threshold=config.get("match_threshold", 0.85),
            log_callback=self.log,
        )

        # Init modules
        self.modules: Dict[str, any] = {
            "gather":   GatherModule(self.adb, self.screen, config, self.log),
            "fight":    FightModule(self.adb, self.screen, config, self.log),
            "claim":    ClaimModule(self.adb, self.screen, config, self.log),
            "research": ResearchModule(self.adb, self.screen, config, self.log),
            "build":    BuildModule(self.adb, self.screen, config, self.log),
            "goblin":   GoblinModule(self.adb, self.screen, config, self.log),
        }

        # Apply enabled state from config
        for name, module in self.modules.items():
            if config.get(f"enable_{name}", True):
                module.enable()

    # ─────────────────────────── START / STOP ────────────────────────

    def start(self) -> bool:
        """Connect to BlueStacks and start the bot loop."""
        self.log("[Bot] 🐉 CoD AutoBot starting up...")

        if not self.adb.connect():
            self.log("[Bot] ❌ Cannot start — ADB connection failed")
            return False

        self._running = True
        self._stop_event.clear()
        self._stats["session_start"] = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="BotLoop")
        self._thread.start()
        self.log("[Bot] ✅ Bot loop started in background thread")
        return True

    def stop(self):
        """Stop the bot loop gracefully."""
        self.log("[Bot] ⏹ Stopping bot...")
        self._running = False
        self._stop_event.set()
        for module in self.modules.values():
            module.stop()
        if self._thread:
            self._thread.join(timeout=5)
        self.adb.disconnect()
        self.log("[Bot] Bot stopped.")

    def is_running(self) -> bool:
        return self._running and (self._thread is not None and self._thread.is_alive())

    # ─────────────────────────── MAIN LOOP ───────────────────────────

    def _loop(self):
        """Main bot execution loop — runs in background thread."""
        self.log("[Bot] 🔄 Main loop running...")

        while not self._stop_event.is_set():
            try:
                # Check ADB connection
                if not self.adb.is_alive():
                    self.log("[Bot] ⚠️ ADB disconnected — attempting reconnect...")
                    if not self.adb.reconnect():
                        self.log("[Bot] ❌ Reconnect failed — pausing 30s...")
                        self._stop_event.wait(30)
                        continue

                now = time.time()

                # Run modules based on their intervals
                for name, module in self.modules.items():
                    if self._stop_event.is_set():
                        break
                    if not module.enabled:
                        continue
                    interval = self.MODULE_INTERVALS.get(name, 60)
                    last = self._last_run.get(name, 0)
                    if now - last >= interval:
                        self._run_module(name, module)
                        self._last_run[name] = time.time()

                # Anti-ban: random idle pause
                self._anti_ban_pause()

                self._stats["cycles"] += 1

                # Short sleep between cycle iterations
                self._stop_event.wait(5)

            except Exception as e:
                self._stats["errors"] += 1
                self.log(f"[Bot] ❌ Loop error: {e}")
                self.log(traceback.format_exc())
                self._stop_event.wait(10)

        self.log("[Bot] Loop exited.")

    def _run_module(self, name: str, module):
        """Run a single module with error catching."""
        try:
            module.run_once()
        except Exception as e:
            self._stats["errors"] += 1
            self.log(f"[Bot] ❌ Error in module '{name}': {e}")
            # Try to recover to city view
            try:
                self.adb.press_back()
                time.sleep(1)
            except:
                pass

    def _anti_ban_pause(self):
        """
        Randomly pause the bot to appear human-like.
        Pauses 2-8 seconds every ~10 cycles.
        """
        if self._stats["cycles"] % 10 == 0:
            pause = 2 + (self._stats["cycles"] % 7)
            self._stop_event.wait(pause)

    # ─────────────────────────── MODULE CONTROL ──────────────────────

    def enable_module(self, name: str):
        if name in self.modules:
            self.modules[name].enable()
            self.log(f"[Bot] ✅ Module enabled: {name}")

    def disable_module(self, name: str):
        if name in self.modules:
            self.modules[name].disable()
            self.log(f"[Bot] ⏸ Module disabled: {name}")

    def toggle_module(self, name: str, enabled: bool):
        if enabled:
            self.enable_module(name)
        else:
            self.disable_module(name)

    # ─────────────────────────── STATS ───────────────────────────────

    def get_stats(self) -> dict:
        stats = dict(self._stats)
        if stats["session_start"]:
            elapsed = time.time() - stats["session_start"]
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            s = int(elapsed % 60)
            stats["uptime"] = f"{h:02d}:{m:02d}:{s:02d}"
        else:
            stats["uptime"] = "00:00:00"
        stats["enabled_modules"] = [n for n, m in self.modules.items() if m.enabled]
        stats["research_progress"] = self.modules["research"].get_progress_pct()
        stats["current_research"] = self.modules["research"].get_current_research_name()
        return stats

    def update_config(self, new_config: dict):
        """Update config at runtime (e.g. from GUI settings change)."""
        self.config.update(new_config)
        self.adb.click_delay = new_config.get("click_delay", self.adb.click_delay)
        self.adb.random_offset = new_config.get("random_offset", self.adb.random_offset)
        self.screen.threshold = new_config.get("match_threshold", self.screen.threshold)
        for name, module in self.modules.items():
            module.config.update(new_config)
        self.log("[Bot] ⚙️ Config updated at runtime")
