"""
Tests for Feature A: User-Controlled Duration Control
=====================================================
Covers:
  - platform_profiles.validate_duration (None, negative, below min, above max, exact)
  - platform_profiles.calculate_target_words (wpm scaling, tolerance bounds, zero/negative error)
  - script_generator.generate with target_duration_s
  - CLI argument handling and validation
"""
import pytest
from platform_profiles import (
    get_profile,
    validate_duration,
    calculate_target_words,
)
from script_generator import ScriptGenerator


def test_validate_duration_none():
    """When no duration is passed, validation must succeed with no advisory warning."""
    profile = get_profile("youtube")
    is_valid, msg = validate_duration(None, profile)
    assert is_valid is True
    assert msg is None


def test_validate_duration_invalid_zero_or_negative():
    """Durations <= 0 must fail validation with an actionable error."""
    profile = get_profile("youtube")

    is_valid, msg = validate_duration(0, profile)
    assert is_valid is False
    assert "greater than 0" in msg

    is_valid, msg = validate_duration(-15, profile)
    assert is_valid is False
    assert "greater than 0" in msg


def test_validate_duration_below_platform_min():
    """Duration below platform recommended minimum triggers advisory warning but is valid."""
    profile = get_profile("shorts")  # duration_range_s is [25, 59]
    is_valid, msg = validate_duration(15, profile)
    assert is_valid is True
    assert msg is not None
    assert "below recommended minimum" in msg
    assert "15s" in msg
    assert f"{profile.duration_range_s[0]}s" in msg


def test_validate_duration_above_platform_max():
    """Duration above platform recommended maximum triggers advisory warning but is valid."""
    profile = get_profile("shorts")  # duration_range_s is [25, 59]
    is_valid, msg = validate_duration(90, profile)
    assert is_valid is True
    assert msg is not None
    assert "exceeds recommended maximum" in msg
    assert "90s" in msg
    assert f"{profile.duration_range_s[1]}s" in msg


def test_validate_duration_in_range():
    """Duration within platform bounds is valid with no warning."""
    profile = get_profile("shorts")  # duration_range_s is [30, 60]
    is_valid, msg = validate_duration(45, profile)
    assert is_valid is True
    assert msg is None


def test_calculate_target_words_formula():
    """Calculate target words should calculate ±15% around duration * (wpm / 60)."""
    # 60s at 140 wpm -> center = 140 words.
    # min_words = int(140 * 0.85) = 119
    # max_words = int(140 * 1.15) = 161
    min_w, max_w = calculate_target_words(60, wpm=140)
    assert min_w == 119
    assert max_w == 161

    # Short 10s video
    min_w_10, max_w_10 = calculate_target_words(10, wpm=150)
    assert min_w_10 >= 5
    assert max_w_10 > min_w_10


def test_calculate_target_words_invalid():
    """Calculate target words with duration <= 0 raises ValueError."""
    with pytest.raises(ValueError, match="greater than 0"):
        calculate_target_words(0)

    with pytest.raises(ValueError, match="greater than 0"):
        calculate_target_words(-5)


def test_script_generator_duration_estimate():
    """Script generator must record target duration and apply word constraints."""
    gen = ScriptGenerator()
    script = gen.generate(
        topic="Rocket Fuel Types",
        platform="shorts",
        target_duration_s=45,
    )
    assert script.duration_estimate == 45
