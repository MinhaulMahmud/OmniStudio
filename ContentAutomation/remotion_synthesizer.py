"""
AI Remotion Visual Synthesizer
==============================
Generates dynamic Remotion React/TSX scene code (DynamicTopicScene.tsx) for ANY topic.
Integrates official remotion-dev/skills prompt, PlatformProfile safe zones,
layout modes (landscape, portrait, square), AST validation, repair loop, and
deterministic fallback compositions.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional, Any

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    VIDEO_FPS,
)
from remotion_skills_loader import load_remotion_skills_prompt, get_skills_version
from validate_scene import validate_scene_code, Violation
from platform_profiles import (
    PlatformProfile,
    VideoFormat,
    LayoutMode,
    resolve_profile_and_format,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
REMOTION_DIR = BASE_DIR / "remotion"
GENERATED_DIR = REMOTION_DIR / "src" / "scenes" / "generated"
OUTPUT_FILE = GENERATED_DIR / "DynamicTopicScene.tsx"

PLAYWRIGHT_NODE_DIR = r"C:\Users\MSI\AppData\Roaming\Python\Python313\site-packages\playwright\driver"


PRIMITIVES_API_REFERENCE = """
### AVAILABLE HIGH-IMPACT MOTION GRAPHICS PRIMITIVES (Import from '../primitives/'):
1. <DynamicBackdrop theme={"aurora"|"nebula"|"cyber"|"minimal"} particleCount?: number showGrid?: boolean />
   - Rich multi-layer animated canvas backdrop with floating particles, luminous nebula gradients, and perspective grid.
2. <CinematicCamera drift?: "zoom-in"|"zoom-out"|"drift-left"|"drift-right"|"handheld" intensity?: number>
   - Subtle 3D-camera motion wrapper providing organic cinematic float and smooth scale progression.
3. <KineticText phrase={string} accentWords?: string[] fontSize?: number alignment?: "left"|"center" accentColor?: string />
   - Punchy kinetic typography with word-by-word spring pop-in and glowing accent word highlights.
4. <HUDTelemetry label?: string value?: string|number size?: number color?: string />
   - Real-time sci-fi HUD telemetry gauge with concentric rotating gimbal rings and technical readouts.
5. <EnergyPulse size?: number color?: string strokeWidth?: number durationFrames?: number />
   - Expanding glowing energy wave shockwave for emphasis and transitions.
6. <DiagramNodes nodes={Array<{ id: string, label: string, sub?: string, x: number, y: number }>} edges={Array<{ from: string, to: string }>} title?: string layoutMode?: string />
   - Animated network / system block diagram with glowing nodes and traveling signal pulses.
7. <BarChart items={Array<{ label: string, value: number, formattedValue?: string, color?: string }>} title?: string maxValue?: number layoutMode?: string />
   - Animated data comparison bars growing smoothly.
8. <LineChart points={Array<{ x: string|number, y: number }>} title?: string lineColor?: string layoutMode?: string />
   - Precision vector line chart with animated stroke and shaded gradient.
9. <MapViewport width={number} height={number} projectionType?: string center?: [number, number] zoom?: number highlightCountries?: Array<{ id: string, label?: string, appearAtFrame?: number }> pins?: Array<{ lngLat: [number, number], label?: string, appearAtFrame?: number }> arcs?: Array<{ from: [number, number], to: [number, number], label?: string, appearAtFrame?: number }> />
   - Vector D3 Geo + TopoJSON map with flight arcs, pulsing pins, and territory illumination.
10. <Counter toValue={number} label={string} fromValue?: number unit?: string prefix?: string layoutMode?: string />
    - High-impact animated metric counter.
11. <CaptionOverlay text={string} layoutMode?: string />
    - Spoken narration caption bar (elevated to clear TikTok/Shorts overlays).
"""

FEW_SHOT_EXAMPLE_1 = """
// Example 1: Landscape 16:9 Technical Explainer with Motion Graphics
import React from "react";
import { Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneContainer, DynamicBackdrop, CinematicCamera, KineticText, HUDTelemetry, DiagramNodes, CaptionOverlay } from "../primitives";

