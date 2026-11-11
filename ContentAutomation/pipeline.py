"""
Content Automation Pipeline
============================
The main orchestrator that ties together:
  1. Research (yt-dlp trend scraping)
  2. Script generation (LLM)
  3. Voice synthesis (VoiceStudio cloned voice)
  4. Subtitle generation
  5. Video composition (FFmpeg)
  6. Multi-format export

Usage:
    python pipeline.py --topic "AI productivity tips" --platform youtube
    python pipeline.py --research --topics "AI tools,python tips"
    python pipeline.py --from-script scripts/my_script.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    OUTPUT_DIR,
    LOGS_DIR,
    DEFAULT_TOPICS,
    OUTPUT_FORMATS,
    VIDEOS_PER_RUN,
    LOG_LEVEL,
    LOG_FILE,
    VOICESTUDIO_BASE_URL,
)
from researcher import ContentResearcher, VideoIdea
from script_generator import ScriptGenerator, VideoScript
from voice_client import VoiceStudioClient
from subtitle_generator import SubtitleGenerator
from video_composer import VideoComposer
from remotion_renderer import RemotionRenderer
from remotion_synthesizer import RemotionSynthesizer
from platform_profiles import (
    resolve_profile_and_format,
    validate_duration,
    ArgumentConflictError,
    PlatformProfile,
    VideoFormat,
    LayoutMode,
)

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ],
)
logger = logging.getLogger("pipeline")


class ContentAutomationPipeline:
    """
    End-to-end content automation pipeline.

    Workflow:
      Research → Script → Voice → Subtitles → Video → Export
    """

    def __init__(self):
        self.researcher = ContentResearcher()
        self.script_gen = ScriptGenerator()
        self.voice = VoiceStudioClient()
        self.subtitle_gen = SubtitleGenerator()
        self.video_composer = VideoComposer()
        self.remotion = RemotionRenderer()
        self.synthesizer = RemotionSynthesizer()

    # ─── Full Pipeline ────────────────────────────────────────────────────────

    def run(
        self,
        topics: Optional[list[str]] = None,
        platform: str = "youtube",
        formats: Optional[list[str]] = None,
        voice_id: Optional[str] = None,
        voice_name: Optional[str] = None,
        language: Optional[str] = None,
        skip_research: bool = False,
        skip_video: bool = False,
        use_remotion: bool = True,
        custom_script: Optional[VideoScript] = None,
        output_subdir: Optional[str] = None,
        profile: Optional[PlatformProfile] = None,
        video_format: Optional[VideoFormat] = None,
        duration: Optional[int] = None,
    ) -> list[dict]:
        """
        Run the full pipeline for one or more topics.

        Args:
            topics: List of topics to generate content for.
            platform: Primary platform (youtube, shorts, tiktok).
            formats: List of formats to export (youtube, shorts, tiktok).
            voice_id: VoiceStudio voice ID to use.
            voice_name: VoiceStudio voice name (resolved to ID).
            skip_research: Skip yt-dlp research step.
            skip_video: Only generate audio + script, not video.
            custom_script: Pre-built VideoScript to use directly.
            output_subdir: Subdirectory under output/ for this run.
            profile: Optional PlatformProfile specifying safe zones, pacing, limits.
            video_format: Optional VideoFormat specifying resolution, layout_mode.

        Returns:
            List of result dicts with paths to generated assets.
        """
        if profile is None or video_format is None:
            profile, video_format = resolve_profile_and_format(platform)

        topics = topics or DEFAULT_TOPICS
        formats = formats or [profile.id]
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = OUTPUT_DIR / (output_subdir or run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 60)
        logger.info("🚀 Content Automation Pipeline Started")
        logger.info("   Run ID: %s", run_id)
        logger.info("   Topics: %s", ", ".join(topics[:3]))
        logger.info("   Platform Profile: %s (%s)", profile.display_name, profile.id)
        logger.info("   Video Format: %dx%d (%s, %s)", video_format.width, video_format.height, video_format.aspect_ratio, video_format.layout_mode.value)
        logger.info("   Formats: %s", ", ".join(formats))
        logger.info("   Output: %s", run_dir)
        logger.info("=" * 60)

        # ─── Step 0: Check VoiceStudio ────────────────────────────────────
        self._check_voicestudio()

        results = []

        if custom_script:
            # Use provided script directly
            result = self._process_script(
                script=custom_script,
                voice_id=voice_id,
                voice_name=voice_name,
                language=language,
                formats=formats,
                run_dir=run_dir,
                skip_video=skip_video,
                use_remotion=use_remotion,
                profile=profile,
                video_format=video_format,
            )
            results.append(result)
        else:
            # Process each topic
            for topic in topics[:VIDEOS_PER_RUN]:
                try:
                    result = self._run_single_topic(
                        topic=topic,
                        platform=platform,
                        formats=formats,
                        voice_id=voice_id,
                        voice_name=voice_name,
                        language=language,
                        run_dir=run_dir,
                        skip_research=skip_research,
                        skip_video=skip_video,
                        use_remotion=use_remotion,
                        profile=profile,
                        video_format=video_format,
                        duration=duration,
                    )
                    results.append(result)
                except Exception as exc:
                    logger.error("Failed to process topic '%s': %s", topic, exc, exc_info=True)
                    results.append({"topic": topic, "error": str(exc), "status": "failed"})

        # ─── Summary ──────────────────────────────────────────────────────
        self._print_summary(results, run_dir)
        return results

    def _run_single_topic(
        self,
        topic: str,
        platform: str,
        formats: list[str],
        voice_id: Optional[str],
        voice_name: Optional[str],
        run_dir: Path,
        skip_research: bool,
        skip_video: bool,
        use_remotion: bool = True,
        language: Optional[str] = None,
        profile: Optional[PlatformProfile] = None,
        video_format: Optional[VideoFormat] = None,
        duration: Optional[int] = None,
    ) -> dict:
        """Run the full pipeline for a single topic."""
        if profile is None or video_format is None:
            profile, video_format = resolve_profile_and_format(platform)

        result = {
            "topic": topic,
            "platform": platform,
            "status": "started",
            "paths": {},
            "timestamp": datetime.now().isoformat(),
        }

        # ─── Step 1: Intelligent Research ──────────────────────────────────
        ideas: list[VideoIdea] = []
        effective_topic = topic
        context_summary = ""
        analysis = None

        if not skip_research:
            logger.info("\n📡 STEP 1: Intelligent Topic Research on '%s'...", topic)
            ideas, analysis = self.researcher.research_topic(
                raw_topic=topic,
                max_results=5,
            )
            if analysis:
                effective_topic = analysis.corrected_topic
                context_summary = analysis.context_summary
                if analysis.has_corrections:
                    logger.info("⚠️ Typo detected in topic: '%s' -> Corrected to '%s' (%s)",
                                topic, effective_topic, analysis.correction_reason)
                    result["original_topic"] = topic
                    result["corrected_topic"] = effective_topic
                    result["correction_reason"] = analysis.correction_reason

            if ideas:
                self.researcher.print_summary(ideas, top=5)
                research_path = self.researcher.save_research(
                    ideas, run_dir / f"research_{self._safe_name(effective_topic)}.json"
                )
                result["paths"]["research"] = str(research_path)

        # ─── Step 2: Script Generation ─────────────────────────────────────
        logger.info("\n✍️  STEP 2: Generating script for '%s'...", effective_topic)
        script = self.script_gen.generate(
            topic=effective_topic,
            platform=platform,
            ideas=ideas[:5] if ideas else [],
            context_summary=context_summary,
            target_duration_s=duration,
        )
        script_path = self.script_gen.save_script(
            script, run_dir / f"script_{self._safe_name(effective_topic)}.json"
        )
        result["paths"]["script"] = str(script_path)
        result["title"] = script.title

        logger.info("   Title: %s", script.title)
        logger.info("   Duration estimate: ~%ds", script.duration_estimate)

        # ─── Step 3: Voice Synthesis ───────────────────────────────────────
        logger.info("\n🎙️  STEP 3: Synthesizing voice...")
        narration_text = script.to_narration()
        audio_path = run_dir / f"audio_{self._safe_name(effective_topic)}.mp3"

        # Use chunked synthesis for optimal VoiceStudio reliability (3-4 sentences per chunk)
        try:
            audio, segment_timings = self.voice.synthesize_chunked(
                text_or_chunks=narration_text,
                output_path=audio_path,
                voice_id=voice_id,
                voice_name=voice_name,
                language=language,
            )
        except Exception as exc:
            logger.warning("synthesize_chunked failed (%s); falling back to direct synthesize...", exc)
            audio = self.voice.synthesize(
                text=narration_text,
                output_path=audio_path,
                voice_id=voice_id,
                voice_name=voice_name,
                language=language,
            )
            segment_timings = []

        if not audio:
            result["status"] = "failed"
            result["error"] = "Voice synthesis failed. Is VoiceStudio running?"
            logger.error("Voice synthesis failed.")
            return result

        result["paths"]["audio"] = str(audio)

        # ─── Step 4: Subtitles ─────────────────────────────────────────────
        logger.info("\n📝 STEP 4: Generating subtitles...")
        audio_ms = self.video_composer.get_audio_duration_ms(audio)
        if segment_timings:
            # Chunk-aligned subtitle generation preventing text bleeding across pauses
            all_chunks = []
            idx = 1
            for seg in segment_timings:
                seg_ms = int(seg.get("duration", 0) * 1000)
                sub_chunks = self.subtitle_gen.generate(seg.get("text", ""), audio_duration_ms=seg_ms)
                offset_ms = int(seg.get("start", 0) * 1000)
                for c in sub_chunks:
                    c.start_ms += offset_ms
                    c.end_ms += offset_ms
                    c.index = idx
                    idx += 1
                    all_chunks.append(c)
            subtitle_chunks = all_chunks
        else:
            subtitle_chunks = self.subtitle_gen.generate(narration_text, audio_ms)

        srt_path = run_dir / f"subtitles_{self._safe_name(topic)}.srt"
        self.subtitle_gen.save(subtitle_chunks, srt_path, fmt="srt")
        result["paths"]["subtitles"] = str(srt_path)
        logger.info("   Generated %d subtitle chunks", len(subtitle_chunks))

        # ─── Step 5: Video Composition & Motion Graphics ───────────────────
        if not skip_video:
            rendered_remotion = None

            # 5A. AI Synthesized Remotion Motion Graphics Video
            if use_remotion and self.remotion.is_available():
                logger.info("\n⚛️  STEP 5: Synthesizing & Rendering Remotion Visuals...")
                remotion_path = run_dir / f"video_remotion_{self._safe_name(effective_topic)}.mp4"

                voice_label = "KittenTTS Explainer"
                if voice_name and voice_name.lower() in ["minhaz", "clone"]:
                    voice_label = "Minhaz Voice"
                elif voice_name:
                    voice_label = f"{voice_name} Voice"

                # Invoke RemotionSynthesizer for dynamic React/TSX scene synthesis
                t_synth_start = time.time()
                audio_dur_s = audio_ms / 1000.0 if audio_ms else 10.0
                v_keywords = getattr(analysis, "primary_keywords", []) + getattr(analysis, "key_concepts", [])

                synthesized_scene = self.synthesizer.synthesize(
                    topic=effective_topic,
                    script=script,
                    audio_duration_s=audio_dur_s,
                    visual_keywords=v_keywords,
                    profile=profile,
                    video_format=video_format,
                )
                synth_comp_id = None
                if synthesized_scene and synthesized_scene.exists():
                    synth_duration = time.time() - t_synth_start
                    logger.info(
                        "   🎨 Scene synthesized in %.2fs -> %s (Version: %s, Model: %s)",
                        synth_duration,
                        synthesized_scene.name,
                        self.synthesizer.skills_version[:10],
                        self.synthesizer.model,
                    )
                    synth_comp_id = "DynamicTopicScene"
                else:
                    logger.info("   🎨 Using rich DynamicExplainer motion graphics engine with VisualMechanismViewport")

                t_render_start = time.time()
                rendered_remotion = self.remotion.render(
                    audio_path=audio,
                    output_path=remotion_path,
                    title=script.title,
                    subtitle=script.hook or getattr(analysis, "context_summary", ""),
                    category=getattr(analysis, "detected_category", "Artificial Intelligence"),
                    voice_badge=voice_label,
                    sections=script.sections,
                    segment_timings=segment_timings,
                    narration_text=narration_text,
                    composition_id=synth_comp_id,
                    profile=profile,
                    video_format=video_format,
                )
                render_duration = time.time() - t_render_start
                if rendered_remotion and rendered_remotion.exists():
                    result["paths"]["video_remotion"] = str(rendered_remotion)
                    size_mb = rendered_remotion.stat().st_size / 1024 / 1024
                    logger.info("   ✅ REMOTION 1080p: %s (%.1f MB in %.1fs)", rendered_remotion.name, size_mb, render_duration)
            elif use_remotion:
                logger.warning("   ⚠️ Remotion not available; falling back to dynamic FFmpeg composition")

            # 5B. Multi-format FFmpeg Delivery Videos (Shorts, TikTok, YouTube)
            # Uses rendered Remotion video as background if available, or dynamic animated gradient
            logger.info("\n🎬 STEP 5B: Composing Multi-Format Delivery Videos...")
            video_base = run_dir / f"video_{self._safe_name(effective_topic)}"
            bg_for_composer = rendered_remotion if (rendered_remotion and rendered_remotion.exists()) else None

            video_results = self.video_composer.compose_multi_format(
                audio_path=audio,
                base_output_path=video_base,
                formats=formats,
                title=script.title,
                subtitle_chunks=subtitle_chunks,
                narration_text=narration_text,
                background_path=bg_for_composer,
            )

            for fmt, path in video_results.items():
                if path:
                    result["paths"][f"video_{fmt}"] = str(path)
                    size_mb = path.stat().st_size / 1024 / 1024
                    logger.info("   ✅ %s: %s (%.1f MB)", fmt.upper(), path.name, size_mb)
                else:
                    logger.warning("   ❌ %s video failed", fmt.upper())

        result["status"] = "completed"
        return result

    def _process_script(
        self,
        script: VideoScript,
        voice_id: Optional[str],
        voice_name: Optional[str],
        formats: list[str],
        run_dir: Path,
        skip_video: bool,
        use_remotion: bool = True,
        language: Optional[str] = None,
        profile: Optional[PlatformProfile] = None,
        video_format: Optional[VideoFormat] = None,
    ) -> dict:
        """Process a pre-built VideoScript through voice synthesis and video."""
        return self._run_single_topic(
            topic=script.title,
            platform=script.platform,
            formats=formats,
            voice_id=voice_id,
            voice_name=voice_name,
            run_dir=run_dir,
            skip_research=True,
            skip_video=skip_video,
            use_remotion=use_remotion,
            language=language,
            profile=profile,
            video_format=video_format,
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _check_voicestudio(self):
        """Warn if VoiceStudio isn't running."""
        logger.info("🔍 Checking VoiceStudio at %s...", VOICESTUDIO_BASE_URL)
        if self.voice.is_running():
            voices = self.voice.list_voices()
            if isinstance(voices, dict):
                voices = voices.get("voices", list(voices.values()))
            if not isinstance(voices, list):
                voices = []
            logger.info("✅ VoiceStudio connected. %d voice(s) available.", len(voices))
            for v in voices[:5]:
                if isinstance(v, dict):
                    logger.info("   • %s (id=%s)", v.get("name", "?"), v.get("id", "?"))
        else:
            logger.warning(
                "⚠️  VoiceStudio not running at %s. "
                "Open VoiceStudio app before running the pipeline, "
                "or set VOICESTUDIO_URL in your .env file.",
                VOICESTUDIO_BASE_URL,
            )

    @staticmethod
    def _safe_name(text: str) -> str:
        """Convert text to a safe filename."""
        import re
        return re.sub(r"[^\w\s-]", "", text)[:40].strip().replace(" ", "_")

    def _print_summary(self, results: list[dict], run_dir: Path):
        """Print a final summary of all produced assets."""
        print("\n" + "═" * 70)
        print("  🎉 PIPELINE COMPLETE")
        print("═" * 70)
        for r in results:
            status_icon = "✅" if r.get("status") == "completed" else "❌"
            print(f"\n  {status_icon} {r.get('title', r.get('topic', '?'))}")
            paths = r.get("paths", {})
            for key, path in paths.items():
                p = Path(path)
                size = ""
                if p.exists():
                    size_b = p.stat().st_size
                    size = f" ({size_b/1024/1024:.1f} MB)" if size_b > 1024*1024 else f" ({size_b/1024:.1f} KB)"
                print(f"     📁 {key:20s} → {p.name}{size}")
            if error := r.get("error"):
                print(f"     ⚠️  Error: {error}")

        print(f"\n  📂 All files in: {run_dir}")
        print("═" * 70 + "\n")


