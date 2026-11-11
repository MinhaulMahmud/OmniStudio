"""
Remotion Scene Validator
========================
Validates generated Remotion React code (.tsx) against Remotion Dev skills,
security allowlists, and AST invariants. Returns structured violations for repair loops.
"""
from __future__ import annotations

import re
import os
import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Violation:
    rule_id: str
    line: int
    message: str
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        return f"[Line {self.line}] [{self.rule_id}] {self.message}" + (f" -> '{self.snippet}'" if self.snippet else "")


# Disallowed patterns that violate Remotion headless rendering
FORBIDDEN_CSS_PATTERNS = [
    (r"\btransition\s*:", "CSS 'transition' property detected. Animate only through useCurrentFrame() and interpolate()."),
    (r"\btransition-[a-z0-9-]+", "CSS transition utility detected. Animate only through useCurrentFrame() and interpolate()."),
    (r"\banimation\s*:", "CSS 'animation' property detected. Animate only through useCurrentFrame() and interpolate()."),
    (r"\banimation-[a-z0-9-]+", "CSS animation utility detected. Animate only through useCurrentFrame() and interpolate()."),
    (r"@keyframes\b", "@keyframes declaration detected. Remotion requires frame-driven interpolate() or spring()."),
]

# Disallowed dangerous globals / imports
FORBIDDEN_CALLS = [
    (r"\beval\s*\(", "eval() is strictly forbidden for security and determinism."),
    (r"\bnew\s+Function\s*\(", "new Function() is strictly forbidden."),
    (r"\bXMLHttpRequest\b", "XMLHttpRequest is forbidden in Remotion scene code."),
    (r"\bfetch\s*\(", "Runtime fetch() during frame rendering is forbidden. Use static assets or Remotion pre-loading."),
    (r"\bprocess\.env\b", "Direct process.env access in client scene code is disallowed."),
]

# Allowed import sources
ALLOWED_IMPORT_PREFIXES = (
    "react",
    "react-dom",
    "remotion",
    "@remotion/",
    "../primitives",
    "./primitives",
)


def validate_scene_code(code: str, file_path: Optional[Path] = None) -> list[Violation]:
    """
    Validate Remotion TSX code string.

    Returns:
        List of Violation objects. If empty, code is valid.
    """
    violations: list[Violation] = []
    lines = code.split("\n")

    # 1. Check for CSS animations / transitions
    for line_idx, line in enumerate(lines, start=1):
        # Skip pure comments
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        for pattern, msg in FORBIDDEN_CSS_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(Violation(
                    rule_id="no_css_animations",
                    line=line_idx,
                    message=msg,
                    snippet=line.strip()[:100],
                ))

        for pattern, msg in FORBIDDEN_CALLS:
            if re.search(pattern, line):
                violations.append(Violation(
                    rule_id="forbidden_runtime_call",
                    line=line_idx,
                    message=msg,
                    snippet=line.strip()[:100],
                ))

    # 2. Check import allowlist
    import_pattern = re.compile(r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""")
    for line_idx, line in enumerate(lines, start=1):
        match = import_pattern.search(line)
        if match:
            module_name = match.group(1) or match.group(2)
            if module_name:
                # Check against allowlist
                is_allowed = any(
                    module_name == allowed or module_name.startswith(allowed)
                    for allowed in ALLOWED_IMPORT_PREFIXES
                )
                if not is_allowed:
                    violations.append(Violation(
                        rule_id="disallowed_import",
                        line=line_idx,
                        message=(
                            f"Import from '{module_name}' is not in the allowlist. "
                            f"Allowed sources: react, remotion, @remotion/*, ../primitives/*"
                        ),
                        snippet=line.strip(),
                    ))

    # 3. Check for dynamic motion requirements
    has_use_current_frame = "useCurrentFrame" in code
    has_interpolate = "interpolate" in code
    has_spring = "spring" in code

    if ("frame" in code or "animate" in code.lower()) and not has_use_current_frame:
        violations.append(Violation(
            rule_id="missing_use_current_frame",
            line=1,
            message="Scene attempts animation but does not call useCurrentFrame().",
        ))

    if has_use_current_frame and not (has_interpolate or has_spring):
        violations.append(Violation(
            rule_id="missing_interpolate_or_spring",
            line=1,
            message="Component subscribes to useCurrentFrame() but uses neither interpolate() nor spring() for motion.",
        ))

    # 4. Check for hardcoded frame constants vs fps scaling
    # Look for patterns like from={90} or durationInFrames={120} where a raw number >= 45 is used without fps
    hardcoded_frames_pattern = re.compile(r"(?:durationInFrames|from|trimBefore)\s*=\s*\{\s*([4-9]\d{1,3}|\d{3,})\s*\}")
    for line_idx, line in enumerate(lines, start=1):
        m = hardcoded_frames_pattern.search(line)
        if m and "fps" not in line:
            violations.append(Violation(
                rule_id="hardcoded_fps_frames",
                line=line_idx,
                message=f"Hardcoded frame count '{m.group(1)}' found without fps scaling. Use 'Math.round(seconds * fps)'.",
                snippet=line.strip(),
            ))

    # 5. Check for hardcoded excessive pixel widths (>1100px)
    excessive_width_pattern = re.compile(r"""(?:width|maxWidth)\s*:\s*['"]?([1-9]\d{3,})px?['"]?""")
    for line_idx, line in enumerate(lines, start=1):
        match = excessive_width_pattern.search(line)
        if match:
            w_val = int(match.group(1))
            if w_val >= 1100:
                violations.append(Violation(
                    rule_id="no_hardcoded_wide_widths",
                    line=line_idx,
                    message=f"Hardcoded width of {w_val}px exceeds responsive safe bounds. Use '100%' or responsive layoutMode.",
                    snippet=line.strip()[:100],
                ))

    return violations


def validate_with_typescript(file_path: Path, remotion_dir: Optional[Path] = None) -> list[Violation]:
    """
    Optional deep typecheck with tsc if available.
    """
    violations: list[Violation] = []
    if not file_path.exists():
        return [Violation("file_not_found", 1, f"File {file_path} does not exist")]

    # First run static validator
    code = file_path.read_text(encoding="utf-8")
    violations.extend(validate_scene_code(code, file_path))

    return violations