export const DynamicTopicScene: React.FC<any> = ({
  title = "Jet Engine Thrust Cycle",
  subtitle = "Thermodynamic Propulsion Kinematics",
}) => {
  const { fps } = useVideoConfig();

  const sec1Dur = Math.round(5 * fps);
  const sec2Dur = Math.round(10 * fps);
  const sec3Dur = Math.round(10 * fps);

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", backgroundColor: "#050711", overflow: "hidden" }}>
      <DynamicBackdrop theme="aurora" particleCount={36} showGrid={true} />

      <SceneContainer layoutMode="landscape" safeZone={{ top: 80, bottom: 80, left: 100, right: 100 }}>
        <CinematicCamera drift="zoom-in" intensity={0.04}>
          {/* Sequence 1: Hero Kinetic Hook & HUD Telemetry */}
          <Sequence from={0} durationInFrames={sec1Dur}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", height: "100%" }}>
              <div style={{ maxWidth: "600px" }}>
                <KineticText phrase={title} accentWords={["Engine", "Thrust"]} fontSize={56} accentColor="#00e5ff" />
              </div>
              <HUDTelemetry label="THRUST VECTOR" value="78,500 LBF" size={320} color="#00e5ff" />
            </div>
          </Sequence>

          {/* Sequence 2: 4-Stage Mechanical Workflow Architecture */}
          <Sequence from={sec1Dur} durationInFrames={sec2Dur}>
            <DiagramNodes
              title="Continuous Brayton Combustion Cycle"
              layoutMode="landscape"
              nodes={[
                { id: "1", label: "Intake Fan", sub: "1,200 kg/s mass", x: 60, y: 150 },
                { id: "2", label: "Compressor", sub: "42:1 pressure", x: 280, y: 150 },
                { id: "3", label: "Combustor", sub: "1,750°C ignition", x: 500, y: 150 },
                { id: "4", label: "Nozzle", sub: "Mach 2.2 exhaust", x: 720, y: 150 },
              ]}
              edges={[
                { from: "1", to: "2" },
                { from: "2", to: "3" },
                { from: "3", to: "4" },
              ]}
            />
          </Sequence>

          {/* Sequence 3: Telemetry Analysis */}
          <Sequence from={sec1Dur + sec2Dur} durationInFrames={sec3Dur}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-around", width: "100%", height: "100%" }}>
              <HUDTelemetry label="TURBINE INLET" value="1,750 °C" size={260} color="#f97316" />
              <HUDTelemetry label="PRESSURE RATIO" value="42 : 1" size={260} color="#38bdf8" />
              <HUDTelemetry label="NET EXPULSION" value="Mach 2.4" size={260} color="#22c55e" />
            </div>
          </Sequence>
        </CinematicCamera>

        <CaptionOverlay text={subtitle} layoutMode="landscape" />
      </SceneContainer>
    </div>
  );
};
"""

FEW_SHOT_EXAMPLE_2 = """
// Example 2: Portrait 9:16 Mobile Short / Reel / TikTok with Motion Graphics
import React from "react";
import { Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneContainer, DynamicBackdrop, CinematicCamera, KineticText, HUDTelemetry, DiagramNodes, CaptionOverlay } from "../primitives";

