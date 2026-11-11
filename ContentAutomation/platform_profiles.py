"""
Platform Profiles & Video Format Specification
==============================================
Separates technical VideoFormat (resolution, fps, layout_mode) from delivery PlatformProfile
(safe zones, pacing, duration bounds, caption style).
Single source of truth for prompts, skills rules, primitives, and composers.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROFILES_JSON = Path(__file__).resolve().parent / "platform_profiles.json"


class LayoutMode(str, Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"
    SQUARE = "square"


@dataclass(frozen=True)
class VideoFormat:
    id: str                  # "16:9", "9:16", "1:1"
    width: int               # pixels
    height: int              # pixels
    fps: int                 # frames per second
    aspect_ratio: str        # e.g. "16:9"
    layout_mode: LayoutMode

    def to_dict(self) -> dict:
        d = asdict(self)
        d["layout_mode"] = self.layout_mode.value
        return d


@dataclass(frozen=True)
class SafeZone:
    top: int
    bottom: int
    left: int
    right: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PlatformProfile:
    id: str
    display_name: str
    format: VideoFormat
    safe_zone: SafeZone
    duration_range_s: tuple[int, int]
    target_wpm: int
    caption_style: str
    max_bullet_points: int
    title_char_limit: int

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "format": self.format.to_dict(),
            "safe_zone": self.safe_zone.to_dict(),
            "duration_range_s": list(self.duration_range_s),
            "target_wpm": self.target_wpm,
            "caption_style": self.caption_style,
            "max_bullet_points": self.max_bullet_points,
            "title_char_limit": self.title_char_limit,
        }


# Standard Video Formats
STANDARD_FORMATS: dict[str, VideoFormat] = {
    "16:9": VideoFormat(
        id="16:9",
        width=1920,
        height=1080,
        fps=30,
        aspect_ratio="16:9",
        layout_mode=LayoutMode.LANDSCAPE,
    ),
    "9:16": VideoFormat(
        id="9:16",
        width=1080,
        height=1920,
        fps=30,
        aspect_ratio="9:16",
        layout_mode=LayoutMode.PORTRAIT,
    ),
    "1:1": VideoFormat(
        id="1:1",
        width=1080,
        height=1080,
        fps=30,
        aspect_ratio="1:1",
        layout_mode=LayoutMode.SQUARE,
    ),
}

# Alias mappings for user-friendly ratio input
RATIO_ALIASES: dict[str, str] = {
    "16:9": "16:9",
    "landscape": "16:9",
    "horizontal": "16:9",
    "wide": "16:9",
    "9:16": "9:16",
    "portrait": "9:16",
    "vertical": "9:16",
    "short": "9:16",
    "reel": "9:16",
    "1:1": "1:1",
    "square": "1:1",
}


def load_platform_profiles(json_path: Path = PROFILES_JSON) -> dict[str, PlatformProfile]:
    """Load platform profiles from JSON config, binding each to its VideoFormat."""
    if not json_path.exists():
        raise FileNotFoundError(f"Platform profiles config not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles: dict[str, PlatformProfile] = {}
    for pid, pdata in data.items():
        format_id = pdata["format_id"]
        if format_id not in STANDARD_FORMATS:
            raise ValueError(f"Unknown format_id '{format_id}' in profile '{pid}'")
        video_fmt = STANDARD_FORMATS[format_id]

        sz = pdata["safe_zone"]
        safe_zone = SafeZone(
            top=sz.get("top", 80),
            bottom=sz.get("bottom", 80),
            left=sz.get("left", 80),
            right=sz.get("right", 80),
        )

        dur_range = tuple(pdata.get("duration_range_s", [30, 180]))

        profiles[pid] = PlatformProfile(
            id=pid,
            display_name=pdata.get("display_name", pid.title()),
            format=video_fmt,
            safe_zone=safe_zone,
            duration_range_s=dur_range,  # type: ignore
            target_wpm=pdata.get("target_wpm", 150),
            caption_style=pdata.get("caption_style", "clean_box"),
            max_bullet_points=pdata.get("max_bullet_points", 3),
            title_char_limit=pdata.get("title_char_limit", 50),
        )

    return profiles


# Preloaded registry
PLATFORM_PROFILES = load_platform_profiles()


def get_profile(platform_id: str) -> PlatformProfile:
    """Retrieve platform profile by ID (e.g. 'youtube', 'shorts', 'reels', 'instagram')."""
    pid = platform_id.strip().lower()
    if pid not in PLATFORM_PROFILES:
        supported = ", ".join(sorted(PLATFORM_PROFILES.keys()))
        raise ValueError(f"Unknown platform '{platform_id}'. Supported platforms: {supported}")
    return PLATFORM_PROFILES[pid]


class ArgumentConflictError(Exception):
    """Raised when --platform and --ratio conflict."""
    pass


def resolve_profile_and_format(
    platform: Optional[str] = None,
    ratio: Optional[str] = None,
) -> tuple[PlatformProfile, VideoFormat]:
    """
    Resolve PlatformProfile and VideoFormat from CLI inputs with conflict detection.

    Rules:
      1. Default when neither is provided: platform='youtube', format='16:9'
      2. If platform is given: default format is profile's format.
      3. If ratio is given: map to VideoFormat, pick default platform for that ratio.
      4. If both are given: validate compatibility. If conflicting, raise ArgumentConflictError.
    """
    profiles = PLATFORM_PROFILES

    # Normalize ratio alias if provided
    normalized_ratio: Optional[str] = None
    if ratio:
        norm = ratio.strip().lower()
        if norm not in RATIO_ALIASES:
            supported = ", ".join(sorted(set(STANDARD_FORMATS.keys())))
            raise ValueError(f"Unsupported ratio '{ratio}'. Supported ratios: {supported}")
        normalized_ratio = RATIO_ALIASES[norm]

    # Normalize platform if provided
    norm_platform: Optional[str] = None
    if platform:
        norm_platform = platform.strip().lower()
        if norm_platform not in profiles:
            supported_p = ", ".join(sorted(profiles.keys()))
            raise ValueError(f"Unknown platform '{platform}'. Supported platforms: {supported_p}")

    # Case 1: Neither provided -> Default to YouTube (16:9)
    if not norm_platform and not normalized_ratio:
        default_profile = profiles["youtube"]
        return default_profile, default_profile.format

    # Case 2: Platform only
    if norm_platform and not normalized_ratio:
        profile = profiles[norm_platform]
        return profile, profile.format

    # Case 3: Ratio only
    if normalized_ratio and not norm_platform:
        video_fmt = STANDARD_FORMATS[normalized_ratio]
        # Pick best platform preset for this ratio
        preset_map = {
            "16:9": "youtube",
            "9:16": "shorts",
            "1:1": "instagram",
        }
        fallback_pid = preset_map.get(normalized_ratio, "youtube")
        profile = profiles[fallback_pid]
        return profile, video_fmt

    # Case 4: Both provided -> Conflict Check
    assert norm_platform is not None and normalized_ratio is not None
    profile = profiles[norm_platform]
    platform_expected_ratio = profile.format.aspect_ratio

    if platform_expected_ratio != normalized_ratio:
        raise ArgumentConflictError(
            f"Conflicting arguments: Platform '{norm_platform}' requires format '{platform_expected_ratio}', "
            f"but '--ratio {ratio}' was requested.\n"
            f"Remedy: Either use a matching platform (e.g. '--platform shorts' for 9:16), "
            f"or remove '--ratio' to use {profile.display_name}'s native {platform_expected_ratio} format."
        )

    return profile, profile.format


def validate_duration(
    duration_s: Optional[int],
    profile: PlatformProfile,
) -> tuple[bool, Optional[str]]:
    """
    Validate user-specified duration against platform profile bounds.

    Returns:
        (is_valid, message):
          - (True, None) if duration is within range or None.
          - (False, error_msg) if duration <= 0.
          - (True, warning_msg) if duration is outside platform bounds (advisory).
    """
    if duration_s is None:
        return True, None

    if duration_s <= 0:
        return False, f"Invalid duration {duration_s}s: duration must be greater than 0."

    min_s, max_s = profile.duration_range_s
    if duration_s < min_s:
        return True, (
            f"Advisory: requested duration {duration_s}s is below recommended minimum "
            f"for {profile.display_name} ({min_s}s). Video will be generated with tighter pacing."
        )
    if duration_s > max_s:
        return True, (
            f"Advisory: requested duration {duration_s}s exceeds recommended maximum "
            f"for {profile.display_name} ({max_s}s). Video will be generated as a longer cut."
        )

    return True, None


def calculate_target_words(
    duration_s: int,
    wpm: int = 140,
) -> tuple[int, int]:
    """
    Calculate target word count range (min_words, max_words) for a given duration in seconds.
    Uses ±15% tolerance around average speech rate.
    """
    if duration_s <= 0:
        raise ValueError(f"Duration must be greater than 0, got {duration_s}")
    center_words = int(duration_s * (wpm / 60.0))
    min_words = max(5, int(center_words * 0.85))
    max_words = max(min_words + 5, int(center_words * 1.15))
    return min_words, max_words
