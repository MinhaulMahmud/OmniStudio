"""
Unit tests for platform_profiles.py
Validates Format vs Platform profile resolution, defaults, and conflict detection.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from platform_profiles import (
    resolve_profile_and_format,
    ArgumentConflictError,
    LayoutMode,
    PLATFORM_PROFILES,
    STANDARD_FORMATS,
)


def test_default_resolution_when_neither_given():
    profile, fmt = resolve_profile_and_format(None, None)
    assert profile.id == "youtube"
    assert fmt.aspect_ratio == "16:9"
    assert fmt.width == 1920
    assert fmt.height == 1080
    assert fmt.layout_mode == LayoutMode.LANDSCAPE


def test_platform_shorts_resolution():
    profile, fmt = resolve_profile_and_format("shorts", None)
    assert profile.id == "shorts"
    assert fmt.aspect_ratio == "9:16"
    assert fmt.width == 1080
    assert fmt.height == 1920
    assert fmt.layout_mode == LayoutMode.PORTRAIT
    assert profile.safe_zone.bottom >= 300


def test_ratio_9_16_resolution():
    profile, fmt = resolve_profile_and_format(None, "9:16")
    assert fmt.aspect_ratio == "9:16"
    assert fmt.layout_mode == LayoutMode.PORTRAIT
    assert profile.id in ["shorts", "reels", "tiktok"]


def test_ratio_aliases():
    _, fmt_vert = resolve_profile_and_format(None, "vertical")
    assert fmt_vert.aspect_ratio == "9:16"
    assert fmt_vert.layout_mode == LayoutMode.PORTRAIT

    _, fmt_sq = resolve_profile_and_format(None, "square")
    assert fmt_sq.aspect_ratio == "1:1"
    assert fmt_sq.layout_mode == LayoutMode.SQUARE


def test_platform_instagram_square():
    profile, fmt = resolve_profile_and_format("instagram", None)
    assert profile.id == "instagram"
    assert fmt.aspect_ratio == "1:1"
    assert fmt.width == 1080
    assert fmt.height == 1080
    assert fmt.layout_mode == LayoutMode.SQUARE


def test_conflict_detection_youtube_and_vertical():
    with pytest.raises(ArgumentConflictError) as exc_info:
        resolve_profile_and_format(platform="youtube", ratio="9:16")
    assert "Conflicting arguments" in str(exc_info.value)
    assert "youtube" in str(exc_info.value)
    assert "9:16" in str(exc_info.value)


def test_conflict_detection_shorts_and_landscape():
    with pytest.raises(ArgumentConflictError) as exc_info:
        resolve_profile_and_format(platform="shorts", ratio="16:9")
    assert "Conflicting arguments" in str(exc_info.value)


def test_unknown_platform_raises_error():
    with pytest.raises(ValueError) as exc_info:
        resolve_profile_and_format(platform="unknown_tv", ratio=None)
    assert "Unknown platform" in str(exc_info.value)


def test_unsupported_ratio_raises_error():
    with pytest.raises(ValueError) as exc_info:
        resolve_profile_and_format(platform=None, ratio="4:3")
    assert "Unsupported ratio" in str(exc_info.value)
