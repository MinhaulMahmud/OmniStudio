"""
Unit tests for Voice Model Selection & Audio Settings (Audio Quality, Voice Refinement, Even Out Volume).
"""
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autonomous_voice_router import AutonomousVoiceRouter
from config import (
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_VOICE_REFINEMENT,
    DEFAULT_EVEN_OUT_VOLUME,
)
from voice_client import VoiceStudioClient


# ─── 1. AutonomousVoiceRouter Tests ──────────────────────────────────────────

def test_default_routing_uses_kittentts():
    """Default English narration routes to KittenTTS expr-voice-2-m."""
    decision = AutonomousVoiceRouter.route_voice("This is a fast explainer video about jet engines.")
    assert decision.model == "kittentts"
    assert decision.voice == "expr-voice-2-m"


def test_user_clone_voice_routing():
    """Selecting user clone ('minhaz' or clone ID) routes to OmniVoice with the clone."""
    decision = AutonomousVoiceRouter.route_voice(
        "Explaining propulsion using my cloned voice.",
        requested_voice="minhaz",
    )
    assert decision.model == "omnivoice"
    assert decision.voice == "minhaz"


def test_explicit_voice_model_omnivoice():
    """Selecting voice model omnivoice without voice defaults to a valid OmniVoice voice."""
    decision = AutonomousVoiceRouter.route_voice(
        "Explaining propulsion systems.",
        requested_model="omnivoice",
    )
    assert decision.model == "omnivoice"
    assert decision.voice in ["alloy", "onyx"]


def test_explicit_voice_model_and_explainer_voice():
    """Selecting voice model omnivoice with male explainer voice onyx routes correctly."""
    decision = AutonomousVoiceRouter.route_voice(
        "Explaining jet engine combustion chambers.",
        requested_model="omnivoice",
        requested_voice="onyx",
    )
    assert decision.model == "omnivoice"
    assert decision.voice == "onyx"


def test_explicit_voice_model_kittentts():
    """Selecting kittentts explicitly routes to kittentts."""
    decision = AutonomousVoiceRouter.route_voice(
        "Explaining aerodynamics.",
        requested_model="kittentts",
    )
    assert decision.model == "kittentts"
    assert decision.voice == "expr-voice-2-m"


# ─── 2. VoiceStudioClient Payload & Settings Tests ───────────────────────────

def test_synthesize_single_chunk_payload_defaults():
    """Payload to /v1/audio/speech must include default audio_quality (original), refinement (19), even_out_volume (True)."""
    client = VoiceStudioClient()
    mock_resp = MagicMock()
    mock_resp.iter_content.return_value = [b"dummy audio data " * 100]
    mock_resp.raise_for_status.return_value = None

    with patch.object(client.session, "post", return_value=mock_resp) as mock_post, \
         patch.object(client, "verify_audio", return_value=3.5):
        out = client.synthesize_single_chunk(
            text="Hello world test",
            output_path=Path("dummy_chunk.wav"),
            voice_id="expr-voice-2-m",
            model="kittentts",
        )
        assert out is not None
        assert mock_post.called
        payload = mock_post.call_args[1]["json"]
        assert payload["audio_quality"] == "original"
        assert payload["refinement"] == 19
        assert payload["even_out_volume"] is True


def test_three_audio_quality_categories():
    """Verify all 3 audio quality categories: standard, for editing / editing, and original."""
    client = VoiceStudioClient()
    mock_chunk_path = Path("fake_chunk.wav")

    categories_and_expected_codecs = [
        ("standard", "pcm_s16le"),
        ("editing", "pcm_s24le"),
        ("for editing", "pcm_s24le"),
        ("original", "pcm_f32le"),
    ]

    for quality_input, expected_codec in categories_and_expected_codecs:
        with patch.object(client, "synthesize_single_chunk", return_value=mock_chunk_path), \
             patch.object(client, "verify_audio", return_value=2.0), \
             patch("subprocess.run") as mock_subproc:
            mock_subproc.return_value = MagicMock(returncode=0, stderr="")

            client.synthesize_chunked(
                text_or_chunks=["Quality test."],
                output_path=Path("out.wav"),
                audio_format="wav",
                audio_quality=quality_input,
                even_out_volume=False,
            )

            concat_call = [call for call in mock_subproc.call_args_list if "-filter_complex" in call[0][0]]
            assert len(concat_call) >= 1
            cmd = concat_call[0][0][0]
            assert expected_codec in cmd