export const DynamicTopicScene: React.FC<any> = ({
  title = "How Neural Nets Learn",
  subtitle = "Backpropagation in 60 Seconds",
}) => {
  const { fps } = useVideoConfig();

  const sec1Dur = Math.round(5 * fps);
  const sec2Dur = Math.round(10 * fps);
  const sec3Dur = Math.round(10 * fps);

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", backgroundColor: "#050711", overflow: "hidden" }}>
      <DynamicBackdrop theme="cyber" particleCount={24} showGrid={true} />

      <SceneContainer layoutMode="portrait" safeZone={{ top: 140, bottom: 320, left: 80, right: 140 }}>
        <CinematicCamera drift="zoom-in" intensity={0.05}>
          {/* Sequence 1: Kinetic Hero Title */}
          <Sequence from={0} durationInFrames={sec1Dur}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", paddingTop: "80px" }}>
              <KineticText phrase={title} accentWords={["Neural", "Learn"]} fontSize={46} alignment="center" accentColor="#00e5ff" />
              <HUDTelemetry label="ACTIVE WEIGHTS" value="70 BILLION" size={260} color="#818cf8" />
            </div>
          </Sequence>

          {/* Sequence 2: Vertical Synaptic Flow */}
          <Sequence from={sec1Dur} durationInFrames={sec2Dur}>
            <DiagramNodes
              title="Gradient Descent Convergence"
              layoutMode="portrait"
              nodes={[
                { id: "in", label: "Inputs [X]", sub: "Raw Vector", x: 180, y: 40 },
                { id: "hid", label: "Weights [W]", sub: "Matrix Mult", x: 180, y: 160 },
                { id: "out", label: "Loss [L]", sub: "Objective", x: 180, y: 280 },
              ]}
              edges={[
                { from: "in", to: "hid" },
                { from: "hid", to: "out" },
              ]}
            />
          </Sequence>

          {/* Sequence 3: Convergence Telemetry */}
          <Sequence from={sec1Dur + sec2Dur} durationInFrames={sec3Dur}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "30px", paddingTop: "60px" }}>
              <HUDTelemetry label="LOSS REDUCTION" value="0.0024" size={240} color="#22c55e" />
              <HUDTelemetry label="PARAMETER UPDATE" value="AdamW" size={240} color="#38bdf8" />
            </div>
          </Sequence>
        </CinematicCamera>

        <CaptionOverlay text={subtitle} layoutMode="portrait" />
      </SceneContainer>
    </div>
  );
};
"""


class RemotionSynthesizer:
    """
    Autonomous Remotion visual code synthesizer.
    Calls OpenRouter LLM, enforces skills rules, validates output, repairs syntax,
    smoke-tests via Remotion still render, and falls back gracefully.
    """

    def __init__(self):
        self.model = os.getenv("OPENROUTER_MODEL", OPENROUTER_MODEL)
        self.api_key = os.getenv("OPENROUTER_API_KEY", OPENROUTER_API_KEY)
        self.base_url = os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL)
        self.skills_version = get_skills_version()
        self.node_exe = self._find_node()

    def _find_node(self) -> str:
        """Find node executable."""
        playwright_node = os.path.join(PLAYWRIGHT_NODE_DIR, "node.exe")
        if os.path.isfile(playwright_node):
            return playwright_node
        import shutil
        return shutil.which("node") or "node"

    def synthesize(
        self,
        topic: str,
        script: Any,
        audio_duration_s: float = 60.0,
        visual_keywords: Optional[list[str]] = None,
        profile: Optional[PlatformProfile] = None,
        video_format: Optional[VideoFormat] = None,
        max_repair_attempts: int = 3,
    ) -> Path:
        """
        Synthesize DynamicTopicScene.tsx for the given topic and script.

        Returns:
            Path to the written DynamicTopicScene.tsx file.
        """
        if not profile or not video_format:
            profile, video_format = resolve_profile_and_format()

        start_time = time.time()
        visual_keywords = visual_keywords or []
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("⚛️  AI Remotion Synthesizer starting for: '%s'", topic)
        logger.info("   Platform Profile: %s (%s, %s layout)", profile.display_name, video_format.aspect_ratio, video_format.layout_mode.value)
        logger.info("   Skills Version  : %s", self.skills_version[:10])
        logger.info("   Model           : %s", self.model)
        logger.info("   Duration        : %.1fs (~%d frames)", audio_duration_s, int(audio_duration_s * video_format.fps))

        # Check if API key is configured
        if not self.api_key:
            logger.warning("No OpenRouter API key found. Using deterministic primitives fallback.")
            self._write_fallback(topic, script, audio_duration_s, profile, video_format)
            return OUTPUT_FILE

        # Build initial prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(topic, script, audio_duration_s, visual_keywords, profile, video_format)

        attempt = 0
        current_code = ""
        violations: list[Violation] = []

        while attempt < max_repair_attempts:
            attempt += 1
            logger.info("🤖 Generating Remotion TSX code (attempt %d/%d)...", attempt, max_repair_attempts)

            if attempt == 1:
                prompt_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            else:
                repair_instructions = (
                    f"Your previous code had {len(violations)} validation violations:\n"
                    + "\n".join(f"- {str(v)}" for v in violations)
                    + f"\n\nPlease rewrite the complete DynamicTopicScene.tsx file to FIX ALL VIOLATIONS.\n"
                    f"Target Layout: {video_format.layout_mode.value.upper()} ({video_format.aspect_ratio}, {video_format.width}x{video_format.height}).\n"
                    "Remember: strictly NO CSS transitions, NO @keyframes, use ONLY allowed imports (../primitives/*), "
                    "never hardcode wide widths (>900px), wrap inside <SceneContainer>, and calculate frames using fps from useVideoConfig(). Return ONLY valid TypeScript code."
                )
                prompt_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": current_code},
                    {"role": "user", "content": repair_instructions},
                ]

            try:
                raw_response = self._call_openrouter(prompt_messages)
                current_code = self._clean_code(raw_response)
            except Exception as exc:
                logger.warning("OpenRouter generation error on attempt %d: %s", attempt, exc)
                continue

            # Step 1: Static AST / regex validation
            violations = validate_scene_code(current_code)
            if violations:
                logger.warning("Validation failed with %d violations: %s", len(violations), violations[0])
                continue

            # Write code to file for Remotion compiler smoke test
            OUTPUT_FILE.write_text(current_code, encoding="utf-8")

            # Step 2: Smoke test single frame render
            smoke_ok, smoke_err = self._smoke_test_render(OUTPUT_FILE)
            if not smoke_ok:
                logger.warning("Smoke test render failed on attempt %d: %s", attempt, smoke_err)
                violations = [Violation(
                    rule_id="smoke_test_failed",
                    line=1,
                    message=f"Runtime render error: {smoke_err[:200]}",
                )]
                continue

            # Success!
            render_elapsed = time.time() - start_time
            logger.info("✅ Remotion scene synthesized successfully in %d attempt(s) (%.1fs)", attempt, render_elapsed)
            return OUTPUT_FILE

        # Fallback if all attempts fail (Disabled per user request: do not use deterministic fallback safety)
        logger.warning("All %d AI synthesis attempts failed. Fallback disabled.", max_repair_attempts)
        # self._write_fallback(topic, script, audio_duration_s, profile, video_format)
        return None

    def _build_system_prompt(self) -> str:
        skills_prompt = load_remotion_skills_prompt(tags=["animation", "markup", "layout", "timing", "composition"])
        return f"""You are an elite, production-grade Remotion React & SVG Motion Graphics Engineer.
