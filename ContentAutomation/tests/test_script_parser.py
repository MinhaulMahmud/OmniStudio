"""
Tests for Feature B: Script-with-Timestamps Parser
==================================================
Covers:
  - Valid timestamped script parsing
  - Overlap detection and error reporting
  - Decreasing timestamp detection
  - Missing required fields
  - Gaps calculation
  - Conversion to VideoScript
"""
import pytest
from script_parser import parse_timestamped_script, TimestampedSection, ParsedScript


def test_parse_valid_timestamped_script():
    """Verify that a valid script is parsed into sections with exact timings."""
    data = {
        "title": "Jet Propulsion Basics",
        "platform": "shorts",
        "sections": [
            {
                "id": "hook",
                "text": "Jet engines work by pushing air backward — fast.",
                "start_ms": 0,
                "duration_ms": 3000,
                "visual_hint": "thrust vector diagram"
            },
            {
                "id": "body",
                "text": "Inside, a compressor squeezes air, fuel burns, and exhaust blasts out.",
                "start_ms": 3000,
                "duration_ms": 7000,
                "visual_hint": "cutaway engine"
            },
            {
                "id": "cta",
                "text": "Follow for more aerospace breakdowns.",
                "start_ms": 10000,
                "duration_ms": 2000
            }
        ]
    }

    parsed = parse_timestamped_script(data)
    assert parsed.title == "Jet Propulsion Basics"
    assert parsed.platform == "shorts"
    assert len(parsed.sections) == 3
    assert parsed.total_duration_ms == 12000
    assert len(parsed.gaps) == 0

    # Test conversion to pipeline VideoScript
    vscript = parsed.to_video_script()
    assert vscript.title == "Jet Propulsion Basics"
    assert vscript.duration_estimate == 12
    assert len(vscript.sections) == 3


def test_parse_with_end_ms_instead_of_duration():
    """Allow end_ms to be provided instead of duration_ms."""
    data = {
        "title": "Quantum Tunnels",
        "sections": [
            {"id": "s1", "text": "Particles can pass barriers.", "start_ms": 0, "end_ms": 4000},
            {"id": "s2", "text": "This is quantum tunneling.", "start_ms": 4000, "end_ms": 9000},
        ]
    }
    parsed = parse_timestamped_script(data)
    assert parsed.sections[0].duration_ms == 4000
    assert parsed.sections[1].duration_ms == 5000
    assert parsed.total_duration_ms == 9000


def test_parse_overlap_error():
    """Sections that collide in time must raise a descriptive ValueError."""
    data = {
        "title": "Overlapping Timers",
        "sections": [
            {"id": "intro", "text": "First concept.", "start_ms": 0, "duration_ms": 5000},
            {"id": "collision", "text": "Second concept.", "start_ms": 4000, "duration_ms": 3000},
        ]
    }
    with pytest.raises(ValueError, match="Section overlap detected"):
        parse_timestamped_script(data)


def test_parse_decreasing_timestamps():
    """Sections with out-of-order start_ms must raise ValueError."""
    data = {
        "title": "Time Travel Error",
        "sections": [
            {"id": "s1", "text": "Start late.", "start_ms": 5000, "duration_ms": 2000},
            {"id": "s2", "text": "Start early.", "start_ms": 1000, "duration_ms": 2000},
        ]
    }
    with pytest.raises(ValueError, match="non-decreasing"):
        parse_timestamped_script(data)


def test_parse_detect_gaps():
    """Gaps between sections must be recorded for silent padding."""
    data = {
        "title": "Script With B-Roll Gap",
        "sections": [
            {"id": "hook", "text": "Look at this.", "start_ms": 0, "duration_ms": 3000},
            # 2000ms gap here (3000ms to 5000ms)
            {"id": "reveal", "text": "Now look here.", "start_ms": 5000, "duration_ms": 4000},
        ]
    }
    parsed = parse_timestamped_script(data)
    assert len(parsed.gaps) == 1
    assert parsed.gaps[0] == (3000, 2000)
    assert parsed.total_duration_ms == 9000


def test_parse_missing_required_fields():
    """Missing title, empty sections, or missing text must raise ValueError."""
    with pytest.raises(ValueError, match="non-empty 'title'"):
        parse_timestamped_script({"title": "", "sections": [{"text": "Hi", "start_ms": 0, "duration_ms": 1000}]})

    with pytest.raises(ValueError, match="non-empty 'sections'"):
        parse_timestamped_script({"title": "No Sections", "sections": []})

    with pytest.raises(ValueError, match="non-empty 'text'"):
        parse_timestamped_script({"title": "No Text", "sections": [{"id": "s1", "text": "", "start_ms": 0, "duration_ms": 1000}]})


def test_parse_non_existent_file():
    """Attempting to load a missing file path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        parse_timestamped_script("non_existent_path_xyz123.json")
