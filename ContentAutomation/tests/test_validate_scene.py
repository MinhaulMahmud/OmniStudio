"""
Unit tests for validate_scene.py
Tests 6 bad samples and 2 good samples to verify strict Remotion compliance.
"""
import pytest
from validate_scene import validate_scene_code


def test_bad_sample_1_css_transition():
    code = """
    import React from "react";
    export const Scene = () => {
        return <div style={{ transition: "all 0.3s ease", opacity: 1 }}>Bad</div>;
    };
    """
    v = validate_scene_code(code)
    assert any(violation.rule_id == "no_css_animations" for violation in v)


def test_bad_sample_2_keyframes():
    code = """
    import React from "react";
    export const Scene = () => {
        return (
            <style>{`
                @keyframes spin { 0% { rotate: 0deg; } 100% { rotate: 360deg; } }
            `}</style>
        );
    };
    """
    v = validate_scene_code(code)
    assert any(violation.rule_id == "no_css_animations" for violation in v)


def test_bad_sample_3_forbidden_import():
    code = """
    import React from "react";
    import fs from "fs";
    export const Scene = () => <div>Insecure</div>;
    """
    v = validate_scene_code(code)
    assert any(violation.rule_id == "disallowed_import" for violation in v)


def test_bad_sample_4_runtime_fetch():
    code = """
    import React, { useEffect } from "react";
    export const Scene = () => {
        useEffect(() => {
            fetch("https://api.example.com/data");
        }, []);
        return <div>Data</div>;
    };
    """
    v = validate_scene_code(code)
    assert any(violation.rule_id == "forbidden_runtime_call" for violation in v)


def test_bad_sample_5_eval_call():
    code = """
    import React from "react";
    export const Scene = () => {
        const x = eval("2 + 2");
        return <div>{x}</div>;
    };
    """
    v = validate_scene_code(code)
    assert any(violation.rule_id == "forbidden_runtime_call" for violation in v)


def test_bad_sample_6_hardcoded_fps_duration():
    code = """
    import React from "react";
    import { Sequence } from "remotion";
    export const Scene = () => {
        return <Sequence from={0} durationInFrames={450}><div>Fixed</div></Sequence>;
    };
    """
    v = validate_scene_code(code)
    assert any(violation.rule_id == "hardcoded_fps_frames" for violation in v)


def test_good_sample_1_primitives_composition():
    code = """
    import React from "react";
    import { useCurrentFrame, useVideoConfig, interpolate, Sequence } from "remotion";
    import { TitleCard } from "../primitives/TitleCard";

    export const DynamicTopicScene: React.FC = () => {
        const frame = useCurrentFrame();
        const { fps } = useVideoConfig();

        const opacity = interpolate(frame, [0, Math.round(1 * fps)], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
        });

        return (
            <Sequence from={0} durationInFrames={Math.round(5 * fps)}>
                <div style={{ opacity }}>
                    <TitleCard title="Jet Engines" subtitle="How Thrust is Generated" />
                </div>
            </Sequence>
        );
    };
    """
    v = validate_scene_code(code)
    assert len(v) == 0, f"Expected 0 violations but got: {[str(x) for x in v]}"


def test_bad_sample_7_excessive_width():
    code = """
    import React from "react";
    import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
    export const Scene = () => {
        const frame = useCurrentFrame();
        const { fps } = useVideoConfig();
        const o = interpolate(frame, [0, 10], [0, 1]);
        return <div style={{ width: "1600px", opacity: o }}>Wide Container</div>;
    };
    """
    v = validate_scene_code(code)
    assert any(violation.rule_id == "no_hardcoded_wide_widths" for violation in v)


def test_good_sample_2_spring_bullets():
    code = """
    import React from "react";
    import { useCurrentFrame, useVideoConfig, spring, Sequence } from "remotion";
    import { BulletReveal } from "../primitives/BulletReveal";

    export const DynamicTopicScene: React.FC = () => {
        const frame = useCurrentFrame();
        const { fps } = useVideoConfig();

        const scale = spring({ frame, fps, config: { damping: 12 } });

        return (
            <Sequence from={0} durationInFrames={Math.round(10 * fps)}>
                <div style={{ transform: `scale(${scale})` }}>
                    <BulletReveal bullets={["Intake", "Compression", "Combustion", "Exhaust"]} />
                </div>
            </Sequence>
        );
    };
    """
    v = validate_scene_code(code)
    assert len(v) == 0, f"Expected 0 violations but got: {[str(x) for x in v]}"

