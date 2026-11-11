"""
Script Generator — 100% Free, No API Keys
==========================================
Generates video scripts using LOCAL LLMs via Ollama.
No paid API, no account, no rate limits — runs entirely on your machine.

Backends (in priority order):
  1. Ollama   — local LLM (Llama 3.2, Mistral, Phi-3, Gemma 2, etc.)  ← FREE DEFAULT
  2. OpenAI   — cloud API (optional, requires API key)
  3. Gemini   — cloud API (optional, requires API key)
  4. Template — built-in fallback, works offline with zero dependencies

Setup Ollama (one-time, free):
  1. Download from https://ollama.com (Windows installer)
  2. Run:  ollama pull llama3.2
  3. That's it — the pipeline will auto-detect and use it.

Smaller/faster models for older hardware:
  ollama pull phi3           # Microsoft Phi-3 mini (~2GB)
  ollama pull gemma2:2b      # Google Gemma 2B (~1.5GB)
  ollama pull mistral:7b-instruct  # Mistral 7B
  ollama pull llama3.2:1b    # Llama 3.2 1B (very fast, 1GB)
"""
from __future__ import annotations

import json
import logging
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import (
    LLM_BACKEND,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    OMNIROUTE_BASE_URL,
    OMNIROUTE_AUTH_TOKEN,
    OMNIROUTE_MODEL,
    IMAGE_GENERATION_URL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GEMINI_API_KEY,
    LOGS_DIR,
)
from researcher import VideoIdea

logger = logging.getLogger(__name__)


# ─── VideoScript dataclass ────────────────────────────────────────────────────

@dataclass
class VideoScript:
    """A fully generated video script ready for TTS synthesis."""
    title: str
    platform: str               # youtube | shorts | tiktok
    hook: str                   # 1-2 sentence attention grabber
    sections: list[dict]        # [{"heading": str, "text": str, "duration_hint": int}]
    cta: str                    # Call to action
    tags: list[str] = field(default_factory=list)
    seo_description: str = ""
    full_text: str = ""         # Complete narration text
    duration_estimate: int = 0  # Estimated seconds

    def to_narration(self) -> str:
        """Return the full text to be synthesized by TTS."""
        if self.full_text:
            return self.full_text
        parts = [self.hook]
        for section in self.sections:
            parts.append(section.get("text", ""))
        parts.append(self.cta)
        return "\n\n".join(p for p in parts if p)

    def to_segments(self) -> list[str]:
        """Return text broken into segments for per-segment TTS synthesis."""
        segments = []
        if self.hook:
            segments.append(self.hook)
        for section in self.sections:
            text = section.get("text", "")
            if text:
                words = text.split()
                chunk_size = 200
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i + chunk_size])
                    if chunk.strip():
                        segments.append(chunk)
        if self.cta:
            segments.append(self.cta)
        return segments

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "platform": self.platform,
            "hook": self.hook,
            "sections": self.sections,
            "cta": self.cta,
            "tags": self.tags,
            "seo_description": self.seo_description,
            "duration_estimate": self.duration_estimate,
            "full_narration": self.to_narration(),
        }


# ─── Prompts ──────────────────────────────────────────────────────────────────

