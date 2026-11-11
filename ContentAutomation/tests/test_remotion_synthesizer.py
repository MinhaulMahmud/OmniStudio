"""
Unit tests for RemotionSynthesizer
Tests repair loop on invalid LLM output and graceful fallback to deterministic primitives.
"""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from remotion_synthesizer import RemotionSynthesizer, OUTPUT_FILE


class MockScript:
    title = "Test Jet Engine Thrust"
    hook = "How jet engines generate propulsion"
    sections = [
        {"heading": "Intake & Compression", "text": "Fan blades draw air in and compress it."},
        {"heading": "Combustion & Thrust", "text": "Fuel ignites creating high velocity exhaust."},
    ]


def test_synthesizer_broken_code_triggers_repair_and_fallback():
    synthesizer = RemotionSynthesizer()

    # Broken code with forbidden CSS transition and disallowed import
    broken_code = """
    import React from "react";
    import fs from "fs";
    export const DynamicTopicScene = () => {
        return <div style={{ transition: "all 0.5s ease" }}>Broken</div>;
    };
    """

    mock_llm = MagicMock(return_value=broken_code)

    with patch.object(synthesizer, "_call_openrouter", mock_llm):
        out_path = synthesizer.synthesize(
            topic="Jet Engines",
            script=MockScript(),
            audio_duration_s=20.0,
            visual_keywords=["turbine", "thrust"],
            max_repair_attempts=2,
        )

        assert out_path == OUTPUT_FILE
        assert OUTPUT_FILE.exists()
        # Verify LLM was retried
        assert mock_llm.call_count == 2

        # Verify fallback was written and contains valid code
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert "TitleCard" in content
        assert "Test Jet Engine Thrust" in content

        # Verify fallback compiles smoke test
        smoke_ok, smoke_err = synthesizer._smoke_test_render(OUTPUT_FILE)
        assert smoke_ok is True, f"Smoke test failed on fallback: {smoke_err}"

