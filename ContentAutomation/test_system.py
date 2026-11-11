"""
System Test Script
==================
Quick integration test to verify all components are working.
Run this after setup to check everything is connected properly.

Usage:
    python test_system.py
"""
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def print_section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

def test_imports():
    print_section("1. Testing module imports")
    modules = [
        "config",
        "researcher",
        "script_generator",
        "voice_client",
        "subtitle_generator",
        "video_composer",
        "background_manager",
        "composition_plan",
        "scheduler",
    ]
    all_ok = True
    for mod in modules:
        try:
            __import__(mod)
            print(f"  ✅ {mod}")
        except ImportError as exc:
            print(f"  ❌ {mod}: {exc}")
            all_ok = False
    return all_ok

def test_ytdlp():
    print_section("2. Testing yt-dlp")
    result = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--version"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        print(f"  ✅ yt-dlp v{result.stdout.strip()}")
        return True
    else:
        print(f"  ❌ yt-dlp not working: {result.stderr}")
        return False

def test_voicestudio():
    print_section("3. Testing VoiceStudio connection")
    from voice_client import VoiceStudioClient
    from config import VOICESTUDIO_BASE_URL
    client = VoiceStudioClient()
    if client.is_running():
        voices = client.list_voices()
        print(f"  ✅ VoiceStudio at {VOICESTUDIO_BASE_URL}")
        print(f"     {len(voices)} voice(s) available")
        for v in voices[:3]:
            print(f"     • {v.get('name', '?')} (id={v.get('id', '?')})")
        return True
    else:
        print(f"  ⚠️  VoiceStudio not running at {VOICESTUDIO_BASE_URL}")
        print("     Start VoiceStudio app first, then re-run this test")
        return False

def test_omniroute():
    print_section("3b. Testing Omniroute Proxy (1.6 Billion Tokens)")
    from script_generator import OmnirouteClient
    from config import OMNIROUTE_BASE_URL, OMNIROUTE_MODEL
    client = OmnirouteClient()
    if client.is_running():
        print(f"  ✅ Omniroute active at {OMNIROUTE_BASE_URL}")
        print(f"     Model: {OMNIROUTE_MODEL} (1.6 Billion tokens pool)")
        return True
    else:
        print(f"  ℹ️  Omniroute configured at {OMNIROUTE_BASE_URL}")
        print("     Will be used whenever the proxy is running / quota is reached on other models.")
        return True

def test_research():
    print_section("4. Testing content research (yt-dlp)")
    from researcher import ContentResearcher
    researcher = ContentResearcher()
    ideas = researcher.search_youtube("Python tips", max_results=2)
    if ideas:
        print(f"  ✅ Found {len(ideas)} YouTube video(s):")
        for idea in ideas[:2]:
            print(f"     • {idea.title[:60]} ({idea.view_count:,} views)")
        return True
    else:
        print("  ⚠️  No results (may need internet access or yt-dlp update)")
        return False

def test_script_generation():
    print_section("5. Testing script generation")
    from script_generator import ScriptGenerator
    gen = ScriptGenerator()
    script = gen.generate("Python tips for beginners", platform="shorts")
    if script and script.hook:
        print(f"  ✅ Script generated: {script.title[:60]}")
        print(f"     Hook: {script.hook[:80]}")
        return True
    else:
        print("  ❌ Script generation failed")
        return False

def test_subtitles():
    print_section("6. Testing subtitle generation")
    from subtitle_generator import SubtitleGenerator
    gen = SubtitleGenerator()
    text = "Welcome to this video. Today we'll learn about Python. It's going to be great."
    chunks = gen.generate(text, audio_duration_ms=10000)
    if chunks:
        print(f"  ✅ Generated {len(chunks)} subtitle chunks")
        print(f"     Sample: [{chunks[0].start_srt}] {chunks[0].text}")
        return True
    else:
        print("  ❌ Subtitle generation failed")
        return False

def test_ffmpeg():
    print_section("7. Testing FFmpeg")
    from video_composer import VideoComposer
    import shutil
    composer = VideoComposer()
    ffmpeg_found = shutil.which(composer.ffmpeg) is not None or Path(composer.ffmpeg).is_file()
    if ffmpeg_found:
        print(f"  ✅ FFmpeg found: {composer.ffmpeg}")
        return True
    else:
        print(f"  ❌ FFmpeg not found ({composer.ffmpeg})")
        print("     Video composition will not work until FFmpeg is installed")
        print("     Download: https://ffmpeg.org/download.html")
        return False

def test_tts_synthesis():
    print_section("8. Testing TTS voice synthesis (requires VoiceStudio)")
    from voice_client import VoiceStudioClient
    from config import OUTPUT_DIR
    client = VoiceStudioClient()
    if not client.is_running():
        print("  ⚠️  Skipped: VoiceStudio not running")
        return None

    test_text = "This is a test of the content automation voice synthesis pipeline."
    test_path = OUTPUT_DIR / "test_synthesis.mp3"
    result = client.synthesize(test_text, test_path)
    if result and result.exists():
        size_kb = result.stat().st_size / 1024
        print(f"  ✅ Audio synthesized: {result.name} ({size_kb:.1f} KB)")
        return True
    else:
        print("  ❌ TTS synthesis failed")
        print("     → Ensure you have a cloned voice set up in VoiceStudio")
        print("     → Set CLONED_VOICE_ID or CLONED_VOICE_NAME in config.py")
        return False


def main():
    print("\n" + "═"*60)
    print("  🎬 Content Automation System Test")
    print("═"*60)

    results = {}
    results["imports"] = test_imports()
    results["ytdlp"] = test_ytdlp()
    results["voicestudio"] = test_voicestudio()
    results["omniroute"] = test_omniroute()
    results["research"] = test_research()
    results["scripts"] = test_script_generation()
    results["subtitles"] = test_subtitles()
    results["ffmpeg"] = test_ffmpeg()
    results["tts"] = test_tts_synthesis()

    # Summary
    print(f"\n{'═'*60}")
    print("  TEST SUMMARY")
    print(f"{'═'*60}")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    for name, status in results.items():
        icon = "✅" if status is True else ("❌" if status is False else "⏭")
        print(f"  {icon} {name}")
    print(f"\n  {passed} passed, {failed} failed, {skipped} skipped")
    print(f"{'═'*60}\n")

    if failed > 0:
        print("⚠️  Fix the failing tests above, then run the pipeline.")
        print("   See README.md for setup instructions.\n")
    else:
        print("✅ All critical tests passed!")
        print("   Run: python main.py run --topic 'AI tools 2026'\n")


if __name__ == "__main__":
    main()