SCRIPT_PROMPTS = {
    "youtube": """You are an expert technical explainer scriptwriter and AI researcher. Write a 100% authentic, factually precise video script with ZERO misconceptions.

TOPIC: {topic}
RESEARCH INSIGHTS & GROUND TRUTH: {insights}

STRICT TECHNICAL ACCURACY REQUIREMENTS:
- NO misconceptions, NO generic AI hype, NO fabricated numbers.
- If explaining AI Model Weights & Compute Requirements:
  * Clarify that model weights (parameters) are learned numerical matrices that store the neural network's knowledge.
  * Exact Memory Formula: Model VRAM (GB) = Parameters (Billions) × Precision Bytes (FP16/BF16 = 2 bytes; INT8 = 1 byte; INT4 = 0.5 bytes). Always mention adding 20-25% extra memory for KV-cache and CUDA overhead.
  * Clearly distinguish Compute (FLOPs) vs Memory Bandwidth (GB/s): Generating tokens (autoregressive decode) is memory-bandwidth bound (reading all weights from VRAM for every single token); prompt processing (prefill) is compute bound.
  * Explain why quantization (e.g. 4-bit / 8-bit) allows running larger models on consumer GPUs without losing core intelligence.
- Start with a clear, authentic hook that immediately frames the core engineering principle.
- Break content into 4 to 6 clear visual sections with smooth transitions.
- Target length: 60 to 90 seconds (180-260 words total).
- Spoken explainer voiceover delivery for KittenTTS.

Respond with ONLY valid JSON (no markdown, no backticks):
{{"title":"Accurate, engaging explainer title","hook":"First 2-3 clear sentences setting the technical reality","sections":[{{"heading":"Section Heading","text":"2-3 spoken sentences explaining the concept with exact clarity","duration_hint":15}}],"cta":"Call-to-action text","tags":["tag1","tag2"],"seo_description":"Accurate YouTube description"}}""",

    "shorts": """You are a technical Shorts creator. Create an authentic 45-60 second explainer with ZERO misconceptions.

TOPIC: {topic}
RESEARCH INSIGHTS & GROUND TRUTH: {insights}

STRICT REQUIREMENTS:
- Immediate technical hook debunking common confusion in the first 3 seconds.
- Deliver exact mathematical or architectural truth clearly (under 140 words).
- No fluff, no false claims. Perfect for fast KittenTTS narration.

Respond with ONLY valid JSON (no markdown, no backticks):
{{"title":"Shorts title under 60 chars","hook":"First punchy sentence","sections":[{{"heading":"The Real Formula","text":"80-100 word precise explanation","duration_hint":45}}],"cta":"Quick CTA","tags":["shorts","tech"],"seo_description":"Accurate description"}}""",

    "tiktok": """You are a viral TikTok scriptwriter. Create a 30-60 second addictive script.

TOPIC: {topic}
RESEARCH INSIGHTS: {insights}

Requirements:
- Trending TikTok style: fast, surprising, emotional
- Start mid-thought or with a controversial statement
- Maximum 120 words
- Must feel authentic

Respond with ONLY valid JSON (no markdown, no backticks):
{{"title":"TikTok caption","hook":"Shocking opener","sections":[{{"heading":"Core","text":"80-100 word narration","duration_hint":40}}],"cta":"Viral CTA","tags":["fyp","viral"],"seo_description":"Caption with hashtags"}}""",
}


# ─── OpenRouter Client (High Accuracy, Cost-Effective Models) ────────────────

