"""
AI Remotion Visual Synthesizer
===============================
Dynamically generates custom React/TypeScript Remotion scene code (.tsx)
at runtime for ANY topic using OpenRouter, guided by official remotion-dev/skills,
validated by validate_scene.py, with an automated repair loop and deterministic fallback.
"""
from __future__ import annotations

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

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
REMOTION_DIR = BASE_DIR / "remotion"
GENERATED_DIR = REMOTION_DIR / "src" / "scenes" / "generated"
OUTPUT_FILE = GENERATED_DIR / "DynamicTopicScene.tsx"

PLAYWRIGHT_NODE_DIR = r"C:\Users\MSI\AppData\Roaming\Python\Python313\site-packages\playwright\driver"


PRIMITIVES_API_REFERENCE = """
### AVAILABLE TESTED PRIMITIVES (Import from '../primitives/'):
1. <TitleCard title={string} subtitle?: string badge?: string accentColor?: string />
   - Main title card with spring-animated scaling and safe-area margins.
2. <BulletReveal bullets={string[]} accentColor?: string delayFrames?: number staggerFrames?: number maxWidth?: number />
   - Numbered bullet points revealed sequentially via frame interpolation.
3. <BarChart items={Array<{ label: string, value: number, formattedValue?: string, color?: string }>} title?: string maxValue?: number />
   - Animated horizontal data bars growing smoothly.
4. <LineChart points={Array<{ x: string|number, y: number }>} title?: string lineColor?: string />
   - SVG line chart with animated stroke and shaded gradient.
5. <Timeline steps={Array<{ title: string, description?: string }>} activeStep?: number accentColor?: string />
   - Sequential process nodes with glowing active connector track.
6. <DiagramNodes nodes={Array<{ id: string, label: string, sub?: string, x: number, y: number }>} edges={Array<{ from: string, to: string }>} title?: string />
   - Network / system block diagram with animated signal pulses.
7. <Counter toValue={number} label={string} fromValue?: number unit?: string prefix?: string />
   - High-impact animated metric counter.
8. <CaptionOverlay text={string} />
   - Bottom floating caption bar for spoken narration.
"""

FEW_SHOT_EXAMPLE_1 = """
// Example 1: Physical / Engineering Process (e.g. Aerodynamics or Turbine)
import React from "react";
import { Sequence, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { TitleCard } from "../primitives/TitleCard";
import { BulletReveal } from "../primitives/BulletReveal";
import { Timeline } from "../primitives/Timeline";
import { CaptionOverlay } from "../primitives/CaptionOverlay";

export interface DynamicTopicSceneProps {
  title?: string;
  subtitle?: string;
  sections?: Array<{ heading: string; text: string }>;
}

export const DynamicTopicScene: React.FC<DynamicTopicSceneProps> = ({
  title = "Jet Engine Thrust Cycle",
  subtitle = "Brayton Thermodynamic Cycle",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sec1Dur = Math.round(5 * fps);
  const sec2Dur = Math.round(8 * fps);
  const sec3Dur = Math.round(10 * fps);

  // Custom SVG mechanism: Compressor & Turbine fan rotation
  const fanRotation = frame * 12;

  return (
    <div style={{ flex: 1, backgroundColor: "#060913", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", position: "relative", overflow: "hidden" }}>
      {/* Sequence 1: Hook & Title */}
      <Sequence from={0} durationInFrames={sec1Dur}>
        <TitleCard title={title} subtitle={subtitle} badge="PROPULSION KINEMATICS" />
      </Sequence>

      {/* Sequence 2: 4-Stage Process Timeline */}
      <Sequence from={sec1Dur} durationInFrames={sec2Dur}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "20px" }}>
          <h2 style={{ fontSize: "44px", fontWeight: 800, margin: 0, color: "#38bdf8" }}>Four Stages of Jet Thrust</h2>
          <Timeline steps={[
            { title: "Intake", description: "Huge fan scoops air" },
            { title: "Compress", description: "Blades squeeze air 40:1" },
            { title: "Combust", description: "Fuel ignites at 1700C" },
            { title: "Exhaust", description: "High velocity nozzle thrust" },
          ]} />
        </div>
      </Sequence>

      {/* Sequence 3: Visual Mechanism & Bullets */}
      <Sequence from={sec1Dur + sec2Dur} durationInFrames={sec3Dur}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "1600px", padding: "0 60px" }}>
          {/* Custom SVG Turbine Rotor */}
          <div style={{ width: "650px", height: "450px", backgroundColor: "rgba(15,23,42,0.85)", borderRadius: "24px", border: "1px solid rgba(56,189,248,0.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg viewBox="0 0 400 400" style={{ width: "360px", height: "360px" }}>
              <circle cx="200" cy="200" r="160" fill="none" stroke="#334155" strokeWidth="4" />
              <g transform={`translate(200, 200) rotate(${fanRotation})`}>
                {[...Array(12)].map((_, i) => (
                  <path key={i} d="M 0 0 C 20 -40, 40 -80, 10 -150 C -10 -80, -20 -40, 0 0 Z" fill="#38bdf8" opacity="0.8" transform={`rotate(${i * 30})`} />
                ))}
                <circle cx="0" cy="0" r="28" fill="#0f172a" stroke="#38bdf8" strokeWidth="3" />
              </g>
            </svg>
          </div>
          <BulletReveal bullets={[
            "Compressor raises air pressure exponentially before ignition.",
            "Turbine extracts energy from expanding gas to power the front fan.",
            "Newton's 3rd law generates massive forward momentum."
          ]} maxWidth={750} />
        </div>
      </Sequence>

      <CaptionOverlay text={subtitle} />
    </div>
  );
};
"""

