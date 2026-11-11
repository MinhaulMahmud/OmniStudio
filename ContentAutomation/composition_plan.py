"""
Remotion-Style Composition Plan
=================================
This module describes how to extend the content automation pipeline
with Remotion (React-based video rendering) for professional motion graphics.

Remotion allows you to write video compositions in React/TypeScript,
which is ideal for:
  - Animated title cards and lower thirds
  - Text kinetic animations synchronized to audio
  - Dynamic data visualizations
  - Transition effects between sections

Installation (requires Node.js 18+):
  npm create video@latest
  npm install @remotion/cli @remotion/player

Usage Pattern:
  1. Generate script + audio with this Python pipeline
  2. Render motion graphics frames with Remotion
  3. Composite with FFmpeg (merge Remotion output + audio)

See: https://www.remotion.dev/docs/

This file also defines the composition_plan JSON structure used to
configure both FFmpeg and future Remotion rendering.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TextAnimation:
    """A text overlay animation for Remotion."""
    text: str
    start_frame: int = 0
    end_frame: int = 90
    animation: str = "fade_in"   # fade_in | slide_up | bounce | typewriter
    x: str = "50%"               # CSS position
    y: str = "85%"
    font_size: int = 60
    font_color: str = "#FFFFFF"
    font_family: str = "Inter"
    font_weight: str = "bold"
    shadow: bool = True
    background: str = "rgba(0,0,0,0.5)"


@dataclass
class Section:
    """A timed section of the video composition."""
    name: str
    start_seconds: float
    end_seconds: float
    audio_file: Optional[str] = None
    background: Optional[str] = None      # file path or color
    text_animations: list[TextAnimation] = field(default_factory=list)
    transitions: str = "crossfade"        # cut | crossfade | fade_black


@dataclass
class CompositionPlan:
    """
    A complete video composition plan.

    This can drive either:
      - The FFmpeg-based VideoComposer (current implementation)
      - A Remotion React renderer (future implementation)
    """
    title: str
    platform: str             # youtube | shorts | tiktok
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration_seconds: float = 0
    audio_file: str = ""
    subtitle_file: str = ""
    background_file: str = ""
    background_color: str = "#0d0d1a"
    sections: list[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_remotion_props(self) -> dict:
        """Convert to Remotion inputProps format."""
        return {
            "title": self.title,
            "platform": self.platform,
            "durationInFrames": int(self.duration_seconds * self.fps),
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "audioFile": self.audio_file,
            "subtitleFile": self.subtitle_file,
            "backgroundColor": self.background_color,
            "backgroundFile": self.background_file,
            "sections": [asdict(s) for s in self.sections],
        }

    def save(self, path: Path) -> Path:
        """Save the composition plan as JSON."""
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        return path

    @classmethod
    def from_pipeline_result(
        cls,
        title: str,
        platform: str,
        audio_path: Path,
        subtitle_path: Optional[Path] = None,
        background_path: Optional[Path] = None,
        duration_seconds: float = 0,
    ) -> "CompositionPlan":
        """Create a composition plan from pipeline output paths."""
        width, height = {
            "youtube": (1920, 1080),
            "shorts": (1080, 1920),
            "tiktok": (1080, 1920),
            "instagram": (1080, 1080),
        }.get(platform, (1920, 1080))

        return cls(
            title=title,
            platform=platform,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            audio_file=str(audio_path) if audio_path else "",
            subtitle_file=str(subtitle_path) if subtitle_path else "",
            background_file=str(background_path) if background_path else "",
        )


def render_with_remotion(
    composition_plan: CompositionPlan,
    output_path: Path,
    remotion_project: Optional[Path] = None,
) -> Optional[Path]:
    """
    Render a video using Remotion CLI.

    Prerequisites:
      1. Install Node.js 18+ from https://nodejs.org/
      2. Set up Remotion project:
         cd ContentAutomation/remotion
         npm install
      3. Run this function.

    Args:
        composition_plan: The composition definition.
        output_path: Where to save the rendered video.
        remotion_project: Path to the Remotion project directory.

    Returns:
        Path to rendered video, or None if Remotion is not available.
    """
    import subprocess, shutil

    remotion_project = remotion_project or Path(__file__).parent / "remotion"
    if not remotion_project.exists():
        logger.warning(
            "Remotion project not found at %s. "
            "Run setup_remotion() to initialize it.",
            remotion_project,
        )
        return None

    npx = shutil.which("npx")
    if not npx:
        logger.warning("Node.js/npx not found. Install Node.js to use Remotion.")
        return None

    # Save props to temp file
    props_file = remotion_project / "composition_props.json"
    with open(props_file, "w") as f:
        json.dump(composition_plan.to_remotion_props(), f, indent=2)

    cmd = [
        npx, "remotion", "render",
        "ContentAutomation",           # Composition ID in Remotion
        str(output_path),
        "--props", str(props_file),
        "--codec", "h264",
    ]

    logger.info("🎬 Rendering with Remotion: %s", output_path.name)
    result = subprocess.run(cmd, cwd=str(remotion_project), capture_output=True, text=True, timeout=600)
    if result.returncode == 0:
        logger.info("✅ Remotion render complete: %s", output_path)
        return output_path
    else:
        logger.error("Remotion render failed: %s", result.stderr[-1000:])
        return None


def setup_remotion(project_dir: Optional[Path] = None) -> Path:
    """
    Bootstrap a Remotion project for video motion graphics.
    Call this once to set up the Remotion renderer.
    """
    import subprocess, shutil

    project_dir = project_dir or Path(__file__).parent / "remotion"
    project_dir.mkdir(parents=True, exist_ok=True)

    if not shutil.which("npm"):
        print("❌ npm not found. Install Node.js from https://nodejs.org/")
        return project_dir

    if (project_dir / "package.json").exists():
        print(f"✅ Remotion project already exists at {project_dir}")
        return project_dir

    print(f"🚀 Initializing Remotion project at {project_dir}...")
    result = subprocess.run(
        ["npm", "create", "video@latest", "--", "--yes"],
        cwd=str(project_dir.parent),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"✅ Remotion project created at {project_dir}")
    else:
        print(f"❌ Remotion setup failed: {result.stderr}")

    return project_dir