class OpenRouterClient:
    """
    Client for OpenRouter API gateway.
    Provides access to cutting-edge models (Llama 3.3 70B, Claude Haiku, Gemini)
    with strict accuracy guardrails and cost efficiency.
    """

    def __init__(
        self,
        base_url: str = OPENROUTER_BASE_URL,
        api_key: str = OPENROUTER_API_KEY,
        model: str = OPENROUTER_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def is_available(self) -> bool:
        """Check if OpenRouter API key is configured."""
        return bool(self.api_key and self.api_key.startswith("sk-or-"))

    def generate(self, prompt: str) -> str:
        """Generate text using OpenRouter chat completions."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/openstudio/content-automation",
            "X-Title": "ContentAutomation",
            "Content-Type": "application/json",
        }
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical explainer scriptwriter and AI researcher. "
                        "CRITICAL: Maintain 100% technical accuracy, authentic facts, and zero misconceptions. "
                        "Always respond with ONLY valid JSON — no markdown code fences, no extra commentary."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
        except Exception as exc:
            raise ConnectionError(f"OpenRouter call failed: {exc}") from exc
        return ""


# ─── Omniroute Client (1.6 Billion Tokens Endpoint) ───────────────────────────

class OmnirouteClient:
    """
    Client for Omniroute proxy running at http://localhost:20128.
    Provides access to 1.6 billion tokens using Anthropic or OpenAI API protocol.
    """

    def __init__(
        self,
        base_url: str = OMNIROUTE_BASE_URL,
        auth_token: str = OMNIROUTE_AUTH_TOKEN,
        model: str = OMNIROUTE_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.model = model

    def is_running(self) -> bool:
        """Check if Omniroute proxy is responsive."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.auth_token}"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as e:
            return e.code in (401, 404, 405)
        except Exception:
            return False

    def generate(self, prompt: str) -> str:
        """Generate text using Omniroute (tries OpenAI format first, then Anthropic)."""
        # Try OpenAI /v1/chat/completions format (standard Omniroute proxy endpoint)
        try:
            return self._generate_openai_format(prompt)
        except Exception as exc:
            logger.warning("Omniroute chat/completions failed (%s); trying Anthropic format...", exc)

        # Fallback to Anthropic /v1/messages format
        headers = {
            "x-api-key": self.auth_token,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = json.dumps({
            "model": self.model,
            "max_tokens": 4096,
            "system": (
                "You are an elite video content scriptwriter. "
                "Always respond with ONLY valid JSON — no markdown backticks, no code fences, no extra text."
            ),
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/v1/messages",
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            content = data.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")

        return ""

    def _generate_openai_format(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an elite video content scriptwriter. "
                        "Always respond with ONLY valid JSON — no markdown backticks, no code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
        except Exception as exc:
            raise ConnectionError(f"Omniroute call failed: {exc}") from exc
        return ""


# ─── Ollama Client (pure stdlib, no dependencies) ─────────────────────────────

class OllamaClient:
    """
    Minimal Ollama API client using only Python stdlib.
    No extra packages needed — just Ollama installed locally.
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_running(self) -> bool:
        """Check if Ollama is running."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """Return names of all locally pulled models."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as resp:
                data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def best_available_model(self) -> Optional[str]:
        """Return the best available model for script writing."""
        models = self.list_models()
        if not models:
            return None
        # Preference order for script writing quality
        preference = [
            "llama3.2", "llama3.1", "llama3", "llama3:8b", "llama3:70b",
            "mistral", "mistral:7b-instruct",
            "gemma2", "gemma2:9b", "gemma:7b",
            "phi3", "phi3:mini",
            "llama3.2:1b", "gemma2:2b",
        ]
        for pref in preference:
            for m in models:
                if m.startswith(pref.split(":")[0]):
                    return m
        return models[0]  # Use whatever is available

    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """Call Ollama /api/generate and return the response text."""
        use_model = model or self.model
        payload = json.dumps({
            "model": use_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,
                "top_p": 0.9,
                "num_predict": 2000,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
            return data.get("response", "")
        except urllib.error.URLError as exc:
            raise ConnectionError(f"Ollama request failed: {exc}") from exc

    def chat(self, messages: list[dict], model: Optional[str] = None) -> str:
        """Call Ollama /api/chat (OpenAI-compatible messages format)."""
        use_model = model or self.model
        payload = json.dumps({
            "model": use_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.8, "top_p": 0.9, "num_predict": 2000},
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
            return data.get("message", {}).get("content", "")
        except urllib.error.URLError as exc:
            raise ConnectionError(f"Ollama chat request failed: {exc}") from exc


# ─── Script Generator ─────────────────────────────────────────────────────────

class ScriptGenerator:
    """
    Generate video scripts using local LLMs or proxy backends:
      1. Omniroute (1.6 Billion tokens at http://localhost:20128)
      2. Ollama (local open-source models)
      3. OpenAI / Gemini (with automatic failover to Omniroute on quota limit)
      4. Template fallback
    """

    def __init__(self):
        self._omniroute: Optional[OmnirouteClient] = OmnirouteClient()
        self._openrouter: Optional[OpenRouterClient] = OpenRouterClient()
        self._ollama: Optional[OllamaClient] = None
        self._openai_client = None
        self._gemini_client = None
        self._active_backend = None
        self._setup()

    def _setup(self):
        """Detect and configure the best available backend."""
        # 1. Try OpenRouter if configured
        if self._openrouter.is_available():
            self._active_backend = "openrouter"
            logger.info("✅ Script generator using OpenRouter (model: %s)", self._openrouter.model)
            return

        # 2. Try Omniroute (1.6 Billion tokens available)
        if LLM_BACKEND == "omniroute" or self._omniroute.is_running():
            self._active_backend = "omniroute"
            logger.info("✅ Script generator using Omniroute (model: %s at %s) — 1.6B tokens",
                        self._omniroute.model, self._omniroute.base_url)
            return

        # 2. Try Ollama (local free)
        ollama = OllamaClient()
        if ollama.is_running():
            best = ollama.best_available_model()
            if best:
                ollama.model = best
                self._ollama = ollama
                self._active_backend = "ollama"
                logger.info("✅ Script generator using Ollama (model: %s) — FREE", best)
                return

        # 3. Try OpenAI (optional fallback)
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
                self._active_backend = "openai"
                logger.info("Script generator using OpenAI (%s)", OPENAI_MODEL)
                return
            except ImportError:
                pass

        # 4. Try Gemini (optional fallback)
        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self._gemini_client = genai.GenerativeModel("gemini-1.5-flash")
                self._active_backend = "gemini"
                logger.info("Script generator using Gemini")
                return
            except ImportError:
                pass

        # 5. Template fallback
        self._active_backend = "template"
        logger.info("Using built-in script templates.")

    # ─── Public API ───────────────────────────────────────────────────────────

    def generate(
        self,
        topic: str,
        platform: str = "youtube",
        ideas: Optional[list[VideoIdea]] = None,
        context_summary: str = "",
        target_duration_s: Optional[int] = None,
    ) -> VideoScript:
        """Generate a complete video script."""
        insights = self._build_insights(ideas or [])
        if context_summary:
            insights = f"BACKGROUND CONTEXT & GROUND TRUTH:\n{context_summary}\n\nKEY RESEARCH SOURCES:\n{insights}"

        prompt_tmpl = SCRIPT_PROMPTS.get(platform, SCRIPT_PROMPTS["youtube"])
        prompt = prompt_tmpl.format(topic=topic, insights=insights)

        if target_duration_s and target_duration_s > 0:
            try:
                from platform_profiles import calculate_target_words
                min_w, max_w = calculate_target_words(target_duration_s)
                duration_instruction = (
                    f"\n\nSTRICT TARGET DURATION REQUIREMENT:\n"
                    f"- This video has a target duration of approximately {target_duration_s} seconds.\n"
                    f"- Total narration word count across hook, sections, and cta MUST be between {min_w} and {max_w} words.\n"
                    f"- Calibrate section duration_hint values so their sum equals approximately {target_duration_s} seconds.\n"
                )
                prompt += duration_instruction
            except Exception as e:
                logger.warning("Could not append duration constraint: %s", e)

        logger.info("✍️  Generating %s script: %s (backend: %s, target duration: %ss)",
                    platform.upper(), topic[:60], self._active_backend, target_duration_s or "default")

        raw = self._call_llm(prompt)
        return self._parse(raw, topic, platform, target_duration_s=target_duration_s)

    def generate_from_idea(self, idea: VideoIdea, platform: str = "youtube") -> VideoScript:
        """Generate a script inspired by a trending video idea."""
        return self.generate(idea.suggested_title or idea.title, platform=platform, ideas=[idea])

    @property
    def backend(self) -> str:
        return self._active_backend or "template"

    # ─── LLM Dispatch ────────────────────────────────────────────────────────

    def _call_llm(self, prompt: str) -> str:
        """Route to the active backend with automatic quota failover to Omniroute."""
        if self._active_backend == "openrouter" and self._openrouter:
            try:
                return self._openrouter.generate(prompt)
            except Exception as exc:
                logger.warning("OpenRouter failed: %s. Failing over to Omniroute...", exc)
                return self._call_omniroute(prompt)

        if self._active_backend == "omniroute":
            return self._call_omniroute(prompt)

        try:
            if self._active_backend == "ollama" and self._ollama:
                return self._call_ollama(prompt)
            elif self._active_backend == "openai" and self._openai_client:
                return self._call_openai(prompt)
            elif self._active_backend == "gemini" and self._gemini_client:
                return self._call_gemini(prompt)
        except Exception as exc:
            # If quota is reached or call fails, auto-fallback to Omniroute
            err_msg = str(exc).lower()
            if any(k in err_msg for k in ["quota", "rate limit", "429", "insufficient", "exceeded"]):
                logger.warning("Quota reached on %s (%s). Failing over to Omniroute (1.6B tokens)...",
                               self._active_backend, exc)
                return self._call_omniroute(prompt)
            raise

        return self._template_response(prompt)

    def _call_omniroute(self, prompt: str) -> str:
        """Call Omniroute endpoint."""
        try:
            return self._omniroute.generate(prompt)
        except Exception as exc:
            logger.error("Omniroute call failed: %s. Falling back to template.", exc)
            return self._template_response(prompt)

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama LLM."""
        try:
            return self._ollama.chat([
                {
                    "role": "system",
                    "content": (
                        "You are a professional video content scriptwriter. "
                        "Always respond with valid JSON only — no markdown code fences, "
                        "no explanations before or after the JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ])
        except ConnectionError as exc:
            logger.error("Ollama call failed: %s. Falling over to Omniroute...", exc)
            return self._call_omniroute(prompt)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        try:
            resp = self._openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("OpenAI error (%s). Falling over to Omniroute...", exc)
            return self._call_omniroute(prompt)

    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API."""
        try:
            resp = self._gemini_client.generate_content(prompt)
            return resp.text or ""
        except Exception as exc:
            logger.warning("Gemini error (%s). Falling over to Omniroute...", exc)
            return self._call_omniroute(prompt)

    # ─── Parsing ─────────────────────────────────────────────────────────────

    def _parse(
        self,
        raw: str,
        topic: str,
        platform: str,
        target_duration_s: Optional[int] = None,
    ) -> VideoScript:
        """Parse LLM JSON response into a VideoScript."""
        # Strip markdown fences if the LLM added them anyway
        raw = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

        # Find the first valid JSON object
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            try:
                data = json.loads(json_match.group())
                sections = data.get("sections", [])
                calc_duration = sum(s.get("duration_hint", 60) for s in sections)
                if target_duration_s and target_duration_s > 0:
                    final_duration = target_duration_s
                else:
                    final_duration = calc_duration

                return VideoScript(
                    title=data.get("title", topic),
                    platform=platform,
                    hook=data.get("hook", ""),
                    sections=sections,
                    cta=data.get("cta", "Like and subscribe for more!"),
                    tags=data.get("tags", []),
                    seo_description=data.get("seo_description", ""),
                    duration_estimate=final_duration,
                )
            except json.JSONDecodeError:
                pass

        # Fallback: use the whole response as narration text
        logger.warning("Could not parse JSON response. Using raw text as script body.")
        fallback_duration = target_duration_s if (target_duration_s and target_duration_s > 0) else 300
        return VideoScript(
            title=topic,
            platform=platform,
            hook=f"Today we're exploring: {topic}.",
            sections=[{"heading": "Main Content", "text": raw or topic, "duration_hint": fallback_duration}],
            cta="Like, subscribe, and leave a comment!",
            full_text=raw or f"Let's talk about {topic}.",
            duration_estimate=fallback_duration,
        )

    # ─── Insights Builder ─────────────────────────────────────────────────────

    def _build_insights(self, ideas: list[VideoIdea]) -> str:
        if not ideas:
            return "No research data. Use your general knowledge and best practices."
        lines = []
        for i, idea in enumerate(ideas[:6], 1):
            if getattr(idea, "source_type", "") == "web" or idea.platform == "web_research":
                lines.append(
                    f"{i}. [🌐 Web Source: {idea.uploader}] {idea.title}\n"
                    f"   Fact: {idea.description[:250]}"
                )
            else:
                views = f"{idea.view_count:,}" if idea.view_count else "unknown"
                lines.append(
                    f"{i}. [📹 Video Idea] '{idea.title}' | {views} views"
                    + (f" | Hook: {idea.hook[:100]}" if idea.hook else "")
                )
        return "\n".join(lines)

    # ─── Template Fallback ────────────────────────────────────────────────────

    def _template_response(self, prompt: str) -> str:
        """Return a smart template script when no LLM is available."""
        m = re.search(r"TOPIC:\s*(.+?)(?:\n|$)", prompt)
        topic = m.group(1).strip() if m else "this topic"

        return json.dumps({
            "title": f"The Complete Guide to {topic} (2026)",
            "hook": (
                f"What if I told you that {topic} could completely change how you work? "
                f"In the next few minutes, I'm going to show you exactly why this matters "
                f"and how to get started today."
            ),
            "sections": [
                {
                    "heading": "Why This Matters",
                    "text": (
                        f"Let's start with the big picture. {topic} is one of the most talked-about "
                        f"subjects right now, and for good reason. The people who understand it "
                        f"early are already gaining a massive advantage. So let's break it down "
                        f"in a way that actually makes sense."
                    ),
                    "duration_hint": 90,
                },
                {
                    "heading": "The Core Concepts",
                    "text": (
                        f"Here's what you absolutely need to know about {topic}. "
                        f"First, don't overcomplicate it. At its core, it's about saving time "
                        f"and doing more with less effort. Second, the barrier to entry is lower "
                        f"than you think — anyone can start today. Third, the results compound "
                        f"over time, so starting early makes a huge difference."
                    ),
                    "duration_hint": 120,
                },
                {
                    "heading": "How to Get Started",
                    "text": (
                        f"Now let's talk about action steps. When it comes to {topic}, the biggest "
                        f"mistake people make is waiting until they feel 'ready'. Spoiler: that day "
                        f"never comes. Here's what you should do instead — start small, be "
                        f"consistent, and iterate based on results. The first step is simply "
                        f"deciding to begin."
                    ),
                    "duration_hint": 120,
                },
                {
                    "heading": "Common Mistakes to Avoid",
                    "text": (
                        f"Before we wrap up, let me save you some time by covering the mistakes "
                        f"I see people make with {topic} all the time. Number one: trying to do "
                        f"everything at once. Focus on one thing. Number two: not measuring "
                        f"results. What gets measured gets improved. Number three: giving up "
                        f"too early. Give it at least 30 days before judging results."
                    ),
                    "duration_hint": 90,
                },
            ],
            "cta": (
                "If this gave you value, smash that like button — it really helps the channel grow. "
                "Subscribe so you don't miss the next video, and drop your biggest question "
                "about this topic in the comments below. I personally read every single one."
            ),
            "tags": [
                topic.split()[0].lower() if topic.split() else "tips",
                "howto", "tutorial", "2026", "productivity",
            ],
            "seo_description": (
                f"In this video, we explore {topic} and break it down step by step. "
                f"Whether you're a complete beginner or looking to level up, "
                f"this guide covers everything you need to know.\n\n"
                f"Subscribe for more practical tips every week!"
            ),
        })

    # ─── Save ─────────────────────────────────────────────────────────────────

    def save_script(self, script: VideoScript, output_path: Optional[Path] = None) -> Path:
        """Save the generated script as JSON."""
        safe_title = re.sub(r"[^\w\s-]", "", script.title)[:40].strip()
        output_path = output_path or (
            LOGS_DIR / f"script_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info("Script saved → %s", output_path)
        return output_path