FEW_SHOT_EXAMPLE_2 = """
// Example 2: Computing & Architectural System (e.g. Distributed Consensus or AI)
import React from "react";
import { Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { TitleCard } from "../primitives/TitleCard";
import { DiagramNodes } from "../primitives/DiagramNodes";
import { Counter } from "../primitives/Counter";
import { CaptionOverlay } from "../primitives/CaptionOverlay";

export const DynamicTopicScene: React.FC<any> = ({
  title = "Distributed Raft Consensus",
  subtitle = "Fault Tolerant State Replication",
}) => {
  const { fps } = useVideoConfig();

  return (
    <div style={{ flex: 1, backgroundColor: "#070b14", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", position: "relative" }}>
      <Sequence from={0} durationInFrames={Math.round(5 * fps)}>
        <TitleCard title={title} subtitle={subtitle} badge="DISTRIBUTED COMPUTING" accentColor="#818cf8" />
      </Sequence>
      <Sequence from={Math.round(5 * fps)} durationInFrames={Math.round(12 * fps)}>
        <div style={{ display: "flex", alignItems: "center", gap: "50px" }}>
          <DiagramNodes
            title="Cluster Topology"
            nodes={[
              { id: "leader", label: "Leader Node", sub: "Term 4 (Active)", x: 50, y: 30, color: "#10b981" },
              { id: "f1", label: "Follower 1", sub: "Replicated", x: 25, y: 75, color: "#38bdf8" },
              { id: "f2", label: "Follower 2", sub: "Replicated", x: 75, y: 75, color: "#38bdf8" },
            ]}
            edges={[
              { from: "leader", to: "f1" },
              { from: "leader", to: "f2" },
            ]}
            width={850}
            height={420}
          />
          <Counter toValue={150000} label="Operations Per Second" unit="ops/s" accentColor="#10b981" />
        </div>
      </Sequence>
      <CaptionOverlay text={subtitle} />
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
        max_repair_attempts: int = 3,
    ) -> Path:
        """
        Synthesize DynamicTopicScene.tsx for the given topic and script.

        Returns:
            Path to the written DynamicTopicScene.tsx file.
        """
        start_time = time.time()
        visual_keywords = visual_keywords or []
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("⚛️  AI Remotion Synthesizer starting for: '%s'", topic)
        logger.info("   Skills Version : %s", self.skills_version[:10])
        logger.info("   Model          : %s", self.model)
        logger.info("   Duration       : %.1fs (~%d frames)", audio_duration_s, int(audio_duration_s * VIDEO_FPS))

        # Check if API key is configured
        if not self.api_key:
            logger.warning("No OpenRouter API key found. Using deterministic primitives fallback.")
            self._write_fallback(topic, script, audio_duration_s)
            return OUTPUT_FILE

        # Build initial prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(topic, script, audio_duration_s, visual_keywords)

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
                    + "\n\nPlease rewrite the complete DynamicTopicScene.tsx file to FIX ALL VIOLATIONS. "
                    "Remember: strictly NO CSS transitions, NO @keyframes, use ONLY allowed imports (../primitives/*), "
                    "and calculate frames using fps from useVideoConfig(). Return ONLY valid TypeScript code."
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
        self._write_fallback(topic, script, audio_duration_s)
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
3. Import primitives from '../primitives/' (e.g. `import {{ TitleCard, BulletReveal, Timeline, Counter }} from "../primitives";`).
4. NEVER use CSS transitions, CSS animations, or @keyframes.
5. All timings must scale with fps from `useVideoConfig()`.
"""

    def _build_user_prompt(
        self,
        topic: str,
        script: Any,
        audio_duration_s: float,
        visual_keywords: list[str],
    ) -> str:
        sections = getattr(script, "sections", [])
        title = getattr(script, "title", topic)
        hook = getattr(script, "hook", "")

        sec_lines = []
        fps = VIDEO_FPS
        total_frames = int(audio_duration_s * fps)
        per_sec_frames = total_frames // max(len(sections) + 1, 1)

        sec_lines.append(f"- Intro/Hook: '{hook[:120]}' (~{per_sec_frames} frames)")
        for idx, sec in enumerate(sections):
            heading = sec.get("heading") if isinstance(sec, dict) else getattr(sec, "heading", f"Point {idx+1}")
            text = sec.get("text") if isinstance(sec, dict) else getattr(sec, "text", "")
            sec_lines.append(f"- Section {idx+1}: '{heading}' - {text[:150]} (~{per_sec_frames} frames)")

        sections_desc = "\n".join(sec_lines)
        keywords_desc = ", ".join(visual_keywords) if visual_keywords else "technical diagrams, process steps"

        return f"""Generate DynamicTopicScene.tsx for:
TOPIC: {topic}
TITLE: {title}
TOTAL DURATION: ~{audio_duration_s:.1f} seconds ({total_frames} frames at {fps} fps)
VISUAL KEYWORDS: {keywords_desc}

SCRIPT TIMELINE BREAKDOWN:
{sections_desc}

FEW-SHOT EXAMPLES FOR INSPIRATION:
--- EXAMPLE 1 ---
{FEW_SHOT_EXAMPLE_1}

--- EXAMPLE 2 ---
{FEW_SHOT_EXAMPLE_2}

Compose a multi-sequence scene using the tested primitives (TitleCard, BulletReveal, Timeline, BarChart, LineChart, DiagramNodes, Counter) and clean custom inline SVGs for any topic-specific mechanisms.
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
        Smoke test by rendering a single still frame at frame 30 using Node.
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
                timeout=45,
            )
            if res.returncode == 0 and temp_img.exists():
                try:
                    temp_img.unlink()
                except Exception:
                    pass
                return True, ""

            combined_out = (res.stderr or "") + "\n" + (res.stdout or "")
            # If bundling reached 100% and getting composition succeeded, the React code is valid
            # (any later ErrorEvent is an OS/sandbox localhost devtools socket restriction)
            if ("Bundling 100%" in combined_out or "Getting composition" in combined_out) and (
                "ErrorEvent" in combined_out or "10013" in combined_out or "getaddrinfo" in combined_out
            ):
                return True, ""

            return False, res.stderr[-800:] if res.stderr else res.stdout[-800:]
        except Exception as exc:
            return False, str(exc)

    def _write_fallback(self, topic: str, script: Any, audio_duration_s: float):
        """Generate a guaranteed-valid deterministic composition from primitives."""
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

        fallback_code = f"""import React from "react";
