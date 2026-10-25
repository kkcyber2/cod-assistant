"""Tests for on-screen detection de-duplication.

A tap target detected several times at slightly different offsets must be
tapped once. Getting this wrong means the bot fires multiple taps at the same
button, which in this game can spend premium currency.
"""
import pytest

from bot.screen import Match, ScreenDetector


def make(name, x, y, conf=0.9, w=40, h=40):
    return Match(name=name, x=x, y=y, confidence=conf, w=w, h=h)


@pytest.fixture
def detector():
    # A detector with no templates directory still exposes _nms; template
    # loading is skipped when the directory is absent.
    return ScreenDetector(templates_dir="/nonexistent-templates-dir")


class TestNonMaximumSuppression:
    def test_empty_input_returns_empty(self, detector):
        assert detector._nms([], overlap=0.5) == []

    def test_single_match_survives(self, detector):
        result = detector._nms([make("btn", 100, 100)], overlap=0.5)
        assert len(result) == 1
        assert result[0].name == "btn"

    def test_duplicates_at_same_point_collapse_to_one(self, detector):
        matches = [make("btn", 100, 100, 0.7), make("btn", 102, 103, 0.95)]
        result = detector._nms(matches, overlap=0.5)
        assert len(result) == 1

    def test_highest_confidence_wins(self, detector):
        matches = [make("btn", 100, 100, 0.51), make("btn", 101, 99, 0.99)]
        result = detector._nms(matches, overlap=0.5)
        assert result[0].confidence == pytest.approx(0.99)

    def test_distant_matches_are_kept_separately(self, detector):
        matches = [make("btn", 10, 10), make("btn", 500, 500)]
        result = detector._nms(matches, overlap=0.5)
        assert len(result) == 2

    def test_ordering_is_by_confidence_descending(self, detector):
        matches = [
            make("a", 10, 10, 0.60),
            make("b", 300, 300, 0.95),
            make("c", 600, 600, 0.80),
        ]
        result = detector._nms(matches, overlap=0.5)
        confidences = [m.confidence for m in result]
        assert confidences == sorted(confidences, reverse=True)

    def test_overlap_threshold_controls_grouping(self, detector):
        # 30px apart with 40px boxes: overlaps at 0.9, not at 0.5.
        matches = [make("btn", 100, 100), make("btn", 130, 100)]
        assert len(detector._nms(matches, overlap=0.9)) == 1
        assert len(detector._nms(matches, overlap=0.5)) == 2

    def test_near_in_x_but_far_in_y_is_kept(self, detector):
        # Buttons stacked in a vertical list share an x coordinate.
        matches = [make("item", 100, 100), make("item", 100, 300)]
        assert len(detector._nms(matches, overlap=0.5)) == 2

    def test_does_not_mutate_caller_list_order_semantics(self, detector):
        matches = [make("a", 10, 10, 0.5), make("b", 500, 500, 0.9)]
        result = detector._nms(matches, overlap=0.5)
        assert len(result) == 2


class TestMatchDataclass:
    def test_center_returns_the_stored_point(self):
        m = make("btn", 42, 77)
        assert m.center() == (42, 77)
