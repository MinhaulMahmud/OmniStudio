"""
Script Parser — Timestamped Script Ingestion
===========================================
Validates and parses pre-authored scripts with per-section timing metadata.
Ensures zero overlap, non-decreasing timestamps, and automated gap detection.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from script_generator import VideoScript

logger = logging.getLogger(__name__)


@dataclass
class TimestampedSection:
    id: str
    text: str
    start_ms: int
    duration_ms: int
    heading: str = ""
    visual_hint: Optional[str] = None
    country_codes: list[str] = field(default_factory=list)
    coordinates: Optional[tuple[float, float]] = None

    @property
    def end_ms(self) -> int:
        return self.start_ms + self.duration_ms


@dataclass
class ParsedScript:
    title: str
    platform: str
    sections: list[TimestampedSection]
    total_duration_ms: int
    hook: str = ""
    cta: str = ""
    tags: list[str] = field(default_factory=list)
    seo_description: str = ""
    gaps: list[tuple[int, int]] = field(default_factory=list)  # [(start_ms, duration_ms)]

    def to_video_script(self) -> VideoScript:
        """Convert to standard pipeline VideoScript."""
        sec_dicts = []
        for s in self.sections:
            sec_dicts.append({
                "heading": s.heading or s.id.title(),
                "text": s.text,
                "duration_hint": max(1, int(s.duration_ms / 1000)),
                "start_ms": s.start_ms,
                "duration_ms": s.duration_ms,
                "visual_hint": s.visual_hint,
                "country_codes": s.country_codes,
            })

        return VideoScript(
            title=self.title,
            platform=self.platform,
            hook=self.hook or (self.sections[0].text if self.sections else ""),
            sections=sec_dicts,
            cta=self.cta or "Follow for more breakdowns.",
            tags=self.tags,
            seo_description=self.seo_description,
            duration_estimate=max(1, int(self.total_duration_ms / 1000)),
        )


def parse_timestamped_script(
    source: Union[str, Path, dict],
    default_platform: str = "shorts",
) -> ParsedScript:
    """
    Parse and validate a timestamped script JSON.

    Args:
        source: File path (str or Path) or already loaded dict.
        default_platform: Platform to use if not specified in JSON.

    Returns:
        Validated ParsedScript dataclass.

    Raises:
        ValueError: If schema is invalid, sections are empty, or timestamps overlap.
        FileNotFoundError: If source path does not exist.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Script file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif isinstance(source, dict):
        data = source
    else:
        raise ValueError(f"Expected file path or dict, got {type(source).__name__}")

    title = data.get("title", "").strip()
    if not title:
        raise ValueError("Script must include a non-empty 'title'.")

    platform = data.get("platform", default_platform).strip().lower()
    raw_sections = data.get("sections")

    if not isinstance(raw_sections, list) or len(raw_sections) == 0:
        raise ValueError("Script must contain a non-empty 'sections' list.")

    parsed_sections: list[TimestampedSection] = []
    gaps: list[tuple[int, int]] = []
    prev_end_ms = 0

    for i, raw_sec in enumerate(raw_sections):
        if not isinstance(raw_sec, dict):
            raise ValueError(f"Section at index {i} must be a JSON object, got {type(raw_sec).__name__}.")

        sec_id = str(raw_sec.get("id", f"section_{i}")).strip()
        text = str(raw_sec.get("text", raw_sec.get("narration", ""))).strip()
        if not text:
            raise ValueError(f"Section '{sec_id}' (index {i}) must include non-empty 'text' or 'narration'.")

        if "start_ms" not in raw_sec:
            raise ValueError(f"Section '{sec_id}' (index {i}) missing mandatory field 'start_ms'.")

        try:
            start_ms = int(raw_sec["start_ms"])
        except (ValueError, TypeError):
            raise ValueError(f"Section '{sec_id}' (index {i}) 'start_ms' must be an integer, got {raw_sec['start_ms']}.")

        if start_ms < 0:
            raise ValueError(f"Section '{sec_id}' (index {i}) 'start_ms' cannot be negative ({start_ms}ms).")

        # Determine duration_ms
        if "duration_ms" in raw_sec:
            try:
                duration_ms = int(raw_sec["duration_ms"])
            except (ValueError, TypeError):
                raise ValueError(f"Section '{sec_id}' 'duration_ms' must be an integer.")
        elif "end_ms" in raw_sec:
            try:
                end_ms = int(raw_sec["end_ms"])
                duration_ms = end_ms - start_ms
            except (ValueError, TypeError):
                raise ValueError(f"Section '{sec_id}' 'end_ms' must be an integer.")
        else:
            raise ValueError(f"Section '{sec_id}' (index {i}) must specify either 'duration_ms' or 'end_ms'.")

        if duration_ms <= 0:
            raise ValueError(f"Section '{sec_id}' (index {i}) duration must be greater than 0, got {duration_ms}ms.")

        # Overlap and ordering checks
        if i > 0:
            if start_ms < parsed_sections[-1].start_ms:
                raise ValueError(
                    f"Timestamps must be non-decreasing: section '{sec_id}' starts at {start_ms}ms, "
                    f"which is earlier than previous section '{parsed_sections[-1].id}' ({parsed_sections[-1].start_ms}ms)."
                )

            if start_ms < prev_end_ms:
                overlap = prev_end_ms - start_ms
                raise ValueError(
                    f"Section overlap detected: '{sec_id}' starts at {start_ms}ms, "
                    f"but previous section '{parsed_sections[-1].id}' ends at {prev_end_ms}ms "
                    f"(overlap of {overlap}ms). Sections must not collide."
                )

            if start_ms > prev_end_ms:
                gap_duration = start_ms - prev_end_ms
                gaps.append((prev_end_ms, gap_duration))
                logger.info("Found timing gap of %sms between '%s' and '%s'. Will insert silent pad.",
                            gap_duration, parsed_sections[-1].id, sec_id)

        parsed_sec = TimestampedSection(
            id=sec_id,
            text=text,
            start_ms=start_ms,
            duration_ms=duration_ms,
            heading=raw_sec.get("heading", ""),
            visual_hint=raw_sec.get("visual_hint"),
            country_codes=raw_sec.get("country_codes", []),
            coordinates=tuple(raw_sec["coordinates"]) if "coordinates" in raw_sec and raw_sec["coordinates"] else None,
        )
        parsed_sections.append(parsed_sec)
        prev_end_ms = parsed_sec.end_ms

    total_duration_ms = parsed_sections[-1].end_ms if parsed_sections else 0

    return ParsedScript(
        title=title,
        platform=platform,
        sections=parsed_sections,
        total_duration_ms=total_duration_ms,
        hook=data.get("hook", ""),
        cta=data.get("cta", ""),
        tags=data.get("tags", []),
        seo_description=data.get("seo_description", ""),
        gaps=gaps,
    )