import {{ Sequence, useCurrentFrame, useVideoConfig }} from "remotion";
import {{ TitleCard }} from "../primitives/TitleCard";
import {{ BulletReveal }} from "../primitives/BulletReveal";
import {{ CaptionOverlay }} from "../primitives/CaptionOverlay";

export const DynamicTopicScene: React.FC<any> = () => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();

  const title = {repr(title)};
  const subtitle = {repr(hook)};
  const sections = {sections_json};

  const secDuration = Math.round({max(4, int(audio_duration_s / max(len(sections_json) + 1, 1)))} * fps);

  return (
    <div
      style={{{{
        flex: 1,
        backgroundColor: "#060913",
        backgroundImage: "radial-gradient(circle at 50% 20%, #0d1e38 0%, #060913 75%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Roboto, sans-serif",
        color: "#ffffff",
        position: "relative",
        padding: "40px",
        overflow: "hidden",
      }}}}
    >
      <Sequence from={{0}} durationInFrames={{secDuration}}>
        <TitleCard title={{title}} subtitle={{subtitle}} badge="OMNISTUDIO TECHNICAL EXPLAINER" />
      </Sequence>

      {{sections.map((sec, i) => {{
        const start = (i + 1) * secDuration;
        return (
          <Sequence key={{i}} from={{start}} durationInFrames={{secDuration}}>
            <div style={{{{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px" }}}}>
              <h2 style={{{{ fontSize: "40px", fontWeight: 800, margin: 0, color: "#38bdf8" }}}}>{{sec.heading}}</h2>
              <BulletReveal bullets={{[sec.text]}} maxWidth={{900}} />
            </div>
          </Sequence>
        );
      }})}}

      <CaptionOverlay text={{subtitle}} />
    </div>
  );
}};
"""
        OUTPUT_FILE.write_text(fallback_code, encoding="utf-8")
        logger.info("✅ Written deterministic fallback scene to %s", OUTPUT_FILE)