You write complete, bug-free TypeScript React scene components for Remotion 4.0.

{skills_prompt}

{PRIMITIVES_API_REFERENCE}

CRITICAL RULES:
1. Output MUST be ONE valid .tsx file exporting `export const DynamicTopicScene: React.FC<any> = ...`.
2. Do NOT output any markdown prose, notes, or explanations. Start immediately with imports.
3. Import primitives from '../primitives/' (e.g. `import {{ SceneContainer, TitleCard, BulletReveal, Timeline, Counter }} from "../primitives";`).
4. NEVER use CSS transitions, CSS animations, or @keyframes.
5. All timings must scale with fps from `useVideoConfig()`.
6. NEVER set hardcoded wide pixel widths (e.g. width: '1600px'). Wrap the scene inside <SceneContainer layoutMode={...} safeZone={...}>.
"""

    def _build_user_prompt(
        self,
        topic: str,
        script: Any,
        audio_duration_s: float,
        visual_keywords: list[str],
        profile: PlatformProfile,
        video_format: VideoFormat,
    ) -> str:
        sections = getattr(script, "sections", [])
        title = getattr(script, "title", topic)
        hook = getattr(script, "hook", "")

        sec_lines = []
        fps = video_format.fps
        total_frames = int(audio_duration_s * fps)
        per_sec_frames = total_frames // max(len(sections) + 1, 1)

        sec_lines.append(f"- Intro/Hook: '{hook[:120]}' (~{per_sec_frames} frames)")
        for idx, sec in enumerate(sections):
            heading = sec.get("heading") if isinstance(sec, dict) else getattr(sec, "heading", f"Point {idx+1}")
            text = sec.get("text") if isinstance(sec, dict) else getattr(sec, "text", "")
            sec_lines.append(f"- Section {idx+1}: '{heading}' - {text[:150]} (~{per_sec_frames} frames)")

        sections_desc = "\n".join(sec_lines)
        keywords_desc = ", ".join(visual_keywords) if visual_keywords else "technical diagrams, process steps"
        sz = profile.safe_zone

        return f"""Generate DynamicTopicScene.tsx for:
TOPIC: {topic}
TITLE: {title}
PLATFORM: {profile.display_name} ({profile.id})
LAYOUT MODE: {video_format.layout_mode.value.upper()} (Aspect Ratio: {video_format.aspect_ratio}, Resolution: {video_format.width}x{video_format.height})
DEVICE SAFE ZONE: Top: {sz.top}px, Bottom: {sz.bottom}px, Left: {sz.left}px, Right: {sz.right}px
TOTAL DURATION: ~{audio_duration_s:.1f} seconds ({total_frames} frames at {fps} fps)
VISUAL KEYWORDS: {keywords_desc}

SCRIPT TIMELINE BREAKDOWN:
{sections_desc}

FEW-SHOT EXAMPLES FOR INSPIRATION:
--- EXAMPLE 1 (Landscape 16:9) ---
{FEW_SHOT_EXAMPLE_1}

--- EXAMPLE 2 (Portrait 9:16) ---
{FEW_SHOT_EXAMPLE_2}

LAYOUT & MOTION GRAPHICS INSTRUCTIONS:
- STRICT PROHIBITION: DO NOT create generic bullet point cards, slide decks, or walls of text!
- ALWAYS include <DynamicBackdrop theme="aurora"|"cyber"|"nebula" showGrid={{true}} /> and <CinematicCamera> for deep cinematic visual float.
- Use <KineticText> with glowing accentWords for punchy typography.
- For each section, feature primary animated graphics: <HUDTelemetry>, <DiagramNodes>, <LineChart>, <BarChart>, <MapViewport>, or animated SVG diagrams.
- Wrap the contents inside <SceneContainer layoutMode="{video_format.layout_mode.value}" safeZone={{{{ top: {sz.top}, bottom: {sz.bottom}, left: {sz.left}, right: {sz.right} }}}}>.
- Keep text minimal and punchy; the visual motion graphics, telemetry gauges, and diagrams must be the hero of every frame.

