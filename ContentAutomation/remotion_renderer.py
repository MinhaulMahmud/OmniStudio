"""
Remotion Renderer
=================
Renders animated React motion graphics using Remotion.
Integrates synchronized VoiceStudio cloned audio narration, dynamic visual cards,
real-time audio waveforms, timeline progress bars, and burned-in typography.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import (
    BASE_DIR,
    OUTPUT_DIR,
    VIDEO_FPS,
)

logger = logging.getLogger(__name__)

PLAYWRIGHT_NODE_DIR = r"C:\Users\MSI\AppData\Roaming\Python\Python313\site-packages\playwright\driver"
BUN_BIN_DIR = r"C:\Users\MSI\.bun\bin"
REMOTION_DIR = BASE_DIR / "remotion"


class RemotionRenderer:
    """
    Orchestrates Remotion video compilation and rendering.
    """

    def __init__(self, remotion_dir: Optional[Path] = None):
        self.remotion_dir = Path(remotion_dir or REMOTION_DIR).resolve()
        self.node_dir = PLAYWRIGHT_NODE_DIR
        self.node_exe = self._find_node()
        self.cli_js = self._find_cli_js()
        self.env = self._build_env()

    def _find_node(self) -> str:
        """Find Node.js executable."""
        playwright_node = os.path.join(self.node_dir, "node.exe")
        if os.path.isfile(playwright_node):
            return playwright_node
        found = shutil.which("node")
        return found or "node"

    def _find_cli_js(self) -> Optional[Path]:
        """Find Remotion CLI javascript entry point."""
        candidate = self.remotion_dir / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
        if candidate.exists():
            return candidate
        return None

    def _build_env(self) -> dict:
        """Ensure node and bun are in PATH for child processes."""
        env = os.environ.copy()
        current_path = env.get("PATH", "")
        extra_paths = []
        if os.path.isdir(self.node_dir) and self.node_dir.lower() not in current_path.lower():
            extra_paths.append(self.node_dir)
        if os.path.isdir(BUN_BIN_DIR) and BUN_BIN_DIR.lower() not in current_path.lower():
            extra_paths.append(BUN_BIN_DIR)

        if extra_paths:
            env["PATH"] = os.path.pathsep.join(extra_paths) + os.path.pathsep + current_path
        return env

    def is_available(self) -> bool:
        """Check if Remotion and Node.js are available to render."""
        return bool(self.node_exe and os.path.isfile(self.node_exe) and self.cli_js and self.cli_js.exists())

    def render(
        self,
        audio_path: Path,
        output_path: Path,
        title: str,
        subtitle: str = "",
        category: str = "Technology & AI",
        voice_badge: str = "KittenTTS Explainer",
        sections: Optional[list[dict]] = None,
        segment_timings: Optional[list[dict]] = None,
        narration_text: str = "",
        composition_id: Optional[str] = None,
        fps: int = VIDEO_FPS,
        profile: Optional[Any] = None,
        video_format: Optional[Any] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Optional[Path]:
        """
        Render a motion graphics video synchronized with audio narration.
        """
        if not self.is_available():
            logger.warning("Remotion or Node.js environment is not available.")
            return None

        # Resolve target dimensions and layout mode
        target_width = 1920
        target_height = 1080
        target_aspect_ratio = "16:9"
        target_layout_mode = "landscape"

        if video_format is not None:
            target_width = getattr(video_format, "width", target_width)
            target_height = getattr(video_format, "height", target_height)
            target_aspect_ratio = getattr(video_format, "aspect_ratio", target_aspect_ratio)
            layout_mode_attr = getattr(video_format, "layout_mode", None)
            if hasattr(layout_mode_attr, "value"):
                target_layout_mode = layout_mode_attr.value
            elif layout_mode_attr:
                target_layout_mode = str(layout_mode_attr)
        elif profile is not None and hasattr(profile, "format"):
            fmt = profile.format
            target_width = getattr(fmt, "width", target_width)
            target_height = getattr(fmt, "height", target_height)
            target_aspect_ratio = getattr(fmt, "aspect_ratio", target_aspect_ratio)
            layout_mode_attr = getattr(fmt, "layout_mode", None)
            if hasattr(layout_mode_attr, "value"):
                target_layout_mode = layout_mode_attr.value
            elif layout_mode_attr:
                target_layout_mode = str(layout_mode_attr)

        if width is not None:
            target_width = width
        if height is not None:
            target_height = height

        audio_path = Path(audio_path).resolve()
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        public_dir = self.remotion_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)

        # Copy audio file into public folder for Remotion staticFile()
        audio_file_name = f"audio_{output_path.stem}.mp3"
        dest_audio = public_dir / audio_file_name
        try:
            shutil.copy2(audio_path, dest_audio)
        except Exception as exc:
            logger.warning("Could not copy audio to remotion public dir (%s); copying as current_narration.mp3", exc)
            audio_file_name = "current_narration.mp3"
            dest_audio = public_dir / audio_file_name
            shutil.copy2(audio_path, dest_audio)

        # Build section timeline
        dynamic_sections = []
        cumulative_frame = 0

        # If we have segment timings from chunked VoiceStudio synthesis:
        if segment_timings:
            for i, seg in enumerate(segment_timings):
                dur_sec = seg.get("duration", 4.0)
                dur_frames = max(30, int(round(dur_sec * fps)))
                text = seg.get("text", "")
                heading = seg.get("heading") or f"Section {i+1}"
                badge = seg.get("badge") or f"Step {i+1}"

                bullets = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 8][:3]
                if not bullets and text:
                    bullets = [text]

                dynamic_sections.append({
                    "heading": heading,
                    "text": text,
                    "startFrame": cumulative_frame,
                    "durationFrames": dur_frames,
                    "badge": badge,
                    "bullets": bullets,
                })
                cumulative_frame += dur_frames
        elif sections:
            # Estimate from script sections
            for i, sec in enumerate(sections):
                hint = sec.get("duration_hint", 60)
                dur_frames = int(hint * fps)
                text = sec.get("text", "")
                bullets = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 8][:3]
                dynamic_sections.append({
                    "heading": sec.get("heading", f"Key Point {i+1}"),
                    "text": text,
                    "startFrame": cumulative_frame,
                    "durationFrames": dur_frames,
                    "badge": f"Point {i+1}",
                    "bullets": bullets or [text],
                })
                cumulative_frame += dur_frames
        else:
            # Single hero slide
            from video_composer import VideoComposer
            vc = VideoComposer()
            dur_ms = vc.get_audio_duration_ms(audio_path) or 10000
            dur_frames = max(30, int(round((dur_ms / 1000) * fps)))
            dynamic_sections.append({
                "heading": title,
                "text": narration_text or subtitle or title,
                "startFrame": 0,
                "durationFrames": dur_frames,
                "badge": category,
                "bullets": [narration_text[:150]] if narration_text else [subtitle],
            })
            cumulative_frame = dur_frames

        total_frames = max(60, cumulative_frame)

        # Decide composition ID
        title_lower = title.lower()
        is_model_weights_topic = any(k in title_lower for k in ["model weight", "compute power", "vram", "quantization", "bandwidth"])
        is_gearbox_topic = any(k in title_lower for k in ["gearbox", "gear box", "transmission", "bike gear", "motorcycle gear"])
        dynamic_scene_file = self.remotion_dir / "src" / "scenes" / "generated" / "DynamicTopicScene.tsx"

        if not composition_id:
            if dynamic_scene_file.exists():
                composition_id = "DynamicTopicScene"
            elif is_gearbox_topic and abs(total_frames - 1600) < 90:
                composition_id = "BikeGearboxExplainer"
            elif is_model_weights_topic and abs(total_frames - 2367) < 90:
                composition_id = "ModelWeightsExplainer"
            else:
                composition_id = "DynamicExplainer"

        # Prepare Props JSON file
        props_data = {
            "title": title,
            "subtitle": subtitle or f"VoiceStudio synthesis with {category}",
            "category": category,
            "voiceBadge": voice_badge,
            "sections": dynamic_sections,
            "totalFrames": total_frames,
            "audioFile": audio_file_name,
            "width": target_width,
            "height": target_height,
            "aspectRatio": target_aspect_ratio,
            "layoutMode": target_layout_mode,
        }

        props_file = self.remotion_dir / f"props_{output_path.stem}.json"
        with open(props_file, "w", encoding="utf-8") as f:
            json.dump(props_data, f, indent=2, ensure_ascii=False)

        # Locate Chrome Headless Shell
        chrome_exe = self.remotion_dir / "node_modules" / ".remotion" / "chrome-headless-shell" / "win64" / "chrome-headless-shell-win64" / "chrome-headless-shell.exe"

        # Build Remotion render command directly invoking node with remotion-cli.js
        cmd = [
            self.node_exe,
            "--unhandled-rejections=warn",
            str(self.cli_js),
            "render",
            "src/index.ts",
            composition_id,
            str(output_path),
            f"--props={str(props_file)}",
            f"--width={target_width}",
            f"--height={target_height}",
            "--codec=h264",
            "--overwrite",
        ]
        if chrome_exe.exists():
            cmd.append(f"--browser-executable={str(chrome_exe)}")

        logger.info("⚛️  Rendering Remotion motion graphics...")
        logger.info("   Composition: %s (%d frames / ~%.1fs)", composition_id, total_frames, total_frames / fps)
        logger.info("   Output: %s", output_path.name)

        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.remotion_dir),
                env=self.env,
                capture_output=True,
                text=True,
                timeout=1200,  # 20 min max
            )
            if res.returncode == 0 and output_path.exists():
                size_mb = output_path.stat().st_size / 1024 / 1024
                logger.info("✅ Remotion video successfully rendered: %s (%.1f MB)", output_path.name, size_mb)
                # Cleanup temp props
                try:
                    props_file.unlink()
                except Exception:
                    pass
                return output_path
            else:
                logger.error("Remotion render failed (code %d):\n%s", res.returncode, res.stderr[-1500:] if res.stderr else res.stdout[-1500:])
                return None
        except subprocess.TimeoutExpired:
            logger.error("Remotion render timed out.")
            return None
        except Exception as exc:
            logger.error("Remotion invocation error: %s", exc)
            return None