def check_first_run_environment():
    """
    First-run guard: if .env or remotion/node_modules is missing,
    if sys.stdin.isatty() prompt to run setup.py, else exit with an actionable error.
    Never hang on non-interactive runs.
    """
    root_dir = Path(__file__).resolve().parent.parent
    env_file = Path(__file__).resolve().parent / ".env"
    remotion_modules = Path(__file__).resolve().parent / "remotion" / "node_modules"

    missing = []
    if not env_file.exists():
        missing.append(f".env file missing ({env_file})")
    if not remotion_modules.exists():
        missing.append(f"Remotion node_modules missing ({remotion_modules})")

    if missing:
        msg = "[!] OmniStudio first-run environment check failed:\n" + "\n".join(f"    - {m}" for m in missing)
        if sys.stdin.isatty():
            print(msg)
            try:
                ans = input("Would you like to run the Setup Wizard now? [Y/n]: ").strip().lower()
                if ans in ("", "y", "yes"):
                    setup_py = root_dir / "setup.py"
                    if setup_py.exists():
                        import subprocess
                        subprocess.run([sys.executable, str(setup_py)], check=True)
                        return
            except Exception:
                pass
        print(f"\n{msg}\nPlease run 'python setup.py' to configure the required dependencies.")
        sys.exit(1)