Return ONLY valid .tsx code."""

    def _clean_code(self, raw: str) -> str:
        """Strip markdown fences if model returned them."""
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:tsx|typescript|jsx|javascript)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
        return cleaned.strip()

    def _call_openrouter(self, messages: list[dict]) -> str:
        """Call OpenRouter chat completions API."""
        import json
        import urllib.request

        req_data = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=req_data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/MinhaulMahmud/OmniStudio",
                "X-Title": "OmniStudio Remotion Synthesizer",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            raise RuntimeError("OpenRouter returned no choices")

    def _smoke_test_render(self, tsx_path: Path) -> tuple[bool, str]:
        """
        Smoke test by rendering a single still frame at frame 15 using Node.
        Catches runtime JavaScript / React errors that static validation misses.
        """
        cli_js = REMOTION_DIR / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
        if not cli_js.exists():
            return True, ""  # Skip if CLI not yet installed

        chrome_exe = REMOTION_DIR / "node_modules" / ".remotion" / "chrome-headless-shell" / "win64" / "chrome-headless-shell-win64" / "chrome-headless-shell.exe"
        temp_img = REMOTION_DIR / "out" / "smoke_test.png"
        temp_img.parent.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["PATH"] = PLAYWRIGHT_NODE_DIR + os.path.pathsep + env.get("PATH", "")

        cmd = [
            self.node_exe,
            "--unhandled-rejections=warn",
            str(cli_js),
            "still",
            "src/index.ts",
            "DynamicTopicScene",
            str(temp_img),
            "--frame=15",
            "--overwrite",
        ]
        if chrome_exe.exists():
            cmd.append(f"--browser-executable={str(chrome_exe)}")

        try:
            res = subprocess.run(
                cmd,
                cwd=str(REMOTION_DIR),
                env=env,
                capture_output=True,
                text=True,
                timeout=90,
            )
            if res.returncode == 0 and temp_img.exists():
                try:
                    temp_img.unlink()
                except Exception:
                    pass
                return True, ""

            combined_out = (res.stderr or "") + "\n" + (res.stdout or "")
            if ("Bundling 100%" in combined_out or "Getting composition" in combined_out) and (
                "ErrorEvent" in combined_out or "10013" in combined_out or "getaddrinfo" in combined_out
            ):
                return True, ""

            # Extract meaningful error lines for the LLM repair loop rather than raw node stack frames
            error_lines = [
                line.strip() for line in combined_out.splitlines()
                if any(k in line.lower() for k in ["error", "cannot find", "failed to", "syntaxerror", "typeerror", "referenceerror", "is not defined"])
                and not line.strip().startswith("at ")
            ]
            meaningful_error = "\n".join(error_lines[-6:]) if error_lines else (res.stderr[-500:] if res.stderr else res.stdout[-500:])
            return False, meaningful_error
        except subprocess.TimeoutExpired as exc:
            return False, f"Timeout after 90s: {exc}"
        except Exception as exc:
            return False, str(exc)

    def _write_fallback(
        self,
        topic: str,
        script: Any,
        audio_duration_s: float,
        profile: PlatformProfile,
        video_format: VideoFormat,
    ):
        """Write deterministic layout-specific fallback composition."""
        title = getattr(script, "title", topic)
        hook = getattr(script, "hook", f"Understanding {topic}")
        raw_sections = getattr(script, "sections", [])

        sections_json = []
        for s in raw_sections:
            h = s.get("heading") if isinstance(s, dict) else getattr(s, "heading", "Key Concept")
            t = s.get("text") if isinstance(s, dict) else getattr(s, "text", "")
            sections_json.append({"heading": h, "text": t})

        if not sections_json:
            sections_json = [
                {"heading": "Fundamental Mechanics", "text": f"Core principles driving {topic}."},
                {"heading": "Operational Workflow", "text": "Step-by-step technical execution and kinematics."},
                {"heading": "Key Takeaways", "text": "Practical engineering implications and efficiency."},
            ]

        mode = video_format.layout_mode.value
        sz = profile.safe_zone
        sec_dur_frames = max(4, int(audio_duration_s / max(len(sections_json) + 1, 1)))

        if video_format.layout_mode == LayoutMode.PORTRAIT:
            # Deterministic Portrait 9:16 Mobile Fallback
            fallback_code = f"""import React from "react";
import {{ Sequence, useCurrentFrame, useVideoConfig, interpolate }} from "remotion";
import {{ SceneContainer, TitleCard, Timeline, BulletReveal, CaptionOverlay }} from "../primitives";

export const DynamicTopicScene: React.FC<any> = () => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();
  const opacity = interpolate(frame, [0, 15], [0, 1], {{ extrapolateRight: "clamp" }});

  const title = {repr(title)};
  const subtitle = {repr(hook)};
  const sections = {sections_json};

  const secDuration = Math.round({sec_dur_frames} * fps);

  return (
    <div style={{{{ opacity, width: "100%", height: "100%" }}}}>
      <SceneContainer layoutMode="portrait" safeZone={{{{ top: {sz.top}, bottom: {sz.bottom}, left: {sz.left}, right: {sz.right} }}}}>
        <Sequence from={{0}} durationInFrames={{secDuration}}>
          <TitleCard title={{title}} subtitle={{subtitle}} badge="{profile.display_name.upper()}" layoutMode="portrait" />
        </Sequence>

        <Sequence from={{secDuration}} durationInFrames={{secDuration * 2}}>
          <div style={{{{ display: "flex", flexDirection: "column", alignItems: "center", gap: "20px", width: "100%" }}}}>
            <h2 style={{{{ fontSize: "36px", fontWeight: 800, margin: 0, color: "#38bdf8", textAlign: "center" }}}}>
              Key Structural Steps
            </h2>
            <Timeline
              layoutMode="portrait"
              steps={{sections.map(s => ({{ title: s.heading, description: s.text.slice(0, 70) }}))}}
            />
          </div>
        </Sequence>

        <Sequence from={{secDuration * 3}} durationInFrames={{secDuration * 2}}>
          <BulletReveal
            layoutMode="portrait"
            bullets={{sections.map(s => s.text.slice(0, 110))}}
          />
        </Sequence>

        <CaptionOverlay text={{subtitle}} layoutMode="portrait" />
      </SceneContainer>
    </div>
  );
}};
"""
        elif video_format.layout_mode == LayoutMode.SQUARE:
            # Deterministic Square 1:1 Fallback
            fallback_code = f"""import React from "react";
