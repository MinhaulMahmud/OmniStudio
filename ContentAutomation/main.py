#!/usr/bin/env python3
"""
ContentAutomation CLI
======================
Main entry point and management interface for the content automation system.

Commands:
  python main.py run              - Run the full pipeline
  python main.py list-voices     - List available VoiceStudio voices
  python main.py research        - Research trends only
  python main.py script          - Generate scripts only
  python main.py synthesize      - Synthesize audio only
  python main.py compose         - Compose video from existing assets
  python main.py status          - Check system health

Usage:
  python main.py run --topic "AI tools 2026"
  python main.py run --topics "ChatGPT tips,Python 2026" --platform shorts
  python main.py run --topic "Tech news" --voice-name "My Voice" --formats youtube,shorts
  python main.py list-voices
  python main.py status
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure script directory is on path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    OUTPUT_DIR,
    VOICESTUDIO_BASE_URL,
    DEFAULT_TOPICS,
    OUTPUT_FORMATS,
    LOG_LEVEL,
    LOG_FILE,
    CLONED_VOICE_ID,
    CLONED_VOICE_NAME,
)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


def cmd_status(args):
    """Check system status."""
    print("\n🔍 Content Automation System Status")
    print("=" * 60)

    # VoiceStudio
    from voice_client import VoiceStudioClient
    client = VoiceStudioClient()
    if client.is_running():
        voices = client.list_voices()
        print(f"  ✅ VoiceStudio: Running at {VOICESTUDIO_BASE_URL}")
        print(f"     Voices available: {len(voices)}")
        if CLONED_VOICE_ID:
            print(f"     Configured voice ID: {CLONED_VOICE_ID}")
        elif CLONED_VOICE_NAME:
            print(f"     Configured voice name: {CLONED_VOICE_NAME}")
        else:
            print("     ⚠️  No voice configured. Set CLONED_VOICE_ID in config.py or .env")
    else:
        print(f"  ❌ VoiceStudio: NOT running at {VOICESTUDIO_BASE_URL}")
        print("     → Open VoiceStudio app to enable TTS synthesis")

    # FFmpeg
    from video_composer import VideoComposer
    composer = VideoComposer()
    import shutil
    ffmpeg_path = shutil.which(composer.ffmpeg) or composer.ffmpeg
    ffmpeg_exists = Path(ffmpeg_path).exists() if Path(ffmpeg_path).is_absolute() else bool(shutil.which(ffmpeg_path))
    if ffmpeg_exists:
        print(f"  ✅ FFmpeg: Found at {ffmpeg_path}")
    else:
        print(f"  ❌ FFmpeg: Not found ({composer.ffmpeg})")
        print("     → Download FFmpeg: https://ffmpeg.org/download.html")
        print("     → Or set FFMPEG_PATH in .env file")

    # yt-dlp
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        print(f"  ✅ yt-dlp: v{result.stdout.strip()}")
    except Exception:
        print("  ❌ yt-dlp: Not found (pip install yt-dlp)")

    # LLM / AI Configuration
    from config import (
        LLM_BACKEND,
        OMNIROUTE_BASE_URL,
        OMNIROUTE_MODEL,
        OPENAI_API_KEY,
        OPENAI_MODEL,
        GEMINI_API_KEY,
    )
    from script_generator import OmnirouteClient
    omniroute = OmnirouteClient()
    if omniroute.is_running():
        print(f"  ✅ Omniroute (1.6B Tokens): Connected at {OMNIROUTE_BASE_URL} (model: {OMNIROUTE_MODEL})")
    else:
        print(f"  ⚠️  Omniroute (1.6B Tokens): Configured for {OMNIROUTE_BASE_URL} (ready on port)")

    if OPENAI_API_KEY:
        print(f"  ✅ OpenAI: Configured (model: {OPENAI_MODEL})")
    elif GEMINI_API_KEY:
        print(f"  ✅ Gemini: Configured")
    else:
        print("  ℹ️  Automatic Failover: If quota is reached on any model, routes to Omniroute (1.6B tokens).")

    # Output directory
    print(f"\n  📂 Output directory: {OUTPUT_DIR}")
    outputs = list(OUTPUT_DIR.glob("**/*.mp4"))
    print(f"     Videos generated: {len(outputs)}")
    print("=" * 60 + "\n")


def cmd_list_voices(args):
    """List available VoiceStudio voices."""
    from voice_client import VoiceStudioClient
    client = VoiceStudioClient()
    if not client.is_running():
        print(f"\n❌ VoiceStudio not running at {VOICESTUDIO_BASE_URL}")
        print("   Open VoiceStudio, then try again.\n")
        return

    voices = client.list_voices()
    if not voices:
        print("\nNo voices found. Create a cloned voice in VoiceStudio first.\n")
        return

    print(f"\n🎙️  Available Voices ({len(voices)})")
    print("─" * 60)
    for v in voices:
        vid = v.get("id") or v.get("voice_id", "?")
        name = v.get("name", "unnamed")
        vtype = v.get("type") or v.get("kind", "")
        marker = " ◀ ACTIVE" if vid == CLONED_VOICE_ID or name == CLONED_VOICE_NAME else ""
        print(f"  ID: {str(vid):<20}  Name: {name:<25}  Type: {vtype}{marker}")
    print()

    print("💡 To use a voice, set in config.py:")
    print('   CLONED_VOICE_ID = "your-voice-id"')
    print('   or CLONED_VOICE_NAME = "Your Voice Name"')
    print('   or use --voice-id / --voice-name flags\n')


def cmd_research(args):
    """Research trending content ideas with intelligent typo detection and web fallback."""
    from researcher import ContentResearcher
    researcher = ContentResearcher()

    topic = getattr(args, "topic", None)
    if topic:
        ideas, analysis = researcher.research_topic(raw_topic=topic, max_results=args.max or 5)
        researcher.print_summary(ideas, top=args.top or 10)
        if ideas:
            path = researcher.save_research(ideas)
            print(f"📄 Research saved to: {path}\n")
        return

    topics = [t.strip() for t in args.topics.split(",")] if getattr(args, "topics", None) else DEFAULT_TOPICS
    ideas = researcher.research_topics(topics=topics, max_per_topic=args.max or 5)
    researcher.print_summary(ideas, top=args.top or 10)
    if ideas:
        path = researcher.save_research(ideas)
        print(f"📄 Research saved to: {path}\n")


def cmd_script(args):
    """Generate a video script."""
    from script_generator import ScriptGenerator
    gen = ScriptGenerator()
    topic = args.topic or (DEFAULT_TOPICS[0] if DEFAULT_TOPICS else "AI tools")
    platform = args.platform or "youtube"
    script = gen.generate(topic=topic, platform=platform)
    path = gen.save_script(script)
    print(f"\n📜 Script: {script.title}")
    print(f"   Platform: {platform}")
    print(f"   Duration: ~{script.duration_estimate}s")
    print(f"   Saved to: {path}")
    print(f"\n--- HOOK ---\n{script.hook}\n")


def cmd_synthesize(args):
    """Synthesize audio from text or script file."""
    from voice_client import VoiceStudioClient
    client = VoiceStudioClient()
    if not client.is_running():
        print(f"❌ VoiceStudio not running at {VOICESTUDIO_BASE_URL}")
        return

    text = args.text
    if not text and args.script:
        with open(args.script, encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("full_narration") or data.get("hook", "")

    if not text:
        print("Provide --text or --script")
        return

    output = Path(args.output or OUTPUT_DIR / "audio_manual.mp3")
    result = client.synthesize(
        text=text,
        output_path=output,
        voice_id=args.voice_id,
        voice_name=args.voice_name,
    )
    if result:
        print(f"✅ Audio saved: {result}")
    else:
        print("❌ Synthesis failed. Check VoiceStudio is running with a cloned voice.")


def cmd_run(args):
    """Run the full pipeline."""
    from pipeline import ContentAutomationPipeline

    topics = None
    if args.topic:
        topics = [args.topic]
    elif args.topics:
        topics = [t.strip() for t in args.topics.split(",")]

    formats = [f.strip() for f in args.formats.split(",")] if args.formats else OUTPUT_FORMATS
    platform = args.platform or "youtube"

    custom_script = None
    if getattr(args, "from_script", None):
        with open(args.from_script, encoding="utf-8") as f:
            data = json.load(f)
        from script_generator import VideoScript
        custom_script = VideoScript(
            title=data["title"],
            platform=data.get("platform", platform),
            hook=data.get("hook", ""),
            sections=data.get("sections", []),
            cta=data.get("cta", ""),
            full_text=data.get("full_narration", ""),
        )

    pipeline = ContentAutomationPipeline()
    pipeline.run(
        topics=topics,
        platform=platform,
        formats=formats,
        voice_id=getattr(args, "voice_id", None),
        voice_name=getattr(args, "voice_name", None),
        skip_research=getattr(args, "no_research", False),
        skip_video=getattr(args, "no_video", False),
        use_remotion=getattr(args, "remotion", False),
        custom_script=custom_script,
    )


def cmd_image(args):
    """Generate an aesthetic image."""
    from generate_image import AestheticImageGenerator, DEFAULT_AESTHETIC_PROMPT
    gen = AestheticImageGenerator()
    prompt = args.prompt or DEFAULT_AESTHETIC_PROMPT
    aspect = args.aspect or "16:9"
    resolutions = {"1:1": (1024, 1024), "16:9": (1920, 1080), "9:16": (1080, 1920)}
    w, h = resolutions.get(aspect, (1920, 1080))
    import time
    out_file = Path(args.output or (OUTPUT_DIR / f"image_{int(time.time())}.jpg"))
    result = gen.generate(prompt=prompt, output_path=out_file, width=w, height=h)
    print(f"\n✅ Image generated: {result}")
    print(f"   Size: {result.stat().st_size / 1024:.1f} KB | Aspect: {aspect} ({w}x{h})\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🎬 Content Automation — Voice-cloned video content pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # ── run ──────────────────────────────────────────────────────────────────
    run_p = subparsers.add_parser("run", help="Run the full automation pipeline")
    run_p.add_argument("--topic", help="Single topic")
    run_p.add_argument("--topics", help="Comma-separated topics")
    run_p.add_argument("--platform", default="youtube",
                       choices=["youtube", "shorts", "tiktok", "instagram"])
    run_p.add_argument("--formats", help="Output formats (default: youtube,shorts,tiktok)")
    run_p.add_argument("--voice-id", dest="voice_id", help="Voice profile ID")
    run_p.add_argument("--voice-name", dest="voice_name", help="Voice profile name")
    run_p.add_argument("--no-research", action="store_true", help="Skip research step")
    run_p.add_argument("--no-video", action="store_true", help="Skip video composition")
    run_p.add_argument("--remotion", dest="remotion", action="store_true", default=True, help="Render motion graphics using Remotion (default: True)")
    run_p.add_argument("--no-remotion", dest="remotion", action="store_false", help="Disable Remotion motion graphics rendering")
    run_p.add_argument("--from-script", dest="from_script", type=Path,
                       help="Use existing script JSON")
    run_p.set_defaults(func=cmd_run)

    # ── status ────────────────────────────────────────────────────────────────
    stat_p = subparsers.add_parser("status", help="Check system health")
    stat_p.set_defaults(func=cmd_status)

    # ── list-voices ───────────────────────────────────────────────────────────
    lv_p = subparsers.add_parser("list-voices", help="List VoiceStudio voices")
    lv_p.set_defaults(func=cmd_list_voices)

    # ── research ──────────────────────────────────────────────────────────────
    res_p = subparsers.add_parser("research", help="Research trending content")
    res_p.add_argument("--topic", help="Single topic to analyze and research")
    res_p.add_argument("--topics", help="Comma-separated topics")
    res_p.add_argument("--max", type=int, default=10, help="Max results per topic")
    res_p.add_argument("--top", type=int, default=10, help="Top N to display")
    res_p.set_defaults(func=cmd_research)

    # ── script ────────────────────────────────────────────────────────────────
    scr_p = subparsers.add_parser("script", help="Generate a video script")
    scr_p.add_argument("--topic", required=True, help="Content topic")
    scr_p.add_argument("--platform", default="youtube",
                       choices=["youtube", "shorts", "tiktok"])
    scr_p.set_defaults(func=cmd_script)

    # ── synthesize ────────────────────────────────────────────────────────────
    syn_p = subparsers.add_parser("synthesize", help="Synthesize audio from text")
    syn_p.add_argument("--text", help="Text to synthesize")
    syn_p.add_argument("--script", type=Path, help="Script JSON file")
    syn_p.add_argument("--voice-id", dest="voice_id")
    syn_p.add_argument("--voice-name", dest="voice_name")
    syn_p.add_argument("--output", help="Output audio path")
    syn_p.set_defaults(func=cmd_synthesize)

    # ── image ─────────────────────────────────────────────────────────────────
    img_p = subparsers.add_parser("image", help="Generate an aesthetic AI image")
    img_p.add_argument("--prompt", help="Custom image prompt")
    img_p.add_argument("--aspect", choices=["16:9", "9:16", "1:1"], default="16:9",
                       help="Aspect ratio: 16:9 (YouTube), 9:16 (Shorts/TikTok), 1:1 (Square)")
    img_p.add_argument("--output", help="Output file path")
    img_p.set_defaults(func=cmd_image)

    # ── dashboard ─────────────────────────────────────────────────────────────
    dash_p = subparsers.add_parser("dashboard", help="Launch unified web dashboard")
    dash_p.add_argument("--port", type=int, default=8080, help="Dashboard port (default: 8080)")
    dash_p.set_defaults(func=lambda a: __import__("dashboard").start_server(port=a.port))

    args = parser.parse_args()

    if not args.command:
        # Default: show help
        parser.print_help()
        print("\nQuick start:")
        print("  python main.py status")
        print("  python main.py list-voices")
        print('  python main.py run --topic "AI productivity tips"')
        return

    args.func(args)


if __name__ == "__main__":
    main()
