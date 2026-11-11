"""
Remotion Skills Loader
======================
Compiles official remotion-dev/skills rules into compact, versioned, swappable prompt sections.
Enforces hard Remotion invariants (MUST / NEVER) and token budgets.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
SKILLS_DIR = BASE_DIR / "skills" / "remotion"
VERSION_FILE = SKILLS_DIR / "SKILLS_VERSION"
CACHE_DIR = BASE_DIR / ".cache" / "skills_prompt"


def get_skills_version() -> str:
    """Read the pinned upstream commit hash or tag of remotion-dev/skills."""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "unknown"


RULES_REGISTRY: list[dict] = [
    {
        "id": "rule_no_css_animations",
        "severity": "hard",
        "tags": ["animation", "markup", "performance"],
        "source_file": "remotion-markup/REFERENCE.md",
        "text": (
            "NEVER use CSS transitions (e.g. transition: all 0.3s), CSS keyframe animations, "
            "or Tailwind animation classes. They freeze or desync in headless video rendering. "
            "You MUST animate strictly through frame-driven useCurrentFrame(), interpolate(), and spring()."
        ),
    },
    {
        "id": "rule_localized_use_current_frame",
        "severity": "hard",
        "tags": ["animation", "markup", "performance"],
        "source_file": "remotion-markup/REFERENCE.md",
        "text": (
            "You MUST call useCurrentFrame() only in small localized visual leaf components, "
            "never at the top level of a giant root scene component. Subscribing the entire root tree "
            "to useCurrentFrame() forces unnecessary re-renders on every frame."
        ),
    },
    {
        "id": "rule_fps_from_video_config",
        "severity": "hard",
        "tags": ["timing", "markup"],
        "source_file": "remotion-markup/REFERENCE.md",
        "text": (
            "You MUST convert seconds to frames using fps from useVideoConfig() (e.g. durationInFrames={Math.round(4 * fps)}). "
            "NEVER hardcode frame counts assuming a fixed 30fps. Keeping timing expressions tied to fps "
            "ensures compositions render correctly at any frame rate."
        ),
    },
    {
        "id": "rule_interpolate_clamping_and_easing",
        "severity": "hard",
        "tags": ["animation", "markup"],
        "source_file": "remotion-markup/REFERENCE.md",
        "text": (
            "When using interpolate(), you MUST always pass { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } "
            "to prevent visual overshoots or NaN values. Use Easing.bezier(0.16, 1, 0.3, 1) or spring() for natural motion."
        ),
    },
    {
        "id": "rule_safe_area_and_viewbox",
        "severity": "hard",
        "tags": ["layout", "markup"],
        "source_file": "remotion-create/video-layout.md",
        "text": (
            "You MUST keep titles, badges, and key information inside a 10% safe-area margin (e.g. padding: 80px 100px). "
            "For custom diagrams and mechanism animations, you MUST use responsive SVG with a viewBox "
            "(e.g. viewBox='0 0 1000 600') and width: '100%'."
        ),
    },
    {
        "id": "rule_import_allowlist",
        "severity": "hard",
        "tags": ["security", "markup"],
        "source_file": "remotion-markup/REFERENCE.md",
        "text": (
            "You MUST import ONLY from: 'react', 'remotion', '@remotion/*', and local primitives from '../primitives/*'. "
            "NEVER import Node.js builtins (fs, path, child_process, os), network clients (fetch, axios), "
            "or evaluate dynamic code (eval, new Function, process.env)."
        ),
    },
    {
        "id": "rule_compose_primitives",
        "severity": "hard",
        "tags": ["composition", "primitives"],
        "source_file": "remotion-markup/multi-scene-video.md",
        "text": (
            "You MUST compose scenes primarily using the tested primitives from '../primitives/' "
            "(TitleCard, BulletReveal, BarChart, LineChart, Timeline, DiagramNodes, Counter, CaptionOverlay). "
            "Custom SVG elements are allowed only for topic-specific diagrams (e.g. turbine blades, DNA helices), "
            "kept modular and isolated in their own components."
        ),
    },
    # Soft Guidance Rules
    {
        "id": "rule_soft_perceptual_scale",
        "severity": "soft",
        "tags": ["animation", "markup"],
        "source_file": "remotion-markup/REFERENCE.md",
        "text": (
            "Prefer inline CSS transform shorthands (scale, translate, rotate) over full transform strings. "
            "For scale animations with spring easing, output: 'perceptual-scale' provides smoother visual scaling."
        ),
    },
    {
        "id": "rule_soft_sequence_separation",
        "severity": "soft",
        "tags": ["transitions", "timing"],
        "source_file": "remotion-markup/sequencing.md",
        "text": (
            "Organize video sections into distinct <Sequence from={startFrame} durationInFrames={durFrames}> blocks "
            "aligned with narration audio timings. Each sequence should have a clean entrance and exit."
        ),
    },
    {
        "id": "rule_soft_color_palette",
        "severity": "soft",
        "tags": ["layout", "styling"],
        "source_file": "remotion-create/video-layout.md",
        "text": (
            "Use modern technical dark palettes: deep slate background (#070b14, #0b0f19), "
            "vibrant cyber accents (cyan #38bdf8, violet #818cf8, amber #f59e0b, emerald #10b981), "
            "and subtle glow drop-shadows."
        ),
    },
    {
        "id": "rule_soft_voiceover_sync",
        "severity": "soft",
        "tags": ["voiceover", "timing"],
        "source_file": "remotion-markup/voiceover.md",
        "text": (
            "Ensure on-screen visual reveals (bullet points, diagram highlights, data surges) occur precisely "
            "as the voiceover mentions them, avoiding revealing all information ahead of narration."
        ),
    },
]


def _cache_key(tags: Optional[list[str]], version: str) -> str:
    tags_str = "_".join(sorted(tags)) if tags else "all"
    return f"prompt_{version[:12]}_{tags_str}.txt"


def load_remotion_skills_prompt(
    tags: Optional[list[str]] = None,
    max_tokens: int = 2500,
) -> str:
    """
    Compile official remotion-dev/skills rules into a versioned, cached prompt.

    Args:
        tags: Optional filter for rule categories (e.g. ["animation", "layout"]).
        max_tokens: Approximate token budget (len(text)//4).

    Returns:
        Formatted prompt section with Hard rules (MUST/NEVER) first, followed by Soft guidance.
    """
    version = get_skills_version()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / _cache_key(tags, version)

    if cache_file.exists():
        try:
            return cache_file.read_text(encoding="utf-8")
        except Exception:
            pass

    # Filter rules by tag
    matching_rules = []
    for r in RULES_REGISTRY:
        if tags is None or any(t in r["tags"] for t in tags):
            matching_rules.append(r)

    hard_rules = [r for r in matching_rules if r["severity"] == "hard"]
    soft_rules = [r for r in matching_rules if r["severity"] == "soft"]

    # Build prompt string
    lines = [
        f"### REMOTION BEST PRACTICES & RULES (Version: {version[:10]})",
        "You must generate valid, production-ready React/TypeScript Remotion scene code following these official guidelines:",
        "",
        "#### MANDATORY HARD RULES (MUST / NEVER):",
    ]
    for r in hard_rules:
        lines.append(f"- [{r['id']}] {r['text']}")

    lines.append("")
    lines.append("#### DESIGN & QUALITY GUIDANCE:")

    # Add soft rules while respecting max_tokens budget (tokens approx len(text)//4)
    current_text = "\n".join(lines)
    for r in soft_rules:
        addition = f"- [{r['id']}] {r['text']}\n"
        if (len(current_text) + len(addition)) // 4 > max_tokens:
            break
        lines.append(f"- [{r['id']}] {r['text']}")
        current_text = "\n".join(lines)

    compiled_prompt = "\n".join(lines)

    # Save to disk cache
    try:
        cache_file.write_text(compiled_prompt, encoding="utf-8")
    except Exception as exc:
        logger.debug("Could not write skills prompt cache: %s", exc)

    return compiled_prompt
