"""Tests for the shared module lifecycle and timing helpers."""
import time

import pytest

from bot.base_module import BotModule


class FakeADB:
    def __init__(self):
        self.taps = []

    def tap(self, x, y, human=True):
        self.taps.append((x, y))


class FakeScreen:
    def __init__(self, result=None):
        self.result = result
        self.calls = 0

    def find(self, screen_img, name, threshold=None):
        self.calls += 1
        return self.result


class Match:
    def __init__(self, x, y, confidence=0.9):
        self.x, self.y, self.confidence = x, y, confidence


@pytest.fixture
def module():
    return BotModule(FakeADB(), FakeScreen(), {}, log_callback=lambda *_: None)


class TestLifecycle:
    def test_starts_disabled(self, module):
        assert module.enabled is False
        assert module.running is False

    def test_enable_and_disable(self, module):
        module.enable()
        assert module.enabled is True
        module.disable()
        assert module.enabled is False

    def test_stop_clears_running(self, module):
        module.running = True
        module.stop()
        assert module.running is False
        assert module._stop_event.is_set()


class TestTapIfFound:
    def test_taps_when_a_match_is_found(self, module):
        module.screen = FakeScreen(Match(10, 20))
        assert module.tap_if_found(object(), "btn") is True
        assert module.adb.taps == [(10, 20)]

    def test_does_not_tap_when_nothing_is_found(self, module):
        module.screen = FakeScreen(None)
        assert module.tap_if_found(object(), "btn") is False
        assert module.adb.taps == []


class TestWait:
    def test_never_sleeps_a_negative_duration(self, module):
        # A jitter larger than the delay would otherwise produce a negative
        # sleep; the floor keeps it at a fraction of a second.
        start = time.monotonic()
        module.wait(0.1, jitter=5.0)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.04
        assert elapsed < 1.0

    def test_actually_sleeps_roughly_the_requested_time(self, module):
        start = time.monotonic()
        module.wait(0.2, jitter=0.02)
        elapsed = time.monotonic() - start
        assert 0.15 <= elapsed < 0.5
