"""
Tests for YouTube Transcript Extraction & Visual Storyboard Flow
================================================================
Verifies:
  1. parse_vtt_subtitles parses WebVTT into clean text, stripping headers, timestamps, tags, and deduping.
  2. VideoIdea dataclass supports transcript field and serialization.
  3. fetch_video_transcript runs yt-dlp in a tempdir and extracts transcript text safely.
  4. ScriptGenerator._build_insights incorporates competitor transcripts into research prompts.
  5. RemotionRenderer passes visual_cue, graphic_type, and key_metric into DynamicExplainer props.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

from researcher import VideoIdea, parse_vtt_subtitles, ContentResearcher
from script_generator import ScriptGenerator
from remotion_renderer import RemotionRenderer


def test_parse_vtt_subtitles():
    sample_vtt = """WEBVTT
Kind: captions
Language: en

00:00:01.360 --> 00:00:03.040
[Applause]

00:00:03.100 --> 00:00:06.500
<c>Most</c> people think <c>jet</c> engines burn fuel to move forward,

00:00:06.500 --> 00:00:09.200
Most people think jet engines burn fuel to move forward,

00:00:09.250 --> 00:00:13.000
but 85% of modern airliner thrust is pure cold bypass air.

00:00:13.500 --> 00:00:15.000
♪ upbeat music ♪
"""
    cleaned = parse_vtt_subtitles(sample_vtt)
    assert "WEBVTT" not in cleaned
    assert "-->" not in cleaned
    assert "[Applause]" not in cleaned
    assert "♪" not in cleaned
    assert "<c>" not in cleaned
    assert "Most people think jet engines burn fuel to move forward, but 85% of modern airliner thrust is pure cold bypass air." in cleaned
    # Ensure deduplicated
    assert cleaned.count("Most people think jet engines burn fuel") == 1


def test_video_idea_transcript_serialization():
    idea = VideoIdea(
        platform="youtube",
        title="Turbofan Engineering",
        url="https://youtube.com/watch?v=123",
        transcript="This is the full spoken transcript of the competitor video explaining bypass ratios.",
        hook="Why high-bypass engines dominate modern aviation.",
    )
    d = idea.to_dict()
    assert "transcript" in d
    assert "competitor video explaining bypass ratios" in d["transcript"]


def test_fetch_video_transcript_empty():
    researcher = ContentResearcher()
    assert researcher.fetch_video_transcript("") == ""


def test_fetch_video_transcript_mocked_success(tmp_path):
    researcher = ContentResearcher()
    fake_vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello and welcome to engineering explainer."

    def fake_subprocess_run(cmd, **kwargs):
        # cmd has out_tmpl with tmpdir
        for arg in cmd:
            if "sub.%(ext)s" in arg:
                vtt_path = Path(arg.replace("%(ext)s", "en.vtt"))
                vtt_path.write_text(fake_vtt, encoding="utf-8")
        res = MagicMock()
        res.returncode = 0
        return res

    with patch("subprocess.run", side_effect=fake_subprocess_run):
        text = researcher.fetch_video_transcript("https://youtube.com/watch?v=mock123")
        assert "Hello and welcome to engineering explainer." in text


def test_build_insights_incorporates_transcript():
    generator = ScriptGenerator()
    ideas = [
        VideoIdea(
            platform="youtube",
            title="How Turbofans Work",
            url="https://youtube.com/watch?v=turbofan",
            view_count=500000,
            hook="The secret behind modern airliner fuel efficiency.",
            transcript="First, let's look at the titanium fan at the front of the nacelle.",
        )
    ]
    insights = generator._build_insights(ideas)
    assert "How Turbofans Work" in insights
    assert "500,000 views" in insights
    assert "Spoken Transcript Excerpt" in insights
    assert "titanium fan at the front" in insights


def test_remotion_renderer_preserves_visual_storyboard_fields(tmp_path):
    renderer = RemotionRenderer()
    dummy_audio = tmp_path / "dummy.mp3"
    dummy_audio.write_bytes(b"RIFF" + b"\x00" * 100)
    out_video = tmp_path / "out.mp4"

    sections = [
        {
            "heading": "Stage 01: Bypass Intake",
            "text": "The huge fan pushes 85 percent of the air around the engine.",
            "visual_cue": "Cyan particle stream flows around the outer cowl",
            "graphic_type": "turbofan",
            "key_metric": {"label": "Bypass Ratio", "value": "10:1", "unit": ""},
            "duration_hint": 15,
        }
    ]

    saved_props = {}

    def fake_subprocess_run(cmd, **kwargs):
        nonlocal saved_props
        # Read props file before it gets unlinked
        for arg in cmd:
            if "--props=" in arg:
                p_path = Path(arg.split("=", 1)[1])
                if p_path.exists():
                    import json
                    saved_props = json.loads(p_path.read_text(encoding="utf-8"))
        out_video.write_bytes(b"fake mp4 video")
        res = MagicMock()
        res.returncode = 0
        res.stdout = "Rendered successfully"
        res.stderr = ""
        return res

    with patch.object(renderer, "is_available", return_value=True), \
         patch("subprocess.run", side_effect=fake_subprocess_run):
        res = renderer.render(
            audio_path=dummy_audio,
            output_path=out_video,
            title="Turbofan Explainer",
            sections=sections,
            narration_text="The huge fan pushes 85 percent of the air around the engine.",
        )
        assert res == out_video
        assert "sections" in saved_props
        sec0 = saved_props["sections"][0]
        assert sec0["heading"] == "Stage 01: Bypass Intake"
        assert sec0["visualCue"] == "Cyan particle stream flows around the outer cowl"
        assert sec0["graphicType"] == "turbofan"
        assert sec0["keyMetric"] == {"label": "Bypass Ratio", "value": "10:1", "unit": ""}
