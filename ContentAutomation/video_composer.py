"""
Video Composer
==============
Assembles the final video from:
  - Background video/image/color
  - Narration audio (from VoiceStudio TTS)
  - Subtitle overlays (via FFmpeg drawtext or ASS filter)
  - Intro/outro animations
  - Multiple output formats (YouTube 16:9, Shorts 9:16, TikTok 9:16)

Uses FFmpeg for all video operations. Remotion-style composition is
described in composition_plan.py for future React-based rendering.
"""
from __future__ import annotations

import logging
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from config import (
    FFMPEG_PATH,
    FFPROBE_PATH,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    VIDEO_BITRATE,
    SHORT_WIDTH,
    SHORT_HEIGHT,
    BACKGROUND_COLOR,
    CAPTION_FONT_SIZE,
    CAPTION_FONT_COLOR,
    CAPTION_SHADOW_COLOR,
    CAPTION_POSITION,
    GENERATE_CAPTIONS,
    OUTPUT_DIR,
    ASSETS_DIR,
)
from subtitle_generator import SubtitleGenerator, SubtitleChunk

logger = logging.getLogger(__name__)


class VideoComposer:
    """
    FFmpeg-based video composer for multi-format content production.
    Supports:
      - YouTube 16:9 (1920x1080)
      - Shorts/Reels/TikTok 9:16 (1080x1920)
      - Custom background (video, image, or solid color)
      - Burned-in captions
      - Audio normalization
    """

    FORMAT_CONFIG = {
        "youtube":    {"width": 1920, "height": 1080, "suffix": "_youtube"},
        "shorts":     {"width": 1080, "height": 1920, "suffix": "_shorts"},
        "tiktok":     {"width": 1080, "height": 1920, "suffix": "_tiktok"},
        "instagram":  {"width": 1080, "height": 1080, "suffix": "_instagram"},
    }

    def __init__(self):
        self.ffmpeg = self._find_ffmpeg()
        self.ffprobe = self._find_ffprobe()
        self.subtitle_gen = SubtitleGenerator()

    # ─── FFmpeg Discovery ─────────────────────────────────────────────────────

    def _find_ffmpeg(self) -> str:
        """Locate the FFmpeg binary."""
        # 1. Use configured path from config.py / environment
        if FFMPEG_PATH and self._is_executable(FFMPEG_PATH):
            logger.info("FFmpeg found (config): %s", FFMPEG_PATH)
            return FFMPEG_PATH

        # 2. Try imageio-ffmpeg Python package (auto-installs ffmpeg)
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_exe and self._is_executable(ffmpeg_exe):
                logger.info("FFmpeg found (imageio-ffmpeg): %s", ffmpeg_exe)
                return ffmpeg_exe
        except (ImportError, RuntimeError):
            pass

        # 3. Try shutil.which
        found = shutil.which("ffmpeg")
        if found:
            logger.info("FFmpeg found (PATH): %s", found)
            return found

        # 4. Common Windows locations
        common = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "ffmpeg", "bin", "ffmpeg.exe"),
        ]
        for path in common:
            if path and self._is_executable(path):
                logger.info("FFmpeg found (common path): %s", path)
                return path

        logger.warning(
            "FFmpeg not found! Video composition will fail. "
            "Quick fix: pip install imageio-ffmpeg\n"
            "Or download from https://ffmpeg.org/download.html and add to PATH, "
            "or set FFMPEG_PATH in your .env file."
        )
        return "ffmpeg"  # Return name anyway; will fail at runtime with clear error

    def _find_ffprobe(self) -> str:
        """Locate the FFprobe binary."""
        candidates = [
            FFPROBE_PATH,
            "ffprobe",
            str(Path(self.ffmpeg).parent / "ffprobe.exe"),
            str(Path(self.ffmpeg).parent / "ffprobe"),
        ]
        for candidate in candidates:
            if candidate and self._is_executable(candidate):
                return candidate
        return "ffprobe"

    @staticmethod
    def _is_executable(path: str) -> bool:
        return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)

    # ─── Audio Analysis ───────────────────────────────────────────────────────

    def get_audio_duration_ms(self, audio_path: Path) -> Optional[int]:
        """Get audio file duration in milliseconds using ffprobe or ffmpeg."""
        # 1. Try ffprobe first
        if self.ffprobe and self._is_executable(self.ffprobe):
            try:
                result = subprocess.run(
                    [
                        self.ffprobe, "-v", "quiet",
                        "-print_format", "json",
                        "-show_format",
                        str(audio_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                    duration = float(data.get("format", {}).get("duration", 0))
                    return int(duration * 1000)
            except Exception as exc:
                logger.debug("ffprobe failed: %s", exc)

        # 2. Fall back to parsing ffmpeg -i stderr
        try:
            result = subprocess.run(
                [self.ffmpeg, "-i", str(audio_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Match "Duration: HH:MM:SS.ms"
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
            if match:
                h, m, s = match.groups()
                total_s = int(h) * 3600 + int(m) * 60 + float(s)
                return int(total_s * 1000)
        except Exception as exc:
            logger.warning("Could not get audio duration: %s", exc)

        return None

    # ─── Video Composition ────────────────────────────────────────────────────

    def compose(
        self,
        audio_path: Path,
        output_path: Path,
        title: str = "",
        subtitle_chunks: Optional[list[SubtitleChunk]] = None,
        background_path: Optional[Path] = None,
        format_name: str = "youtube",
        narration_text: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Compose the final video from audio + background + subtitles.

        Args:
            audio_path: Path to the narration audio file.
            output_path: Path for the output MP4 file.
            title: Video title (shown as text overlay if no background).
            subtitle_chunks: Pre-generated subtitle chunks.
            background_path: Optional background video or image.
            format_name: Output format (youtube, shorts, tiktok).
            narration_text: Text to auto-generate subtitles from.

        Returns:
            Path to the composed video, or None on failure.
        """
        fmt = self.FORMAT_CONFIG.get(format_name, self.FORMAT_CONFIG["youtube"])
        width, height = fmt["width"], fmt["height"]

        audio_path = Path(audio_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get audio duration
        audio_ms = self.get_audio_duration_ms(audio_path)
        audio_duration = (audio_ms / 1000) if audio_ms else None
        logger.info("Audio duration: %.1fs", audio_duration or 0)

        # Generate subtitles if needed
        if GENERATE_CAPTIONS and not subtitle_chunks and narration_text:
            subtitle_chunks = self.subtitle_gen.generate(narration_text, audio_ms)

        # Save subtitle file for FFmpeg
        subtitle_file = None
        if subtitle_chunks:
            subtitle_file = output_path.with_suffix(".ass")
            self.subtitle_gen.save(subtitle_chunks, subtitle_file, fmt="ass",
                                   style="reels" if height > width else "default")

        # Build FFmpeg command
        cmd = self._build_ffmpeg_command(
            audio_path=audio_path,
            output_path=output_path,
            width=width,
            height=height,
            audio_duration=audio_duration,
            background_path=background_path,
            subtitle_file=subtitle_file,
            title=title,
        )

        logger.info("🎬 Composing video: %s", output_path.name)
        logger.debug("FFmpeg command: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.returncode == 0:
                size_mb = output_path.stat().st_size / 1024 / 1024 if output_path.exists() else 0
                logger.info("✅ Video composed: %s (%.1f MB)", output_path.name, size_mb)
                return output_path
            else:
                logger.error("FFmpeg failed (code %d):\n%s", result.returncode, result.stderr[-2000:])
                return None
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timed out after 10 minutes")
            return None
        except FileNotFoundError:
            logger.error(
                "FFmpeg not found at '%s'. "
                "Install FFmpeg: https://ffmpeg.org/download.html",
                self.ffmpeg,
            )
            return None

    def _build_ffmpeg_command(
        self,
        audio_path: Path,
        output_path: Path,
        width: int,
        height: int,
        audio_duration: Optional[float],
        background_path: Optional[Path],
        subtitle_file: Optional[Path],
        title: str,
    ) -> list[str]:
        """Build the FFmpeg command for video composition."""
        cmd = [self.ffmpeg, "-y"]  # -y = overwrite output

        # Input 0: Background
        if background_path and background_path.exists():
            suffix = background_path.suffix.lower()
            if suffix in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
                # Loop background video to match audio length
                if audio_duration:
                    cmd += ["-stream_loop", "-1", "-t", str(audio_duration + 1)]
                cmd += ["-i", str(background_path)]
            else:
                # Static image background
                if audio_duration:
                    cmd += ["-loop", "1", "-t", str(audio_duration + 1)]
                cmd += ["-i", str(background_path)]
        else:
            # Dynamic animated tech gradient background instead of a blank canvas
            duration_arg = f":duration={audio_duration + 1}" if audio_duration else ""
            cmd += [
                "-f", "lavfi",
                "-i", f"gradients=s={width}x{height}:c0=0x070714:c1=0x1e1145:speed=0.005:rate={VIDEO_FPS}{duration_arg}",
            ]

        # Input 1: Audio
        cmd += ["-i", str(audio_path)]

        # ── Video filter chain ──────────────────────────────────────────────
        vf_parts = []

        # 1. Scale and crop to target resolution
        vf_parts.append(
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}"
        )

        # 2. Top Title Header Card overlay
        if title and subtitle_file:
            safe_hdr = title[:45].replace("'", "\\'").replace(":", "\\:")
            vf_parts.append(
                f"drawtext=text='{safe_hdr}':fontsize=36:fontcolor=white"
                f":x=(w-text_w)/2:y=60:shadowcolor=black@0.8:shadowx=2:shadowy=2"
                f":box=1:boxcolor=0x070714@0.7:boxborderw=12"
            )

        # 3. Subtitle overlay
        if subtitle_file and subtitle_file.exists():
            # Escape Windows path for FFmpeg
            safe_sub = str(subtitle_file).replace("\\", "/").replace(":", "\\:")
            vf_parts.append(f"ass='{safe_sub}'")
        elif title:
            # Simple text title overlay
            safe_title = title[:60].replace("'", "\\'").replace(":", "\\:")
            vf_parts.append(
                f"drawtext=text='{safe_title}'"
                f":fontsize={CAPTION_FONT_SIZE}"
                f":fontcolor={CAPTION_FONT_COLOR}"
                f":shadowcolor={CAPTION_SHADOW_COLOR}@0.8"
                f":shadowx=2:shadowy=2"
                f":x=(w-text_w)/2:y=h-th-80"
                f":box=1:boxcolor=black@0.4:boxborderw=10"
            )

        vf = ",".join(vf_parts)

        # ── Build filter_complex or vf ──────────────────────────────────────
        cmd += [
            "-vf", vf,
            "-map", "0:v",
            "-map", "1:a",
        ]

        # ── Encoding settings ───────────────────────────────────────────────
        cmd += [
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-b:v", VIDEO_BITRATE,
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-pix_fmt", "yuv420p",   # Required for broad compatibility
            "-movflags", "+faststart",  # Web-optimized
            "-shortest",             # Match video length to shortest input
        ]

        if audio_duration:
            cmd += ["-t", str(audio_duration)]

        cmd.append(str(output_path))
        return cmd

    def compose_multi_format(
        self,
        audio_path: Path,
        base_output_path: Path,
        formats: list[str] = None,
        **kwargs,
    ) -> dict[str, Optional[Path]]:
        """
        Compose the video in multiple formats (YouTube + Shorts etc.).

        Returns:
            Dict mapping format name → output path.
        """
        formats = formats or ["youtube", "shorts"]
        results = {}
        for fmt in formats:
            fmt_config = self.FORMAT_CONFIG.get(fmt, {})
            suffix = fmt_config.get("suffix", f"_{fmt}")
            output = base_output_path.parent / (
                base_output_path.stem + suffix + ".mp4"
            )
            path = self.compose(audio_path, output, format_name=fmt, **kwargs)
            results[fmt] = path
        return results

    def normalize_audio(self, audio_path: Path, output_path: Optional[Path] = None) -> Path:
        """Normalize audio levels using FFmpeg loudnorm filter."""
        output_path = output_path or audio_path.with_stem(audio_path.stem + "_normalized")
        cmd = [
            self.ffmpeg, "-y",
            "-i", str(audio_path),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "44100",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return output_path
        logger.warning("Audio normalization failed; using original")
        return audio_path

    def add_music(
        self,
        video_path: Path,
        music_path: Path,
        output_path: Path,
        music_volume: float = 0.1,  # 10% volume (background)
    ) -> Optional[Path]:
        """
        Mix background music into a composed video.

        Args:
            video_path: Input video with narration audio.
            music_path: Background music file.
            output_path: Output video path.
            music_volume: Music volume relative to narration (0.0–1.0).
        """
        cmd = [
            self.ffmpeg, "-y",
            "-i", str(video_path),
            "-stream_loop", "-1", "-i", str(music_path),
            "-filter_complex",
            f"[1:a]volume={music_volume}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return output_path
        logger.error("Failed to add music: %s", result.stderr[-500:])
        return None
