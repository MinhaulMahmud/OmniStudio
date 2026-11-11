"""
Background Generator — 100% Free, Zero API Keys
=================================================
Generates professional-looking video backgrounds without any external API.

Methods (all free, all local):
  1. FFmpeg-generated animated gradients and patterns
  2. PIL/Pillow-generated static image backgrounds
  3. yt-dlp CC0/Public Domain video downloads (optional)
  4. User-supplied local video/image files

No Pexels API, no Unsplash API, no subscriptions needed.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from config import ASSETS_DIR, FFMPEG_PATH, IMAGE_GENERATION_URL

logger = logging.getLogger(__name__)

BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)


# ─── Free background styles ───────────────────────────────────────────────────

BACKGROUND_STYLES = {
    # Dark tech / AI aesthetic
    "dark_circuit": {
        "type": "lavfi",
        "filter": "color=0x0a0a1a:size={w}x{h}:rate={fps}",
        "description": "Deep dark blue background",
    },
    "dark_gradient": {
        "type": "lavfi",
        "filter": (
            "gradients=size={w}x{h}:rate={fps}:"
            "c0=0x0d0d2b:c1=0x1a0a2e:x0=0:y0=0:x1={w}:y1={h}:nb_frames=1"
        ),
        "description": "Dark purple-blue gradient",
    },
    "animated_bokeh": {
        "type": "lavfi",
        # Plasma-like animated background using geq filter
        "filter": (
            "color=black:size={w}x{h}:rate={fps},geq="
            "r='128+127*sin(2*PI*X/{w}*2+T*0.5)*sin(2*PI*Y/{h}*3+T*0.3)':"
            "g='50+50*cos(2*PI*X/{w}*3+T*0.4)':"
            "b='200+55*sin(2*PI*(X+Y)/{w}*2+T*0.6)'"
        ),
        "description": "Animated dark blue plasma effect",
    },
    "particles": {
        "type": "lavfi",
        # Dark background with subtle animated gradient shift
        "filter": (
            "color=0x060614:size={w}x{h}:rate={fps},geq="
            "r='20+15*sin(PI*X/{w}+T*0.3)*sin(PI*Y/{h}+T*0.2)':"
            "g='10+8*cos(PI*X/{w}*2+T*0.4)':"
            "b='60+40*sin(PI*(X+Y)/{w}+T*0.5)'"
        ),
        "description": "Dark animated particles effect",
    },
    "minimal_dark": {
        "type": "lavfi",
        "filter": "color=0x111111:size={w}x{h}:rate={fps}",
        "description": "Clean dark gray background",
    },
    "gradient_purple": {
        "type": "lavfi",
        "filter": (
            "color=black:size={w}x{h}:rate={fps},geq="
            "r='80+40*sin(PI*X/{w}+T*0.1)':"
            "g='20+10*sin(PI*Y/{h}+T*0.15)':"
            "b='120+60*cos(PI*(X+Y)/{w}*0.5+T*0.08)'"
        ),
        "description": "Deep purple gradient animation",
    },
}

# Public domain / CC0 YouTube videos suitable as backgrounds
# These are playlists/channels with CC0 footage
CC0_BACKGROUND_SEARCHES = [
    "site:youtube.com CC0 background loop dark abstract",
    "ytsearch5:dark abstract loop background CC0 no copyright",
]


class BackgroundManager:
    """
    Manages background assets for video composition.
    Everything is free — no API keys, no subscriptions.
    """

    def __init__(self):
        self.ffmpeg = self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        for path in [FFMPEG_PATH, "ffmpeg"]:
            if path and shutil.which(path):
                return path
            if path and Path(path).is_file():
                return path
        return "ffmpeg"

    # ─── Main Interface ───────────────────────────────────────────────────────

    def get_background(
        self,
        query: Optional[str] = None,
        style: str = "animated_bokeh",
        width: int = 1920,
        height: int = 1080,
        duration: float = 60.0,
        prefer_video: bool = True,
    ) -> Optional[Path]:
        """
        Get or generate a background asset.

        Priority:
          1. User-supplied files in assets/backgrounds/
          2. FFmpeg-generated animated background
          3. PIL-generated static image (if FFmpeg unavailable)
          4. None (VideoComposer uses solid color)
        """
        # 1. Check for user-supplied backgrounds
        local = self._find_local_background(prefer_video)
        if local:
            logger.info("Using local background: %s", local.name)
            return local

        # 2. Try AI background generation if query provided
        if query:
            ai_bg = self.generate_ai_background(prompt=query, width=width, height=height)
            if ai_bg:
                return ai_bg

        # 3. Generate with FFmpeg
        generated = self._generate_ffmpeg_background(
            style=style, width=width, height=height, duration=duration
        )
        if generated:
            return generated

        # 4. PIL static image fallback
        static = self._generate_pil_background(width=width, height=height)
        if static:
            return static

        logger.info("No background generated — using solid color")
        return None

    # ─── Local File Search ────────────────────────────────────────────────────

    def _find_local_background(self, prefer_video: bool = True) -> Optional[Path]:
        """Find a suitable file in assets/backgrounds/."""
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        image_exts = {".jpg", ".jpeg", ".png", ".webp"}

        candidates = [f for f in BACKGROUNDS_DIR.iterdir()
                      if f.suffix.lower() in (video_exts | image_exts)
                      and not f.name.startswith("_")]

        if prefer_video:
            videos = [f for f in candidates if f.suffix.lower() in video_exts]
            if videos:
                return sorted(videos)[0]
        if candidates:
            return sorted(candidates)[0]
        return None

    # ─── FFmpeg Generated Backgrounds ────────────────────────────────────────

    def _generate_ffmpeg_background(
        self,
        style: str = "animated_bokeh",
        width: int = 1920,
        height: int = 1080,
        duration: float = 30.0,
        fps: int = 30,
    ) -> Optional[Path]:
        """
        Generate an animated background video using FFmpeg lavfi filters.
        Completely free, runs locally, looks professional.
        """
        if not shutil.which(self.ffmpeg) and not Path(self.ffmpeg).is_file():
            logger.debug("FFmpeg not available for background generation")
            return None

        style_config = BACKGROUND_STYLES.get(style, BACKGROUND_STYLES["animated_bokeh"])
        cache_key = hashlib.md5(
            f"{style}{width}{height}{int(duration)}{fps}".encode()
        ).hexdigest()[:8]
        output = BACKGROUNDS_DIR / f"_gen_{style}_{cache_key}.mp4"

        if output.exists():
            logger.info("Using cached background: %s", output.name)
            return output

        vf = style_config["filter"].format(w=width, h=height, fps=fps)

        cmd = [
            self.ffmpeg, "-y",
            "-f", "lavfi",
            "-i", vf,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-pix_fmt", "yuv420p",
            str(output),
        ]

        logger.info("🎨 Generating background: %s (%dx%d, %.0fs)", style, width, height, duration)
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and output.exists():
                logger.info("✅ Background generated: %s (%.1f MB)",
                            output.name, output.stat().st_size / 1024 / 1024)
                return output
            else:
                logger.warning("Background generation failed: %s", result.stderr[-300:])
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.debug("FFmpeg background generation failed: %s", exc)
        return None

    def generate_all_styles(
        self,
        width: int = 1920,
        height: int = 1080,
        duration: float = 10.0,
    ) -> dict[str, Optional[Path]]:
        """Pre-generate all background styles for preview."""
        results = {}
        for style in BACKGROUND_STYLES:
            results[style] = self._generate_ffmpeg_background(
                style=style, width=width, height=height, duration=duration
            )
        return results

    # ─── PIL Generated Backgrounds ────────────────────────────────────────────

    def _generate_pil_background(
        self,
        width: int = 1920,
        height: int = 1080,
    ) -> Optional[Path]:
        """
        Generate a static gradient background image using Pillow.
        Fallback when FFmpeg is not available.
        """
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return None

        output = BACKGROUNDS_DIR / f"_gen_gradient_{width}x{height}.jpg"
        if output.exists():
            return output

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Draw a dark diagonal gradient
        for y in range(height):
            ratio = y / height
            r = int(10 + 20 * ratio)
            g = int(5 + 10 * ratio)
            b = int(30 + 50 * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        img.save(str(output), "JPEG", quality=90)
        logger.info("PIL gradient background saved: %s", output.name)
        return output

    # ─── CC0 Download via yt-dlp ──────────────────────────────────────────────

    def download_cc0_background(
        self,
        url: str,
        output_name: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Download a CC0/public domain background video using yt-dlp.
        Only use this with videos you've confirmed are CC0 licensed.

        Example CC0 video URLs:
          - Pixabay: https://pixabay.com/videos/...
          - YouTube CC: (search for "Creative Commons" licensed videos)
        """
        output_name = output_name or f"background_{hashlib.md5(url.encode()).hexdigest()[:8]}.mp4"
        dest = BACKGROUNDS_DIR / output_name
        if dest.exists():
            logger.info("CC0 background already cached: %s", dest.name)
            return dest

        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--format", "bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "-o", str(dest),
            url,
        ]
        logger.info("Downloading CC0 background: %s", url[:60])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and dest.exists():
            logger.info("✅ Background downloaded: %s", dest.name)
            return dest
        else:
            logger.warning("Background download failed: %s", result.stderr[:200])
            return None

    # ─── AI Image Background Generation ───────────────────────────────────────

    def generate_ai_background(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
    ) -> Optional[Path]:
        """
        Generate an AI background image using the configured IMAGE_GENERATION_URL
        (http://localhost:20128/v1/images/generations).
        """
        if not IMAGE_GENERATION_URL:
            return None

        import urllib.request
        import base64

        prompt_hash = hashlib.md5(f"{prompt}_{width}x{height}".encode()).hexdigest()[:8]
        dest = BACKGROUNDS_DIR / f"_ai_{prompt_hash}.png"
        if dest.exists():
            return dest

        payload = json.dumps({
            "prompt": f"cinematic high quality abstract video background, {prompt}, 8k, modern clean aesthetic",
            "size": f"{width}x{height}",
            "n": 1,
            "response_format": "b64_json",
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer omniroute",
        }

        try:
            req = urllib.request.Request(IMAGE_GENERATION_URL, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                items = data.get("data", [])
                if items:
                    b64_data = items[0].get("b64_json")
                    if b64_data:
                        with open(dest, "wb") as f:
                            f.write(base64.b64decode(b64_data))
                        logger.info("✅ AI background generated: %s", dest.name)
                        return dest
                    url = items[0].get("url")
                    if url:
                        urllib.request.urlretrieve(url, str(dest))
                        logger.info("✅ AI background downloaded: %s", dest.name)
                        return dest
        except Exception as exc:
            logger.debug("AI background generation unavailable: %s", exc)

        return None

    # ─── Management ───────────────────────────────────────────────────────────

    def add_local_background(self, path: Path, name: Optional[str] = None) -> Path:
        """Copy a local video/image into the backgrounds folder."""
        path = Path(path)
        dest = BACKGROUNDS_DIR / (name or path.name)
        shutil.copy2(str(path), str(dest))
        logger.info("Background added: %s", dest.name)
        return dest

    def list_backgrounds(self) -> list[dict]:
        """List all background assets (local + generated)."""
        results = []
        exts = {".mp4", ".mov", ".avi", ".jpg", ".jpeg", ".png", ".webp"}
        for f in sorted(BACKGROUNDS_DIR.iterdir()):
            if f.suffix.lower() in exts:
                results.append({
                    "name": f.name,
                    "path": str(f),
                    "size_mb": round(f.stat().st_size / 1024 / 1024, 2),
                    "type": "video" if f.suffix.lower() in {".mp4", ".mov", ".avi"} else "image",
                    "generated": f.name.startswith("_gen_"),
                })
        return results

    def clear_generated(self):
        """Remove auto-generated background cache."""
        removed = 0
        for f in BACKGROUNDS_DIR.glob("_gen_*"):
            f.unlink()
            removed += 1
        logger.info("Cleared %d generated backgrounds", removed)
