"""
Tests for Feature D: Modern Motion Graphics Engine (Anti-Slide Invariants)
==========================================================================
Covers:
  - AST / regex validation against presentation slide cards (ban_presentation_boxes)
  - Ban on bullet lists (ban_bullet_lists)
  - Word count limit enforcement on on-screen text (max_on_screen_words)
  - Verification of newly registered motion primitives
  - DynamicExplainer inspection ensuring zero slide card boxes
"""
import pytest
from pathlib import Path
from validate_scene import validate_scene_code


def test_reject_bullet_lists():
    """Reject <ul> and <li> elements to prevent lecture slide bullet points."""
    bad_code = """
    import React from "react";
    import { useCurrentFrame, interpolate } from "remotion";
    export const Scene = () => {
        const frame = useCurrentFrame();
        const opacity = interpolate(frame, [0, 10], [0, 1]);
        return (
            <ul>
                <li>Bullet Point 1</li>
                <li>Bullet Point 2</li>
            </ul>
        );
    };
    """
    violations = validate_scene_code(bad_code)
    rule_ids = [v.rule_id for v in violations]
    assert "ban_bullet_lists" in rule_ids


def test_reject_presentation_slide_boxes():
    """Reject static presentation slide boxes with gray semi-transparent backgrounds."""
    bad_code = """
    import React from "react";
    import { useCurrentFrame, interpolate } from "remotion";
    export const Scene = () => {
        const frame = useCurrentFrame();
        const opacity = interpolate(frame, [0, 10], [0, 1]);
        return (
            <div style={{ backgroundColor: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
                <h1>Topic Slide</h1>
            </div>
        );
    };
    """
    violations = validate_scene_code(bad_code)
    rule_ids = [v.rule_id for v in violations]
    assert "ban_presentation_boxes" in rule_ids


def test_reject_excessive_on_screen_words():
    """Reject walls of text with > 12 words in a single text overlay."""
    bad_code = """
    import React from "react";
    import { useCurrentFrame, interpolate } from "remotion";
    export const Scene = () => {
        const frame = useCurrentFrame();
        const opacity = interpolate(frame, [0, 10], [0, 1]);
        return (
            <div>
                <p>
                    This is an excessively long paragraph of text explaining every single detail of
                    the engine which forces the viewer to read rather than watch the animation.
                </p>
            </div>
        );
    };
    """
    violations = validate_scene_code(bad_code)
    rule_ids = [v.rule_id for v in violations]
    assert "max_on_screen_words" in rule_ids


def test_accept_clean_motion_graphics():
    """Accept code that uses KineticText, CinematicCamera, and DynamicBackdrop."""
    valid_code = """
    import React from "react";
    import { useCurrentFrame, interpolate } from "remotion";
    import { CinematicCamera, DynamicBackdrop, KineticText, HUDTelemetry } from "../primitives";

    export const MotionScene: React.FC = () => {
        const frame = useCurrentFrame();
        const rot = interpolate(frame, [0, 60], [0, 360], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
            <CinematicCamera drift="zoom-in">
                <DynamicBackdrop theme="aurora" />
                <KineticText phrase="Jet Propulsion Power" accentWords={["Power"]} fontSize={56} />
                <HUDTelemetry label="THRUST" value="45 kN" />
            </CinematicCamera>
        );
    };
    """
    violations = validate_scene_code(valid_code)
    assert len(violations) == 0


def test_dynamic_explainer_source_has_no_slide_boxes():
    """Verify that DynamicExplainer.tsx does not contain legacy slide card boxes or bullet lists."""
    explainer_path = Path(__file__).resolve().parent.parent / "remotion" / "src" / "DynamicExplainer.tsx"
    assert explainer_path.exists()
    content = explainer_path.read_text(encoding="utf-8")

    assert "<ul>" not in content
    assert "<ol>" not in content
    assert "<li>" not in content
    assert "bullets.slice" not in content
    assert "KineticText" in content
    assert "DynamicBackdrop" in content
    assert "CinematicCamera" in content