# ─── CLI Interface ────────────────────────────────────────────────────────────

def main():
    check_first_run_environment()
    parser = argparse.ArgumentParser(
        description="Content Automation Pipeline — Voice-cloned video content creator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Research and generate one YouTube video
  python pipeline.py --topic "AI productivity tips 2026"

  # Generate a Shorts video without research
  python pipeline.py --topic "Python one-liners" --platform shorts --no-research

  # Research multiple topics
  python pipeline.py --topics "AI tools,ChatGPT tips,Python 2026"

  # Use a specific cloned voice
  python pipeline.py --topic "Tech news" --voice-name "My Voice"

  # Only generate script + audio (no video)
  python pipeline.py --topic "Tech news" --no-video

  # List available voices
  python pipeline.py --list-voices
        """,
    )

    # Content options
    parser.add_argument("--topic", help="Single topic to generate content for")
    parser.add_argument("--topics", help="Comma-separated list of topics")
    parser.add_argument("--platform", default=None,
                        choices=["youtube", "shorts", "reels", "tiktok", "instagram"],
                        help="Target platform preset (default: youtube)")
    parser.add_argument("--ratio", "--aspect-ratio", default=None,
                        choices=["16:9", "9:16", "1:1", "landscape", "portrait", "square"],
                        help="Target aspect ratio (16:9, 9:16, 1:1)")
    parser.add_argument("--formats", default=None,
                        help="Comma-separated output formats (default: matching target platform format)")
    parser.add_argument("--from-script", type=Path,
                        help="Load a pre-generated script JSON file")

    # Voice & Language options
    parser.add_argument("--voice-id", help="VoiceStudio voice ID to use")
    parser.add_argument("--voice-name", help="VoiceStudio voice name to use")
    parser.add_argument("--language", "--lang", default="auto",
                        help="Language code or name (e.g. en, es, fr, bn, hi, auto). Detected automatically by default.")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available VoiceStudio voices and exit")

    # Pipeline control
    parser.add_argument("--duration", type=int, default=None,
                        help="Target duration in seconds (advisory; adjusts script pacing and word count)")
    parser.add_argument("--no-research", action="store_true",
                        help="Skip yt-dlp research step")
    parser.add_argument("--no-video", action="store_true",
                        help="Only generate script and audio, skip video composition")
    parser.add_argument("--remotion", dest="remotion", action="store_true", default=True,
                        help="Render dynamic motion graphics using Remotion (default: True)")
    parser.add_argument("--no-remotion", dest="remotion", action="store_false",
                        help="Disable Remotion motion graphics rendering")
    parser.add_argument("--output-dir", type=Path,
                        help="Custom output directory")

    args = parser.parse_args()

    # Handle --list-voices
    if args.list_voices:
        client = VoiceStudioClient()
        if not client.is_running():
            print(f"❌ VoiceStudio not running at {VOICESTUDIO_BASE_URL}")
            print("   Start VoiceStudio, then run this command again.")
            sys.exit(1)
        voices = client.list_voices()
        if not voices:
            print("No voices found. Create a cloned voice in VoiceStudio first.")
            sys.exit(0)
        print(f"\nAvailable voices ({len(voices)}):")
        print("-" * 50)
        for v in voices:
            vid = v.get("id") or v.get("voice_id", "?")
            name = v.get("name", "unnamed")
            vtype = v.get("type") or v.get("kind", "")
            print(f"  ID: {vid:<20} Name: {name:<25} Type: {vtype}")
        print()
        return

    # Determine topics
    topics = DEFAULT_TOPICS
    if args.topic:
        topics = [args.topic]
    elif args.topics:
        topics = [t.strip() for t in args.topics.split(",") if t.strip()]

    # Load custom script if provided
    custom_script = None
    if args.from_script:
        with open(args.from_script, encoding="utf-8") as f:
            data = json.load(f)
        from script_generator import VideoScript
        custom_script = VideoScript(
            title=data["title"],
            platform=data.get("platform", args.platform),
            hook=data.get("hook", ""),
            sections=data.get("sections", []),
            cta=data.get("cta", ""),
            tags=data.get("tags", []),
            seo_description=data.get("seo_description", ""),
            full_text=data.get("full_narration", ""),
        )

    # Override output dir
    if args.output_dir:
        import config
        config.OUTPUT_DIR = Path(args.output_dir)
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Resolve platform profile and video format with conflict detection
    try:
        profile, video_format = resolve_profile_and_format(args.platform, args.ratio)
    except ArgumentConflictError as err:
        logger.error("Argument conflict: %s", err)
        print(f"\n❌ Configuration Error: {err}\n", file=sys.stderr)
        sys.exit(2)
    except ValueError as err:
        logger.error("Configuration error: %s", err)
        print(f"\n❌ Configuration Error: {err}\n", file=sys.stderr)
        sys.exit(2)

    # Validate duration if provided
    is_valid_dur, dur_msg = validate_duration(args.duration, profile)
    if not is_valid_dur:
        logger.error("Duration error: %s", dur_msg)
        print(f"\n❌ Configuration Error: {dur_msg}\n", file=sys.stderr)
        sys.exit(2)
    elif dur_msg:
        logger.warning("⚠️  %s", dur_msg)
        print(f"\n⚠️  {dur_msg}\n")

    active_formats = [f.strip() for f in args.formats.split(",")] if args.formats else [profile.id]

    # Run pipeline
    pipeline = ContentAutomationPipeline()
    pipeline.run(
        topics=topics,
        platform=profile.id,
        formats=active_formats,
        voice_id=args.voice_id,
        voice_name=args.voice_name,
        language=args.language,
        skip_research=args.no_research,
        skip_video=args.no_video,
        use_remotion=args.remotion,
        custom_script=custom_script,
        profile=profile,
        video_format=video_format,
        duration=args.duration,
    )


if __name__ == "__main__":
    main()
