"""
gui/app.py — CoD AutoBot Desktop GUI Application
Full PyQt5 GUI that controls the bot scheduler, shows live logs, stats, and settings.
Run with: python main.py
"""

import sys
import os
import json
import time
import threading
import queue
from datetime import datetime

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QTabWidget, QTextEdit, QSpinBox, QDoubleSpinBox,
        QCheckBox, QComboBox, QGroupBox, QGridLayout, QProgressBar,
        QFrame, QScrollArea, QSplitter, QStatusBar, QLineEdit, QSlider,
        QSystemTrayIcon, QMenu, QAction, QSizePolicy
    )
    from PyQt5.QtCore import (
        Qt, QTimer, pyqtSignal, QObject, QThread, QSize
    )
    from PyQt5.QtGui import (
        QFont, QColor, QPalette, QIcon, QTextCursor, QPixmap
    )
    PYQT5_OK = True
except ImportError:
    PYQT5_OK = False
    print("PyQt5 not installed. Run: pip install PyQt5")

# ─────────────────────────── THEME ───────────────────────────────────

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #0a0d13;
    color: #c0d0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #1c2d3d;
    background: #0c1018;
    border-radius: 6px;
}
QTabBar::tab {
    background: #0c1018;
    color: #5a7a8a;
    padding: 8px 18px;
    border: 1px solid #1c2d3d;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QTabBar::tab:selected {
    background: #111820;
    color: #c8860a;
    border-color: #c8860a;
}
QTabBar::tab:hover:!selected {
    background: #111820;
    color: #c0d0e0;
}
QPushButton {
    background: #1a2535;
    border: 1px solid #2a3a4a;
    border-radius: 5px;
    color: #c0d0e0;
    padding: 7px 16px;
    font-weight: 600;
}
QPushButton:hover { background: #243040; border-color: #c8860a; color: #f0f0f0; }
QPushButton:pressed { background: #1a2030; }
QPushButton#startBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c8860a, stop:1 #f5a020);
    border: none; color: #000; font-size: 13px; font-weight: 800;
    padding: 10px 28px; letter-spacing: 1px;
}
QPushButton#startBtn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e09010, stop:1 #ffb030); }
QPushButton#stopBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c03030, stop:1 #e04040);
    border: none; color: #fff; font-weight: 800; padding: 10px 28px;
}
QPushButton#greenBtn {
    background: rgba(34,197,94,0.1); border: 1px solid #22c55e;
    color: #22c55e; font-weight: 700;
}
QPushButton#greenBtn:hover { background: rgba(34,197,94,0.2); }
QPushButton#redBtn {
    background: rgba(220,50,50,0.1); border: 1px solid #e04040;
    color: #e04040; font-weight: 700;
}
QPushButton#redBtn:hover { background: rgba(220,50,50,0.2); }
QGroupBox {
    border: 1px solid #1c2d3d;
    border-radius: 8px;
    margin-top: 10px;
    padding: 12px;
    font-weight: 700;
    color: #c8860a;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QCheckBox { spacing: 8px; color: #c0d0e0; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #2a3a4a; background: #111820; }
QCheckBox::indicator:checked { background: #22c55e; border-color: #22c55e; }
QCheckBox::indicator:hover { border-color: #c8860a; }
QComboBox {
    background: #111820; border: 1px solid #2a3a4a; border-radius: 4px;
    color: #c0d0e0; padding: 5px 10px;
}
QComboBox:hover { border-color: #c8860a; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #111820; border: 1px solid #2a3a4a; color: #c0d0e0; selection-background-color: #1a2d3d; }
QSpinBox, QDoubleSpinBox, QLineEdit {
    background: #111820; border: 1px solid #2a3a4a; border-radius: 4px;
    color: #c0d0e0; padding: 5px 8px;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border-color: #c8860a; }
QTextEdit {
    background: #050810; border: 1px solid #1c2d3d; border-radius: 5px;
    color: #a0c0a0; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;
}
QScrollBar:vertical { background: #0a0d13; width: 6px; }
QScrollBar::handle:vertical { background: #1c2d3d; border-radius: 3px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #2a3a4a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QProgressBar { background: #111820; border: 1px solid #1c2d3d; border-radius: 4px; height: 6px; text-align: center; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c8860a, stop:1 #f5a020); border-radius: 3px; }
QLabel#statValue { color: #f5c842; font-family: 'Consolas', monospace; font-size: 18px; font-weight: 900; }
QLabel#statLabel { color: #5a7a8a; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
QFrame#divider { background: #1c2d3d; max-height: 1px; }
QStatusBar { background: #060a0e; border-top: 1px solid #1c2d3d; color: #5a7a8a; font-size: 11px; }
"""


# ─────────────────────────── LOG SIGNAL ──────────────────────────────

class LogSignalEmitter(QObject):
    new_log = pyqtSignal(str, str)  # (level, message)


# ─────────────────────────── STAT CARD ───────────────────────────────

class StatCard(QFrame):
    def __init__(self, icon: str, label: str, value: str = "0", color: str = "#f5c842"):
        super().__init__()
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{
                background: #0d1520;
                border: 1px solid #1c2d3d;
                border-top: 2px solid {color};
                border-radius: 8px;
                padding: 4px;
            }}
            QFrame:hover {{ border-color: {color}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)

        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("font-size: 22px; background: transparent; border: none;")

        self.val_lbl = QLabel(value)
        self.val_lbl.setObjectName("statValue")
        self.val_lbl.setAlignment(Qt.AlignCenter)
        self.val_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 900; font-family: Consolas; background: transparent; border: none;")

        self.lbl = QLabel(label)
        self.lbl.setObjectName("statLabel")
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet("color: #5a7a8a; font-size: 10px; background: transparent; border: none;")

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.val_lbl)
        layout.addWidget(self.lbl)

    def set_value(self, v: str):
        self.val_lbl.setText(v)


# ─────────────────────────── MODULE TOGGLE ROW ───────────────────────

class ModuleRow(QFrame):
    toggled = pyqtSignal(str, bool)

    def __init__(self, module_id: str, icon: str, name: str, desc: str, enabled: bool = True):
        super().__init__()
        self.module_id = module_id
        self.setStyleSheet("""
            QFrame { background: #0d1520; border: 1px solid #1c2d3d; border-radius: 6px; padding: 4px; }
            QFrame:hover { border-color: #243040; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px; min-width: 28px; background: transparent; border: none;")

        info = QVBoxLayout()
        name_lbl = QLabel(f"<b>{name}</b>")
        name_lbl.setStyleSheet("color: #e0f0ff; font-size: 13px; background: transparent; border: none;")
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("color: #5a7a8a; font-size: 11px; background: transparent; border: none;")
        info.addWidget(name_lbl)
        info.addWidget(desc_lbl)

        self.status_lbl = QLabel("● IDLE")
        self.status_lbl.setStyleSheet("color: #5a7a8a; font-size: 11px; font-family: Consolas; background: transparent; border: none; min-width: 80px;")

        self.toggle = QCheckBox()
        self.toggle.setChecked(enabled)
        self.toggle.stateChanged.connect(lambda s: self.toggled.emit(module_id, bool(s)))

        layout.addWidget(icon_lbl)
        layout.addLayout(info, 1)
        layout.addWidget(self.status_lbl)
        layout.addWidget(self.toggle)

    def set_running(self, running: bool):
        if running:
            self.status_lbl.setText("● RUNNING")
            self.status_lbl.setStyleSheet("color: #22c55e; font-size: 11px; font-family: Consolas; background: transparent; border: none;")
            self.setStyleSheet("QFrame { background: #0a1a10; border: 1px solid rgba(34,197,94,0.4); border-radius: 6px; padding: 4px; }")
        else:
            self.status_lbl.setText("● IDLE")
            self.status_lbl.setStyleSheet("color: #5a7a8a; font-size: 11px; font-family: Consolas; background: transparent; border: none;")
            self.setStyleSheet("QFrame { background: #0d1520; border: 1px solid #1c2d3d; border-radius: 6px; padding: 4px; } QFrame:hover { border-color: #243040; }")


# ─────────────────────────── MAIN WINDOW ─────────────────────────────

class CoDAutoBotWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.config = self._load_config()
        self.scheduler = None
        self._bot_running = False
        self._log_queue = queue.Queue()
        self._signal = LogSignalEmitter()
        self._signal.new_log.connect(self._append_log)
        self._module_rows = {}

        self.setWindowTitle("🐉 CoD AutoBot — Call of Dragons")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)
        self.setStyleSheet(DARK_STYLE)

        self._build_ui()

        # Stats refresh timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_stats)
        self._timer.start(2000)

        self._log("info", "🐉 CoD AutoBot v2.0 initialized")
        self._log("info", "Platform: BlueStacks • ADB 127.0.0.1:5555")
        self._log("info", "Press START BOT to begin automation")

    # ─────────────────────────── UI BUILD ────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        root.addWidget(self._build_header())

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background: #1c2d3d; }")

        # Left: tabs
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._tab_dashboard(),  "🏠  Dashboard")
        tabs.addTab(self._tab_modules(),    "⚙️  Modules")
        tabs.addTab(self._tab_gather(),     "⛏️  Gather")
        tabs.addTab(self._tab_fight(),      "⚔️  Fight")
        tabs.addTab(self._tab_claim(),      "🎁  Claim")
        tabs.addTab(self._tab_research(),   "🔬  Research")
        tabs.addTab(self._tab_build(),      "🏰  Build")
        tabs.addTab(self._tab_goblin(),     "🟢  Goblin")
        tabs.addTab(self._tab_settings(),   "⚙️  Settings")
        splitter.addWidget(tabs)

        # Right: live log + resource panel
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)
        right_layout.addWidget(self._build_resource_panel())
        right_layout.addWidget(self._build_log_panel(), 1)
        splitter.addWidget(right)

        splitter.setSizes([780, 380])
        root.addWidget(splitter, 1)

        # Status bar
        self.statusBar().showMessage("Bot Idle  •  BlueStacks ADB: 127.0.0.1:5555  •  Ready")

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet("""
            QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(200,134,10,0.12), stop:0.5 rgba(10,13,20,0),
                stop:1 rgba(0,200,184,0.05));
                border-bottom: 1px solid #1c2d3d; }
        """)
        header.setFixedHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo
        logo_lbl = QLabel("🐉")
        logo_lbl.setStyleSheet("font-size: 30px;")
        title_lbl = QLabel("<span style='font-family:Segoe UI;font-size:16px;font-weight:900;color:#e0f0ff;letter-spacing:2px;'>CoD AutoBot</span><br><span style='font-size:9px;color:#c8860a;letter-spacing:3px;'>CALL OF DRAGONS • FARLIGHT GAMES</span>")
        title_lbl.setStyleSheet("background: transparent;")

        layout.addWidget(logo_lbl)
        layout.addWidget(title_lbl)
        layout.addStretch()

        # Status indicators
        self.conn_lbl = QLabel("⬤  DISCONNECTED")
        self.conn_lbl.setStyleSheet("color: #e04040; font-family: Consolas; font-size: 11px; background: transparent; padding: 5px 12px; border: 1px solid #2a2020; border-radius: 15px; background: #1a0a0a;")

        self.uptime_lbl = QLabel("⏱  00:00:00")
        self.uptime_lbl.setStyleSheet("font-family: Consolas; font-size: 11px; background: #0d1520; padding: 5px 12px; border: 1px solid #1c2d3d; border-radius: 15px; color: #c0d0e0;")

        self.power_lbl = QLabel("⚡  Power: --")
        self.power_lbl.setStyleSheet("font-family: Consolas; font-size: 11px; color: #f5c842; background: #0d1520; padding: 5px 12px; border: 1px solid #1c2d3d; border-radius: 15px;")

        self.start_btn = QPushButton("▶  START BOT")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setFixedHeight(38)
        self.start_btn.clicked.connect(self._toggle_bot)

        layout.addWidget(self.conn_lbl)
        layout.addWidget(self.uptime_lbl)
        layout.addWidget(self.power_lbl)
        layout.addWidget(self.start_btn)
        return header

    # ─────────────────────────── TABS ────────────────────────────────

    def _tab_dashboard(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Stats row
        stats_row = QHBoxLayout()
        self.stat_power    = StatCard("⚡", "Total Power",      "--",  "#f5c842")
        self.stat_gold     = StatCard("🪙", "Gold Gathered",    "0",   "#c8860a")
        self.stat_kills    = StatCard("⚔️", "Darklings Killed", "0",   "#e04040")
        self.stat_claimed  = StatCard("🎁", "Rewards Claimed",  "0",   "#00c8b8")
        self.stat_research = StatCard("🔬", "Research Done",    "0",   "#a855f7")
        for s in [self.stat_power, self.stat_gold, self.stat_kills, self.stat_claimed, self.stat_research]:
            stats_row.addWidget(s)
        layout.addLayout(stats_row)

        # Research progress
        rg = QGroupBox("🔬  RESEARCH PROGRESS")
        rgl = QVBoxLayout(rg)
        self.research_lbl = QLabel("Next: Architecture I")
        self.research_lbl.setStyleSheet("color: #c8860a; font-size: 12px;")
        self.research_bar = QProgressBar()
        self.research_bar.setValue(0)
        rgl.addWidget(self.research_lbl)
        rgl.addWidget(self.research_bar)
        layout.addWidget(rg)

        # Quick module toggles
        mg = QGroupBox("⚡  QUICK MODULE CONTROL")
        mgl = QVBoxLayout(mg)
        hb = QHBoxLayout()
        ea = QPushButton("Enable All")
        ea.setObjectName("greenBtn")
        ea.clicked.connect(self._enable_all)
        da = QPushButton("Disable All")
        da.setObjectName("redBtn")
        da.clicked.connect(self._disable_all)
        hb.addWidget(ea)
        hb.addWidget(da)
        hb.addStretch()
        mgl.addLayout(hb)

        modules_def = [
            ("gather",   "⛏️", "Auto Gather",       "Sends legions to Gold/Wood/Ore/Mana nodes"),
            ("fight",    "⚔️", "Auto Fight",         "Hunts Darklings for Gold, Prestige, Keys"),
            ("claim",    "🎁", "Auto Claim",         "Claims quests, alliance RSS, membership, chests"),
            ("research", "🔬", "Auto Research",      "Economy-first research, never idles queue"),
            ("build",    "🏰", "Auto Build",         "Hall→Alliance→College→Hospitals priority order"),
            ("goblin",   "🟢", "Goblin Market",      "Buys speedups & hero tokens, skips bad deals"),
        ]
        grid = QGridLayout()
        for i, (mid, icon, name, desc) in enumerate(modules_def):
            row_widget = ModuleRow(mid, icon, name, desc, self.config.get(f"enable_{mid}", True))
            row_widget.toggled.connect(self._on_module_toggled)
            self._module_rows[mid] = row_widget
            grid.addWidget(row_widget, i // 2, i % 2)
        mgl.addLayout(grid)
        layout.addWidget(mg)

        layout.addStretch()
        w.setWidget(inner)
        return w

    def _tab_modules(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addWidget(QLabel("<b>All modules and their current status.</b> Enable/disable individually."))
        # Re-use same module rows from dashboard (just rebuild them)
        modules_def = [
            ("gather",   "⛏️", "Auto Gather",
             "Dispatches up to 5 march slots to Gold Mines, Wood nodes, Ore nodes, and Mana nodes. Uses Kella (Gold), Pan (Wood), Chakcha (Ore), Indis (Mana). Stays in Alliance territory for +25% speed. Single commander mode enabled."),
            ("fight",    "⚔️", "Auto Fight",
             "Hunts Darkling Legions Lv.8-20. Each kill yields Gold, Prestige, Hero XP, and a chance for Darkling Keys (used to open Dark Chests). Auto-heals wounded troops. Pursues Lv.15+ targets for max Prestige (needed to enact Policies)."),
            ("claim",    "🎁", "Auto Claim",
             "Claims: Daily Quests, Side Quests, Titan's Legacy chest (6 daily challenges → Rune EXP + Keys), Alliance Territory resources (Gold/Wood/Ore/Mana), Alliance Gift Bags, Alliance Helps, Membership daily reward, Membership shop weekly items (CP tokens, speedups, medals — resources only), Mailbox rewards."),
            ("research", "🔬", "Auto Research",
             "Follows priority: Architecture I&II → Scholarship I&II → Stamina → Logging/Ore/Gold techs → Mana Prospering → T4 minimum path. Never leaves queue empty. Uses 2nd queue at Honor Lv.8. College of Order upgrades only with instant-speedup."),
            ("build",    "🏰", "Auto Build",
             "Priority: Hall of Order → Alliance Center → College of Order → All 4 Hospitals → Barracks/Stables/Arcane/Aviary → Mints → Lumber Mills/Ore Pits/Mana Wells → Goblin Market (ASAP at Hall Lv.6). Waits for alliance helps before starting expensive upgrades."),
            ("goblin",   "🟢", "Goblin Market",
             "Always buys speedups. Buys Epic/Legendary hero tokens at ≥25% off. Buys resource boosts only at ≥50% off. Buys Gems-cost items only at ≥60% off. Never buys Gold for Gems. Only uses 1 free refresh per visit. Scraps duplicate items for Universal Tokens."),
        ]
        for mid, icon, name, desc in modules_def:
            g = QGroupBox(f"{icon}  {name.upper()}")
            gl = QVBoxLayout(g)
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color: #8098a8; font-size: 11px;")
            cb = QCheckBox("Enabled")
            cb.setChecked(self.config.get(f"enable_{mid}", True))
            cb.stateChanged.connect(lambda s, m=mid: self._on_module_toggled(m, bool(s)))
            gl.addWidget(desc_lbl)
            gl.addWidget(cb)
            layout.addWidget(g)
        layout.addStretch()
        w.setWidget(inner)
        return w

    def _tab_gather(self) -> QWidget:
        return self._settings_tab("gather", [
            ("gather_marches",        "March Slots",                  "spin",    1, 5,    1),
            ("gather_mode",           "Gathering Mode",               "combo",
             ["smart", "gold_priority", "wood_priority", "ore_priority", "mana_priority"]),
            ("gather_min_level",      "Min Node Level",               "spin",    1, 6,    1),
            ("gather_alliance_only",  "Alliance Territory Only (+25% speed)", "check"),
            ("gather_single_commander","Use Single Commander (max efficiency)", "check"),
            ("gather_mana",           "Gather Mana (needs Mana Prospering tech)", "check"),
        ], info="Best gathering heroes: Kella (Gold), Pan (Wood), Chakcha (Ore), Indis (Mana).\nAlways gather in Alliance Territory for +25% speed bonus.")

    def _tab_fight(self) -> QWidget:
        return self._settings_tab("fight", [
            ("fight_target",        "Target Type",    "combo",
             ["darkling_legion", "darkling_guard", "darkling_fort", "behemoth"]),
            ("fight_min_level",     "Min Level",      "spin",  1,  30, 1),
            ("fight_max_level",     "Max Level",      "spin",  1,  30, 1),
            ("fight_auto_heal",     "Auto Heal Troops Before Fighting", "check"),
            ("fight_prestige_mode", "Prestige Mode (target Lv.15+ for max Prestige)", "check"),
            ("fight_max_loss_pct",  "Stop if Troop Loss > (%)", "spin", 1, 50, 1),
            ("fight_collect_keys",  "Collect Darkling Keys & Open Dark Chests", "check"),
        ], info="Darkling Lv.15+ = +720 Prestige per kill. Use Prestige to enact policies.\nMilitary Expansion policy is most important — adds 400-600 troops to legion size.")

    def _tab_claim(self) -> QWidget:
        return self._settings_tab("claim", [
            ("claim_daily_quests",    "Daily & Side Quest Rewards",   "check"),
            ("claim_titan_chest",     "Titan's Legacy Chest (6 daily challenges → Rune EXP)", "check"),
            ("claim_alliance_rss",    "Alliance Territory Resources (Gold/Wood/Ore/Mana)", "check"),
            ("claim_alliance_gifts",  "Alliance Gift Bags",           "check"),
            ("claim_alliance_helps",  "Alliance Helps (help all members)", "check"),
            ("claim_membership",      "Honorary Membership Daily Reward", "check"),
            ("claim_membership_shop", "Membership Shop Weekly Items (CP tokens, speedups, medals)", "check"),
            ("claim_mail",            "Mailbox System Rewards",       "check"),
            ("claim_interval_mins",   "Check Interval (minutes)",     "spin", 5, 120, 5),
        ], info="Membership Shop resets every Monday 0:00 UTC.\nOnly buys items costing resources (Gold/Wood/Ore), never Gems.")

    def _tab_research(self) -> QWidget:
        return self._settings_tab("research", [
            ("research_focus",        "Research Focus",  "combo",
             ["economy_first", "military_first", "balanced"]),
            ("research_second_queue", "Use 2nd Research Queue (requires Honor Lv.8 = 35k Gems)", "check"),
            ("research_wait_helps",   "Wait for Alliance Helps Before Starting", "check"),
        ], info="Priority order:\n"
                "ECONOMY: Architecture I&II → Scholarship I&II → Stamina → Logging → Ore → Gold Processing (x5) → Gold Mining (x5) → Mana Prospering → Container Upgrade\n"
                "MILITARY: Conscription I&II → Military Leadership I → Intelligence Gathering (5/5) → Pathfinding 2 (7/10 ONLY) → T4 Infantry/Mounted/Marksmen/Magic\n"
                "RULE: Never max Military before Economy. T4 unlock = first military goal.")

    def _tab_build(self) -> QWidget:
        return self._settings_tab("build", [
            ("build_mode",            "Build Mode",      "combo",
             ["priority_list", "hall_only", "hall_and_research"]),
            ("build_wait_helps",      "Wait for Alliance Helps Before Upgrading", "check"),
            ("build_instant_college", "Use Speedups to Finish College of Order Upgrades Instantly", "check"),
        ], info="Priority order:\n"
                "1. Hall of Order (controls ALL unlocks — always upgrade first)\n"
                "2. Alliance Center (more helps = time saved forever)\n"
                "3. College of Order (research speed — ONLY upgrade with speedups, never let it sit)\n"
                "4. All 4 Hospitals (high power + troop protection)\n"
                "5. Barracks / Stables / Arcane Tower / Aviary (troop bonuses)\n"
                "6. Mints (passive Gold)\n"
                "7. Goblin Market (build ASAP at Hall Lv.6)")

    def _tab_goblin(self) -> QWidget:
        return self._settings_tab("goblin", [
            ("goblin_free_refresh_only", "Use Only 1 Free Refresh (no Gem refreshes)", "check"),
        ], info="BUY RULES:\n"
                "✅ Always buy: ALL Speedups (any discount)\n"
                "✅ Buy: Epic/Legendary Hero Tokens at ≥25% off\n"
                "⚡ Buy: Resource items only at ≥50% off (resources cost, not Gems)\n"
                "⚡ Buy: Ore/resources for Gems only at ≥60% off\n\n"
                "NEVER BUY:\n"
                "❌ Gold with Gems (terrible value)\n"
                "❌ Resource bundles at <25% discount\n"
                "❌ Multiple merchant refreshes with Gems\n\n"
                "♻️ SCRAP: Duplicate hero tokens → Universal Tokens (use on any hero)\n"
                "♻️ SCRAP: Duplicate artifacts → Artifact Tokens")

    def _tab_settings(self) -> QWidget:
        return self._settings_tab("bot", [
            ("adb_host",        "ADB Host",                    "text",   "127.0.0.1"),
            ("adb_port",        "ADB Port (BlueStacks: 5555)", "spin",   5554, 5565, 1),
            ("click_delay",     "Click Delay (seconds)",       "dspin",  0.1, 2.0, 0.05),
            ("random_offset",   "Random Click Offset (pixels)", "spin",  0, 20, 1),
            ("match_threshold", "Image Match Threshold (0-1)", "dspin",  0.5, 1.0, 0.05),
            ("anti_ban",        "Anti-Ban Mode (randomize timing)", "check"),
            ("night_mode",      "Night Mode (pause 12am-6am)", "check"),
            ("auto_reconnect",  "Auto Reconnect on Disconnect", "check"),
        ], info="Anti-Ban mode: randomizes click timing and adds idle pauses every 10 cycles.\n"
                "Image Match Threshold: 0.85 recommended. Lower = more lenient but more false positives.\n"
                "Click Delay: 0.35s recommended. Too fast looks like a bot.")

    # ─────────────────────────── SETTINGS TAB BUILDER ────────────────

    def _settings_tab(self, prefix: str, fields: list, info: str = "") -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        if info:
            info_lbl = QLabel(info)
            info_lbl.setWordWrap(True)
            info_lbl.setStyleSheet("""
                background: rgba(68,136,255,0.07); border: 1px solid rgba(68,136,255,0.3);
                border-radius: 6px; color: #7aabff; font-size: 11px; padding: 10px;
            """)
            layout.addWidget(info_lbl)

        for field in fields:
            key = field[0]
            label = field[1]
            ftype = field[2]

            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setMinimumWidth(320)
            row.addWidget(lbl)

            widget = None
            if ftype == "check":
                widget = QCheckBox()
                widget.setChecked(bool(self.config.get(key, True)))
                widget.stateChanged.connect(lambda s, k=key: self._save_config_value(k, bool(s)))

            elif ftype == "spin":
                widget = QSpinBox()
                widget.setRange(field[3], field[4])
                widget.setSingleStep(field[5])
                widget.setValue(int(self.config.get(key, field[3])))
                widget.setFixedWidth(90)
                widget.valueChanged.connect(lambda v, k=key: self._save_config_value(k, v))

            elif ftype == "dspin":
                widget = QDoubleSpinBox()
                widget.setRange(field[3], field[4])
                widget.setSingleStep(field[5])
                widget.setValue(float(self.config.get(key, field[3])))
                widget.setDecimals(2)
                widget.setFixedWidth(90)
                widget.valueChanged.connect(lambda v, k=key: self._save_config_value(k, v))

            elif ftype == "combo":
                widget = QComboBox()
                options = field[3]
                for opt in options:
                    widget.addItem(opt)
                cur = self.config.get(key, options[0])
                if cur in options:
                    widget.setCurrentIndex(options.index(cur))
                widget.currentTextChanged.connect(lambda v, k=key: self._save_config_value(k, v))

            elif ftype == "text":
                widget = QLineEdit()
                widget.setText(str(self.config.get(key, field[3])))
                widget.setFixedWidth(150)
                widget.textChanged.connect(lambda v, k=key: self._save_config_value(k, v))

            if widget:
                row.addWidget(widget)
                row.addStretch()
            layout.addLayout(row)

            # Divider
            div = QFrame()
            div.setObjectName("divider")
            div.setFrameShape(QFrame.HLine)
            div.setStyleSheet("background: #1c2d3d;")
            layout.addWidget(div)

        # Save button
        save_btn = QPushButton("💾  Save Settings")
        save_btn.setObjectName("greenBtn")
        save_btn.clicked.connect(self._save_config_to_file)
        layout.addWidget(save_btn)
        layout.addStretch()
        w.setWidget(inner)
        return w

    # ─────────────────────────── RIGHT PANELS ────────────────────────

    def _build_resource_panel(self) -> QGroupBox:
        g = QGroupBox("📊  RESOURCES  (estimated)")
        gl = QVBoxLayout(g)
        gl.setSpacing(6)

        resources = [
            ("🪙", "Gold",     "#f5c842", "r_gold"),
            ("🪵", "Wood",     "#a16207", "r_wood"),
            ("⛏️", "Ore",      "#9ca3af", "r_ore"),
            ("🔮", "Mana",     "#a855f7", "r_mana"),
            ("💎", "Gems",     "#00c8b8", "r_gems"),
            ("🏅", "Prestige", "#4488ff", "r_prestige"),
        ]

        self._res_bars = {}
        self._res_vals = {}

        for icon, name, color, key in resources:
            row = QHBoxLayout()
            ico = QLabel(icon)
            ico.setFixedWidth(24)
            ico.setStyleSheet("font-size: 14px; background: transparent; border: none;")
            name_lbl = QLabel(name)
            name_lbl.setFixedWidth(65)
            name_lbl.setStyleSheet(f"color: #c0d0e0; font-size: 12px; background: transparent; border: none;")
            val_lbl = QLabel("--")
            val_lbl.setFixedWidth(80)
            val_lbl.setStyleSheet(f"color: {color}; font-family: Consolas; font-size: 11px; background: transparent; border: none;")
            bar = QProgressBar()
            bar.setFixedHeight(4)
            bar.setTextVisible(False)
            bar.setValue(0)
            bar.setStyleSheet(f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}")
            self._res_vals[key] = val_lbl
            self._res_bars[key] = bar
            row.addWidget(ico)
            row.addWidget(name_lbl)
            row.addWidget(val_lbl)
            row.addWidget(bar, 1)
            gl.addLayout(row)

        return g

    def _build_log_panel(self) -> QGroupBox:
        g = QGroupBox("📋  LIVE ACTIVITY LOG")
        gl = QVBoxLayout(g)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 10))

        clear_btn = QPushButton("🗑  Clear")
        clear_btn.setObjectName("redBtn")
        clear_btn.setFixedHeight(26)
        clear_btn.clicked.connect(self.log_box.clear)

        gl.addWidget(self.log_box, 1)
        gl.addWidget(clear_btn)
        return g

    # ─────────────────────────── BOT CONTROL ─────────────────────────

    def _toggle_bot(self):
        if not self._bot_running:
            self._start_bot()
        else:
            self._stop_bot()

    def _start_bot(self):
        self._log("info", "🚀 Starting CoD AutoBot...")
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from bot.scheduler import BotScheduler
            self.scheduler = BotScheduler(self.config, log_callback=self._thread_safe_log)
            if self.scheduler.start():
                self._bot_running = True
                self.start_btn.setText("⏸  STOP BOT")
                self.start_btn.setObjectName("stopBtn")
                self.start_btn.setStyleSheet("""
                    QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c03030, stop:1 #e04040);
                    border: none; color: white; font-size: 13px; font-weight: 800; padding: 10px 28px; border-radius: 5px; }
                """)
                self.conn_lbl.setText("⬤  CONNECTED")
                self.conn_lbl.setStyleSheet("color: #22c55e; font-family: Consolas; font-size: 11px; background: #0a1a10; padding: 5px 12px; border: 1px solid #22c55e; border-radius: 15px;")
                self.statusBar().showMessage("✅ Bot Running  •  BlueStacks ADB Connected  •  All modules active")
                for row in self._module_rows.values():
                    if row.toggle.isChecked():
                        row.set_running(True)
            else:
                self._log("err", "❌ Failed to start bot — check ADB connection")
        except ImportError as e:
            self._log("warn", f"⚠️ Bot modules not fully installed: {e}")
            self._log("warn", "Install dependencies: pip install opencv-python Pillow PyQt5")
            # Demo mode — just toggle UI
            self._bot_running = True
            self.start_btn.setText("⏸  STOP BOT")
            self.conn_lbl.setText("⬤  DEMO MODE")
            self.conn_lbl.setStyleSheet("color: #f5c842; font-family: Consolas; font-size: 11px; background: #1a1500; padding: 5px 12px; border: 1px solid #f5c842; border-radius: 15px;")

    def _stop_bot(self):
        if self.scheduler:
            self.scheduler.stop()
            self.scheduler = None
        self._bot_running = False
        self.start_btn.setText("▶  START BOT")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setStyleSheet("")
        self.conn_lbl.setText("⬤  DISCONNECTED")
        self.conn_lbl.setStyleSheet("color: #e04040; font-family: Consolas; font-size: 11px; background: #1a0a0a; padding: 5px 12px; border: 1px solid #2a2020; border-radius: 15px;")
        self.statusBar().showMessage("Bot Stopped  •  ADB Disconnected")
        for row in self._module_rows.values():
            row.set_running(False)
        self._log("warn", "⏹ Bot stopped")

    # ─────────────────────────── MODULE TOGGLES ──────────────────────

    def _on_module_toggled(self, module_id: str, enabled: bool):
        self._save_config_value(f"enable_{module_id}", enabled)
        if self.scheduler:
            self.scheduler.toggle_module(module_id, enabled)
        if module_id in self._module_rows:
            self._module_rows[module_id].set_running(enabled and self._bot_running)
        self._log("info", f"Module {'enabled' if enabled else 'disabled'}: {module_id}")

    def _enable_all(self):
        for mid, row in self._module_rows.items():
            row.toggle.setChecked(True)

    def _disable_all(self):
        for mid, row in self._module_rows.items():
            row.toggle.setChecked(False)

    # ─────────────────────────── STATS REFRESH ───────────────────────

    def _refresh_stats(self):
        if not self._bot_running:
            return

        # Update uptime
        if self.scheduler:
            stats = self.scheduler.get_stats()
            self.uptime_lbl.setText(f"⏱  {stats.get('uptime','00:00:00')}")
            self.stat_power.set_value(self._fmt(stats.get("power", 0)))
            self.stat_gold.set_value(self._fmt(stats.get("gold_gathered", 0)))
            self.stat_kills.set_value(str(stats.get("kills", 0)))
            self.stat_claimed.set_value(str(stats.get("claimed", 0)))
            pct = stats.get("research_progress", 0)
            self.research_bar.setValue(int(pct))
            self.research_lbl.setText(f"Current: {stats.get('current_research','--')} — {pct:.1f}% overall")

    def _fmt(self, n) -> str:
        try:
            n = int(n)
            if n >= 1_000_000: return f"{n/1_000_000:.2f}M"
            if n >= 1_000: return f"{n/1_000:.0f}K"
            return str(n)
        except:
            return "--"

    # ─────────────────────────── LOGGING ─────────────────────────────

    def _thread_safe_log(self, msg: str):
        """Called from bot thread — must be thread-safe."""
        level = "info"
        if "❌" in msg or "Error" in msg.lower() or "[err]" in msg.lower(): level = "err"
        elif "⚠️" in msg or "warn" in msg.lower(): level = "warn"
        elif "✅" in msg or "ok" in msg.lower(): level = "ok"
        elif "⚔️" in msg or "🚀" in msg or "⛏️" in msg: level = "act"
        self._signal.new_log.emit(level, msg)

    def _log(self, level: str, msg: str):
        self._signal.new_log.emit(level, msg)

    def _append_log(self, level: str, msg: str):
        colors = {
            "ok":   "#22c55e",
            "warn": "#f5c842",
            "err":  "#e04040",
            "info": "#00c8b8",
            "act":  "#c8860a",
        }
        color = colors.get(level, "#a0c0a0")
        t = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#4a6a7a">[{t}]</span> <span style="color:{color}">{msg}</span>'
        self.log_box.append(html)
        self.log_box.moveCursor(QTextCursor.End)

    # ─────────────────────────── CONFIG ──────────────────────────────

    def _load_config(self) -> dict:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "default_config.json"
        )
        try:
            with open(config_path) as f:
                return json.load(f)
        except:
            return {}

    def _save_config_value(self, key: str, value):
        self.config[key] = value
        if self.scheduler:
            self.scheduler.update_config({key: value})

    def _save_config_to_file(self):
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "default_config.json"
        )
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            self._log("ok", "✅ Config saved to default_config.json")
        except Exception as e:
            self._log("err", f"❌ Failed to save config: {e}")

    def closeEvent(self, event):
        self._stop_bot()
        event.accept()


# ─────────────────────────── ENTRY POINT ─────────────────────────────

def run_gui():
    if not PYQT5_OK:
        print("PyQt5 required. Run: pip install PyQt5")
        return

    app = QApplication(sys.argv)
    app.setApplicationName("CoD AutoBot")
    app.setOrganizationName("FarlightBot")

    window = CoDAutoBotWindow()
    window.show()
    sys.exit(app.exec_())
