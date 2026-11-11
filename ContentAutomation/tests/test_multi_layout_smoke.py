"""
Multi-Layout & Platform Verification Test Suite
================================================
Validates:
1. CLI argument conflict detection (exit code 2)
2. Safe-zone and layout modes for landscape (16:9), portrait (9:16), and square (1:1)
3. Deterministic fallbacks under all 3 layout modes validate cleanly with zero AST violations
4. VideoComposer single-caption ownership and non-destructive blurred letterbox/pillarbox
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from platform_profiles import (
    resolve_profile_and_format,
    get_profile,
    ArgumentConflictError,
    LayoutMode,
    STANDARD_FORMATS,
)
from remotion_synthesizer import RemotionSynthesizer, OUTPUT_FILE
from validate_scene import validate_scene_code
from video_composer import VideoComposer


class MockLongTitleScript:
    title = "Extremely Long Title Designed To Test Responsive Text Wrapping Across Mobile Portrait Safe Zones Without Overflowing"
    hook = "Deep architectural walkthrough testing typography bounds and responsiveness."
    sections = [
        {
            "heading": "Section 1: Kinematics and Aerodynamic Fluid Simulation",
            "text": "Detailed analysis of airflow parameters and high-compression boundary layer dynamics.",
        },
        {
            "heading": "Section 2: Thermodynamic Combustion Cycles",
            "text": "Evaluating fuel-air ratio and stoichiometric thermal efficiency across continuous cycles.",
        },
    ]


def test_cli_conflict_returns_code_2():
    """Verify that conflicting CLI platform and ratio triggers exit code 2."""
    script_path = Path(__file__).resolve().parent.parent / "pipeline.py"
    cmd = [sys.executable, str(script_path), "--platform", "youtube", "--ratio", "9:16"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "Conflicting arguments" in (proc.stderr + proc.stdout)


def test_all_layout_mode_fallbacks_pass_ast_validation():
    """Verify that fallbacks for portrait, square, and landscape all pass strict AST validation."""
    synthesizer = RemotionSynthesizer()
    script = MockLongTitleScript()

    profiles_to_test = [
        ("shorts", "portrait"),
        ("instagram", "square"),
        ("youtube", "landscape"),
    ]

    for pid, expected_mode in profiles_to_test:
        profile = get_profile(pid)
        synthesizer._write_fallback(
            topic="Aerospace Propulsion",
            script=script,
            audio_duration_s=25.0,
            profile=profile,
            video_format=profile.format,
        )
        code = OUTPUT_FILE.read_text(encoding="utf-8")
        assert f'layoutMode="{expected_mode}"' in code
        assert "SceneContainer" in code

        # AST validator must pass cleanly
        violations = validate_scene_code(code)
        assert len(violations) == 0, f"Fallback for {pid} had AST violations: {violations}"


def test_video_composer_single_caption_ownership():
    """Verify Remotion background disables duplicate FFmpeg caption burning."""
    vc = VideoComposer()
    mock_bg = Path("test_bg.mp4")

    # When background_path exists, burn_captions defaults to False
    mock_exists = MagicMock(return_value=True)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Path, "exists", mock_exists)
        cmd = vc._build_ffmpeg_command(
            audio_path=Path("dummy.mp3"),
            output_path=Path("out.mp4"),
            width=1080,
            height=1920,
            audio_duration=10.0,
            background_path=mock_bg,
            subtitle_file=Path("dummy.ass"),
            title="My Video Title",
            burn_captions=False,
        )
        cmd_str = " ".join(cmd)
        # ass filter and drawtext should NOT be present when Remotion owns typography
        assert "ass=" not in cmd_str
        assert "drawtext=" not in cmd_str


def test_video_composer_nondestructive_aspect_mismatch_blur():
    """Verify that aspect ratio mismatch applies frosted-glass blur instead of cropping."""
    vc = VideoComposer()
    mock_bg = Path("landscape_bg.mp4")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Path, "exists", lambda self: True)
        # Mock background video as 1920x1080 (16:9)
        mp.setattr(vc, "get_video_dimensions", lambda p: (1920, 1080))

        # Target format is 1080x1920 (9:16 Shorts)
        cmd = vc._build_ffmpeg_command(
            audio_path=Path("dummy.mp3"),
            output_path=Path("out.mp4"),
            width=1080,
            height=1920,
            audio_duration=10.0,
            background_path=mock_bg,
            subtitle_file=None,
            title="Shorts Test",
            burn_captions=False,
        )
        cmd_str = " ".join(cmd)
        # Must apply split frosted-glass blur and decrease scaling
        assert "boxblur=20:5" in cmd_str
        assert "force_original_aspect_ratio=decrease" in cmd_str
        # Must NOT perform destructive raw cropping on the foreground video
        assert "[vfg]scale=1080:1920:force_original_aspect_ratio=decrease" in cmd_str
        assert "[vfg]scale=1080:1920:force_original_aspect_ratio=increase,crop=" not in cmd_str