def test_synthesize_single_chunk_payload_custom():
    """Payload to /v1/audio/speech must honor custom audio_quality, refinement, and even_out_volume."""
    client = VoiceStudioClient()
    mock_resp = MagicMock()
    mock_resp.iter_content.return_value = [b"dummy audio data " * 100]
    mock_resp.raise_for_status.return_value = None

    with patch.object(client.session, "post", return_value=mock_resp) as mock_post, \
         patch.object(client, "verify_audio", return_value=4.0):
        out = client.synthesize_single_chunk(
            text="Testing custom refinement and quality",
            output_path=Path("dummy_chunk.wav"),
            voice_id="minhaz",
            model="omnivoice",
            audio_quality="editing",
            voice_refinement=25,
            even_out_volume=False,
        )
        assert out is not None
        payload = mock_post.call_args[1]["json"]
        assert payload["audio_quality"] == "editing"
        assert payload["refinement"] == 25
        assert payload["even_out_volume"] is False


def test_synthesize_chunked_ffmpeg_even_out_volume_loudnorm():
    """When even_out_volume is True, FFmpeg filter graph must apply loudnorm normalization."""
    client = VoiceStudioClient()
    mock_chunk_path = Path("fake_chunk.wav")

    with patch.object(client, "synthesize_single_chunk", return_value=mock_chunk_path), \
         patch.object(client, "verify_audio", return_value=2.0), \
         patch("subprocess.run") as mock_subproc:
        mock_subproc.return_value = MagicMock(returncode=0, stderr="")

        client.synthesize_chunked(
            text_or_chunks=["Sentence one.", "Sentence two."],
            output_path=Path("out.wav"),
            audio_format="wav",
            audio_quality="standard",
            even_out_volume=True,
        )

        # Check ffmpeg call args
        concat_call = [call for call in mock_subproc.call_args_list if "-filter_complex" in call[0][0]]
        assert len(concat_call) >= 1
        cmd = concat_call[0][0][0]
        filter_idx = cmd.index("-filter_complex") + 1
        filter_complex = cmd[filter_idx]
        assert "loudnorm" in filter_complex
        assert "pcm_s16le" in cmd


def test_synthesize_chunked_ffmpeg_no_even_out_volume():
    """When even_out_volume is False, loudnorm must not be applied."""
    client = VoiceStudioClient()
    mock_chunk_path = Path("fake_chunk.wav")

    with patch.object(client, "synthesize_single_chunk", return_value=mock_chunk_path), \
         patch.object(client, "verify_audio", return_value=2.0), \
         patch("subprocess.run") as mock_subproc:
        mock_subproc.return_value = MagicMock(returncode=0, stderr="")

        client.synthesize_chunked(
            text_or_chunks=["Sentence one.", "Sentence two."],
            output_path=Path("out.wav"),
            audio_format="wav",
            audio_quality="editing",
            even_out_volume=False,
        )

        concat_call = [call for call in mock_subproc.call_args_list if "-filter_complex" in call[0][0]]
        assert len(concat_call) >= 1
        cmd = concat_call[0][0][0]
        filter_idx = cmd.index("-filter_complex") + 1
        filter_complex = cmd[filter_idx]
        assert "loudnorm" not in filter_complex
        assert "pcm_s24le" in cmd


def test_synthesize_chunked_original_quality_codec():
    """When audio_quality is original, 32-bit float pcm_f32le codec must be used."""
    client = VoiceStudioClient()
    mock_chunk_path = Path("fake_chunk.wav")

    with patch.object(client, "synthesize_single_chunk", return_value=mock_chunk_path), \
         patch.object(client, "verify_audio", return_value=2.0), \
         patch("subprocess.run") as mock_subproc:
        mock_subproc.return_value = MagicMock(returncode=0, stderr="")

        client.synthesize_chunked(
            text_or_chunks=["Sentence one.", "Sentence two."],
            output_path=Path("out.wav"),
            audio_format="wav",
            audio_quality="original",
            even_out_volume=False,
        )

        concat_call = [call for call in mock_subproc.call_args_list if "-filter_complex" in call[0][0]]
        assert len(concat_call) >= 1
        cmd = concat_call[0][0][0]
        assert "pcm_f32le" in cmd


# ─── 3. CLI Argument Parser Tests ────────────────────────────────────────────

def test_pipeline_cli_parser_voice_options():
    """Verify CLI parser parses all voice and audio quality settings correctly."""
    from pipeline import main
    import sys

    test_args = [
        "pipeline.py",
        "--topic", "Aerospace Test",
        "--voice-model", "omnivoice",
        "--voice", "minhaz",
        "--audio-quality", "editing",
        "--voice-refinement", "25",
        "--no-even-out-volume",
        "--no-video",
        "--no-research",
    ]

    with patch.object(sys, "argv", test_args), \
         patch("pipeline.ContentAutomationPipeline.run") as mock_run:
        main()
        assert mock_run.called
        kwargs = mock_run.call_args[1]
        assert kwargs["voice_model"] == "omnivoice"
        assert kwargs["voice_name"] == "minhaz"
        assert kwargs["audio_quality"] == "editing"
        assert kwargs["voice_refinement"] == 25
        assert kwargs["even_out_volume"] is False
