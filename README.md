# CoD AutoBot

An automation assistant for Call of Duty Mobile running in BlueStacks on
Windows, driven over ADB. It screenshots the emulator, matches UI templates with
OpenCV, and taps through gathering, fighting, claiming rewards, research, base
building and the goblin merchant.

## Requirements

- Python 3.11+
- BlueStacks 5 with **ADB enabled** (Settings -> Advanced -> Android Debug Bridge)
- `adb` on your PATH (Android platform-tools)

## Setup

```bash
git clone https://github.com/kkcyber2/cod-assistant.git
cd cod-assistant/cod-autobot
pip install -r requirements.txt
python main.py
```

Set the emulator connection in `config.json` if it is not the default
`127.0.0.1:5555`:

```json
{
  "adb_host": "127.0.0.1",
  "adb_port": 5555,
  "templates_dir": "templates",
  "match_threshold": 0.85
}
```

### Templates

`templates/` holds the PNG crops the bot looks for. If it does not recognise a
screen, capture one with `adb exec-out screencap -p > screen.png`, crop the
button, and save it under the matching name. Template matching is
threshold-based, so re-crop after a game UI update.

## Running the tests

```bash
cd cod-autobot
pip install -r requirements-dev.txt
pip install opencv-python-headless pillow
python -m pytest tests/ -q
```

17 tests covering detection de-duplication (a button detected at several
offsets must be tapped once, and the highest-confidence hit must win) and module
lifecycle and timing. They need no emulator, no ADB, and no game account.

## Layout

```
cod-autobot/
  main.py            entry point
  bot/adb.py         ADB connection, tap/swipe/screenshot
  bot/screen.py      OpenCV template matching and de-duplication
  bot/scheduler.py   module loop and intervals
  bot/<module>.py    gather, fight, claim, research, build, goblin
  gui/app.py         Tkinter control panel
  tests/
```

## Notes

Intervals in `scheduler.py` are deliberately conservative and jittered, because
actions that happen on an exact cadence are the easiest thing to detect. Taps
are offset by a small random amount for the same reason.

## Licence

MIT — see `LICENSE`. Author: Konain Sultan Khan (KK),
https://github.com/kkcyber2
