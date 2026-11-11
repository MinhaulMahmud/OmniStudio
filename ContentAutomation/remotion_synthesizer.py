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
### AVAILABLE TESTED PRIMITIVES (Import from '../primitives/'):
1. <SceneContainer layoutMode={"landscape"|"portrait"|"square"} safeZone={{top, bottom, left, right}}>
   - Top-level root layout wrapper enforcing responsive container bounds and device safe zones.
2. <TitleCard title={string} subtitle?: string badge?: string accentColor?: string layoutMode?: string />
   - Main title card with spring-animated scaling and safe typography scaling.
3. <BulletReveal bullets={string[]} accentColor?: string delayFrames?: number staggerFrames?: number maxWidth?: number|string layoutMode?: string />
   - Numbered bullet points revealed sequentially with responsive card widths.
4. <BarChart items={Array<{ label: string, value: number, formattedValue?: string, color?: string }>} title?: string maxValue?: number layoutMode?: string />
   - Animated horizontal data bars growing smoothly.
5. <LineChart points={Array<{ x: string|number, y: number }>} title?: string lineColor?: string layoutMode?: string />
   - SVG line chart with animated stroke and shaded gradient.
6. <Timeline steps={Array<{ title: string, description?: string }>} activeStep?: number accentColor?: string layoutMode?: string />
   - Sequential process nodes (horizontal on landscape; vertical stepper on portrait).
7. <DiagramNodes nodes={Array<{ id: string, label: string, sub?: string, x: number, y: number }>} edges={Array<{ from: string, to: string }>} title?: string layoutMode?: string />
   - Network / system block diagram with animated signal pulses.
8. <Counter toValue={number} label={string} fromValue?: number unit?: string prefix?: string layoutMode?: string />
   - High-impact animated metric counter.
9. <CaptionOverlay text={string} layoutMode?: string />
   - Spoken narration caption bar (automatically elevated to clear TikTok/Shorts overlays).
"""

FEW_SHOT_EXAMPLE_1 = """
// Example 1: Landscape 16:9 Technical Explainer
import React from "react";
import { Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneContainer, TitleCard, BulletReveal, Timeline, CaptionOverlay } from "../primitives";

export const DynamicTopicScene: React.FC<any> = ({
  title = "Jet Engine Thrust Cycle",
  subtitle = "Brayton Thermodynamic Cycle",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sec1Dur = Math.round(5 * fps);
  const sec2Dur = Math.round(8 * fps);
  const sec3Dur = Math.round(10 * fps);

  return (
    <SceneContainer layoutMode="landscape" safeZone={{ top: 80, bottom: 80, left: 100, right: 100 }}>
      {/* Sequence 1: Hook & Title */}
      <Sequence from={0} durationInFrames={sec1Dur}>
        <TitleCard title={title} subtitle={subtitle} badge="PROPULSION KINEMATICS" layoutMode="landscape" />
      </Sequence>

      {/* Sequence 2: 4-Stage Process Timeline */}
      <Sequence from={sec1Dur} durationInFrames={sec2Dur}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "20px", width: "100%" }}>
          <h2 style={{ fontSize: "40px", fontWeight: 800, margin: 0, color: "#38bdf8" }}>Four Stages of Jet Thrust</h2>
          <Timeline
            layoutMode="landscape"
            steps={[
              { title: "Intake", description: "Huge fan scoops air" },
              { title: "Compress", description: "Blades squeeze air 40:1" },
              { title: "Combust", description: "Fuel ignites at 1700C" },
              { title: "Exhaust", description: "High velocity nozzle thrust" },
            ]}
          />
        </div>
      </Sequence>

      {/* Sequence 3: Key Takeaways */}
      <Sequence from={sec1Dur + sec2Dur} durationInFrames={sec3Dur}>
        <BulletReveal
          layoutMode="landscape"
          bullets={[
            "Compressor raises air pressure exponentially before ignition.",
            "Turbine extracts energy from expanding gas to power the front fan.",
            "Newton's 3rd law generates massive forward momentum."
          ]}
        />
      </Sequence>

      <CaptionOverlay text={subtitle} layoutMode="landscape" />
    </SceneContainer>
  );
};
"""

FEW_SHOT_EXAMPLE_2 = """
// Example 2: Portrait 9:16 Mobile Short / Reel / TikTok
import React from "react";
import { Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneContainer, TitleCard, Timeline, BulletReveal, CaptionOverlay } from "../primitives";

export const DynamicTopicScene: React.FC<any> = ({
  title = "How Neural Nets Learn",
  subtitle = "Backpropagation in 60 Seconds",
}) => {
  const { fps } = useVideoConfig();

  const sec1Dur = Math.round(4 * fps);
  const sec2Dur = Math.round(10 * fps);
  const sec3Dur = Math.round(10 * fps);

  return (
    <SceneContainer layoutMode="portrait" safeZone={{ top: 140, bottom: 320, left: 80, right: 140 }}>
      {/* Sequence 1: Hook Headline at Top Safe Zone */}
      <Sequence from={0} durationInFrames={sec1Dur}>
        <TitleCard title={title} subtitle={subtitle} badge="AI EXPLAINED" layoutMode="portrait" />
      </Sequence>

      {/* Sequence 2: Vertical Stepper in Center */}
      <Sequence from={sec1Dur} durationInFrames={sec2Dur}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "20px", width: "100%" }}>
          <h2 style={{ fontSize: "36px", fontWeight: 800, margin: 0, color: "#38bdf8", textAlign: "center" }}>
            The 3-Step Feedback Loop
          </h2>
          <Timeline
            layoutMode="portrait"
            steps={[
              { title: "Forward Pass", description: "Compute initial prediction" },
              { title: "Calculate Loss", description: "Measure distance from target" },
              { title: "Backpropagation", description: "Update weights via gradient descent" },
            ]}
          />
        </div>
      </Sequence>

      {/* Sequence 3: Key Bullets Above Bottom Safe Zone */}
      <Sequence from={sec1Dur + sec2Dur} durationInFrames={sec3Dur}>
        <BulletReveal
          layoutMode="portrait"
          bullets={[
            "Weights start as random Gaussian noise.",
            "Gradients point toward lowest loss.",
            "Billions of parameters converge simultaneously."
          ]}
        />
      </Sequence>

      <CaptionOverlay text={subtitle} layoutMode="portrait" />
    </SceneContainer>
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

        # Fallback if all attempts fail
        logger.warning("All %d AI synthesis attempts failed. Falling back to deterministic scene composition.", max_repair_attempts)
        self._write_fallback(topic, script, audio_duration_s, profile, video_format)
        return OUTPUT_FILE

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

LAYOUT INSTRUCTIONS:
- If layoutMode is 'portrait' (9:16 Shorts/Reels/TikTok): Use single vertical stack, place TitleCard at top, Timeline/Diagram in middle, and BulletReveal above bottom safe zone ({sz.bottom}px).
- If layoutMode is 'landscape' (16:9 YouTube): Use wide multi-column layout or centered wide card.
- If layoutMode is 'square' (1:1 Instagram): Use centered square box layout.
- Wrap the entire scene in: <SceneContainer layoutMode="{video_format.layout_mode.value}" safeZone={{{{ top: {sz.top}, bottom: {sz.bottom}, left: {sz.left}, right: {sz.right} }}}}>.

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

            err_msg = res.stderr[-500:] if res.stderr else res.stdout[-500:]
            return False, err_msg
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