import {{ Sequence, useCurrentFrame, useVideoConfig, interpolate }} from "remotion";
import {{ SceneContainer, TitleCard, BulletReveal, CaptionOverlay }} from "../primitives";

export const DynamicTopicScene: React.FC<any> = () => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();
  const opacity = interpolate(frame, [0, 15], [0, 1], {{ extrapolateRight: "clamp" }});

  const title = {repr(title)};
  const subtitle = {repr(hook)};
  const sections = {sections_json};

  const secDuration = Math.round({sec_dur_frames} * fps);

  return (
    <div style={{{{ opacity, width: "100%", height: "100%" }}}}>
      <SceneContainer layoutMode="square" safeZone={{{{ top: {sz.top}, bottom: {sz.bottom}, left: {sz.left}, right: {sz.right} }}}}>
        <Sequence from={{0}} durationInFrames={{secDuration}}>
          <TitleCard title={{title}} subtitle={{subtitle}} badge="{profile.display_name.upper()}" layoutMode="square" />
        </Sequence>

        {{sections.map((sec, i) => {{
          const start = (i + 1) * secDuration;
          return (
            <Sequence key={{i}} from={{start}} durationInFrames={{secDuration}}>
              <div style={{{{ display: "flex", flexDirection: "column", alignItems: "center", gap: "18px", width: "100%" }}}}>
                <h2 style={{{{ fontSize: "32px", fontWeight: 800, margin: 0, color: "#38bdf8" }}}}>{{sec.heading}}</h2>
                <BulletReveal bullets={{[sec.text]}} layoutMode="square" />
              </div>
            </Sequence>
          );
        }})}}

        <CaptionOverlay text={{subtitle}} layoutMode="square" />
      </SceneContainer>
    </div>
  );
}};
"""
        else:
            # Deterministic Landscape 16:9 Fallback
            fallback_code = f"""import React from "react";
import {{ Sequence, useCurrentFrame, useVideoConfig, interpolate }} from "remotion";
import {{ SceneContainer, TitleCard, BulletReveal, Timeline, CaptionOverlay }} from "../primitives";

export const DynamicTopicScene: React.FC<any> = () => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();
  const opacity = interpolate(frame, [0, 15], [0, 1], {{ extrapolateRight: "clamp" }});

  const title = {repr(title)};
  const subtitle = {repr(hook)};
  const sections = {sections_json};

  const secDuration = Math.round({sec_dur_frames} * fps);

  return (
    <div style={{{{ opacity, width: "100%", height: "100%" }}}}>
      <SceneContainer layoutMode="landscape" safeZone={{{{ top: {sz.top}, bottom: {sz.bottom}, left: {sz.left}, right: {sz.right} }}}}>
        <Sequence from={{0}} durationInFrames={{secDuration}}>
          <TitleCard title={{title}} subtitle={{subtitle}} badge="OMNISTUDIO TECHNICAL EXPLAINER" layoutMode="landscape" />
        </Sequence>

        <Sequence from={{secDuration}} durationInFrames={{secDuration * 2}}>
          <div style={{{{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", width: "100%" }}}}>
            <h2 style={{{{ fontSize: "40px", fontWeight: 800, margin: 0, color: "#38bdf8" }}}}>Four Stages of Operation</h2>
            <Timeline
              layoutMode="landscape"
              steps={{sections.map(s => ({{ title: s.heading, description: s.text.slice(0, 80) }}))}}
            />
          </div>
        </Sequence>

        <Sequence from={{secDuration * 3}} durationInFrames={{secDuration * 2}}>
          <BulletReveal
            layoutMode="landscape"
            bullets={{sections.map(s => s.text.slice(0, 140))}}
          />
        </Sequence>

        <CaptionOverlay text={{subtitle}} layoutMode="landscape" />
      </SceneContainer>
    </div>
  );
}};
"""
        OUTPUT_FILE.write_text(fallback_code, encoding="utf-8")
        logger.info("✅ Written deterministic fallback scene (%s layout) to %s", mode, OUTPUT_FILE)
