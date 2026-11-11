"""
Topic Intelligence & Research Agent
====================================
Intelligent topic analysis, spell/error correction, keyword generation,
and cascading research (yt-dlp -> internet search fallback).

Features:
  1. AI-powered typo & error detection (e.g. "Spark-X2.6-71.7B" -> "Spark-X2.6-1.7B").
  2. Search-augmented topic normalization: uses live web search to identify real-world entities.
  3. Cascading multi-tier search:
     - Tier 1: yt-dlp video & shorts metadata
     - Tier 2: Live internet search (DuckDuckGo, Wikipedia, technical docs) when yt-dlp yields no results
  4. Automatic fact synthesis for video script generation.
"""
from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

from config import (
    LLM_BACKEND,
    OMNIROUTE_BASE_URL,
    OMNIROUTE_AUTH_TOKEN,
    OMNIROUTE_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GEMINI_API_KEY,
)

logger = logging.getLogger(__name__)


@dataclass
class TopicAnalysis:
    """Detailed AI analysis of a user topic with error corrections."""
    original_topic: str
    corrected_topic: str
    has_corrections: bool
    correction_reason: str
    detected_category: str       # e.g. "AI / LLM Model", "Coding Tutorial", etc.
    primary_keywords: list[str]
    youtube_queries: list[str]
    web_queries: list[str]
    key_concepts: list[str]
    context_summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WebSearchResult:
    """Result from internet search."""
    title: str
    snippet: str
    url: str
    source: str = "web"


# ─── Web Researcher (Internet Search Engine) ─────────────────────────────────

class WebResearcher:
    """
    Searches the live internet (DuckDuckGo, Wikipedia, ArXiv)
    for topic research when yt-dlp yields no video results or for grounding topic analysis.
    """

    def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        """Execute a web search across DuckDuckGo and Wikipedia."""
        logger.info("🌐 Searching internet for: '%s'", query)
        results: list[WebSearchResult] = []

        # 1. DuckDuckGo HTML Search
        ddg_results = self._search_duckduckgo(query, max_results=max_results)
        results.extend(ddg_results)

        # 2. Wikipedia Search if low results
        if len(results) < 3:
            wiki_results = self._search_wikipedia(query)
            results.extend(wiki_results)

        logger.info("✅ Found %d internet search results for '%s'", len(results), query)
        return results

    def _search_duckduckgo(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        """Scrape DuckDuckGo HTML search results without API keys."""
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        results = []
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
                urls = re.findall(r'<a class="result__url[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
                titles = re.findall(r'<a class="result__title[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)

                for i in range(min(len(snippets), max_results)):
                    clean_snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()
                    clean_url = re.sub(r"<[^>]+>", "", urls[i]).strip() if i < len(urls) else ""
                    clean_title = re.sub(r"<[^>]+>", "", titles[i]).strip() if i < len(titles) else query
                    full_url = f"https://{clean_url}" if clean_url and not clean_url.startswith("http") else clean_url

                    if clean_snippet:
                        results.append(WebSearchResult(
                            title=clean_title or query,
                            snippet=clean_snippet,
                            url=full_url,
                            source="duckduckgo",
                        ))
        except Exception as exc:
            logger.warning("DuckDuckGo search error: %s", exc)
        return results

    def _search_wikipedia(self, query: str) -> list[WebSearchResult]:
        """Query official Wikipedia OpenSearch API."""
        encoded = urllib.parse.quote(query)
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded}&limit=3&namespace=0&format=json"
        results = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ContentAutomationBot/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if len(data) >= 4:
                    titles = data[1]
                    snippets = data[2]
                    urls = data[3]
                    for t, s, u in zip(titles, snippets, urls):
                        if s:
                            results.append(WebSearchResult(
                                title=t,
                                snippet=s,
                                url=u,
                                source="wikipedia",
                            ))
        except Exception as exc:
            logger.debug("Wikipedia search error: %s", exc)
        return results


# ─── Heuristic Spell & Version Checker (Fallback when LLM is offline) ────────

KNOWN_AI_ENTITIES = {
    "deepseak": "DeepSeek",
    "deepseek": "DeepSeek",
    "cloude": "Claude",
    "sonet": "Sonnet",
    "chatgbt": "ChatGPT",
    "chatgpt": "ChatGPT",
    "llama3": "Llama 3",
    "llama2": "Llama 2",
    "mistrel": "Mistral",
    "pythn": "Python",
    "remotion": "Remotion",
    "voicestudio": "VoiceStudio",
    "whispr": "Whisper",
    "ytdlp": "yt-dlp",
}


def heuristic_topic_correction(raw_topic: str) -> tuple[str, bool, str]:
    """
    Lightweight heuristic corrections for common AI model notation errors:
      - Transposed/garbled parameter sizes (e.g. 71.7B where 1.7B or 70B was meant)
      - Common phonetic misspellings
    """
    corrected = raw_topic.strip()
    reasons = []

    # Check known word typos
    words = corrected.split()
    new_words = []
    for w in words:
        clean_w = re.sub(r"[^\w]", "", w).lower()
        if clean_w in KNOWN_AI_ENTITIES and clean_w != w.lower():
            replacement = KNOWN_AI_ENTITIES[clean_w]
            new_words.append(w.replace(w, replacement))
            reasons.append(f"Fixed typo '{w}' -> '{replacement}'")
        else:
            new_words.append(w)
    corrected = " ".join(new_words)

    # Check for invalid decimal parameter sizes like 71.7B or 700B
    param_match = re.search(r"(\d+(\.\d+)?)B\b", corrected, re.IGNORECASE)
    if param_match:
        val_str = param_match.group(1)
        if "71.7" in val_str or "7.1.7" in val_str:
            corrected = re.sub(r"71\.7B|7\.1\.7B", "1.7B", corrected, flags=re.IGNORECASE)
            reasons.append("Identified transposed parameter '71.7B' / '7.1.7B'; corrected to '1.7B' (1.71B parameter dense decoder)")
        elif "700B" in val_str:
            corrected = re.sub(r"700B", "70B", corrected, flags=re.IGNORECASE)
            reasons.append("Corrected '700B' to standard '70B' parameter scale")

    has_corrections = corrected.lower() != raw_topic.strip().lower()
    reason_str = "; ".join(reasons) if reasons else "No obvious typos detected"
    return corrected, has_corrections, reason_str


# ─── Topic Intelligence Agent ────────────────────────────────────────────────

class TopicIntelligenceAgent:
    """
    Agent that analyzes user topics, identifies typos or model version mistakes,
    and generates search keywords for yt-dlp and the open internet.
    Augmented with live web search probing to identify real-world models and papers.
    """

    PROMPT_TEMPLATE = """You are an expert AI Research Assistant with real-time web search capabilities.
Your task is to analyze a video topic query typed by a user, identify any spelling mistakes, typos, version errors, or parameter size errors, and generate high-precision search keywords.

USER TOPIC: "{topic}"

LIVE WEB SEARCH CONTEXT (Ground Truth):
{search_context}

Key Guidelines:
1. Check the user topic against the live search results. If the user typed a non-existent parameter size or version (e.g. "Spark-X2.6-71.7B" or "Spark-X2.6-7.1.7B" when real releases are "Spark-X2.6-1.7B" and "Spark-X2.6-4B"), identify the canonical model name and explain the typo clearly.
2. Common errors:
   - "Spark-X2.6-71.7B" -> Typo for "Spark-X2.6-1.7B" (1.71B parameter on-device model) or "Spark-X2.6-4B"
   - "Llama3 700B" -> Typo for "Llama 3 70B"
   - "DeepSeak V3 reasoning" -> "DeepSeek V3 reasoning"
   - "Pythn 3.14 asyncronus" -> "Python 3.14 asynchronous"

Respond with ONLY valid JSON with this exact schema:
{{
  "original_topic": "{topic}",
  "corrected_topic": "Accurate, canonical name of the topic or model",
  "has_corrections": true/false,
  "correction_reason": "Clear explanation of what was corrected or confirmed based on search context",
  "detected_category": "e.g. AI Model Architecture, Python Framework, Hardware Benchmark",
  "primary_keywords": ["keyword1", "keyword2", "keyword3"],
  "youtube_queries": [
    "Query 1 optimized for YouTube search",
    "Query 2 for review/benchmark",
    "Query 3 for tutorial/explainer"
  ],
  "web_queries": [
    "Query 1 for web technical documentation",
    "Query 2 for GitHub / HuggingFace release"
  ],
  "key_concepts": ["concept 1", "concept 2", "concept 3"],
  "context_summary": "1-2 sentences explaining what this topic actually is"
}}"""

    def __init__(self, web_researcher: Optional[WebResearcher] = None):
        self.web = web_researcher or WebResearcher()
        self._setup_llm()

    def _setup_llm(self):
        """Set up client connection for topic analysis."""
        self.endpoint = OMNIROUTE_BASE_URL
        self.token = OMNIROUTE_AUTH_TOKEN
        self.model = OMNIROUTE_MODEL

    def analyze(self, topic: str) -> TopicAnalysis:
        """
        Analyze a topic, correct typos, and generate queries.
        Probes the web first for grounding, then uses AI with heuristic fallback.
        """
        logger.info("🧠 Analyzing topic with Topic Intelligence Agent: '%s'", topic)

        # Step 1: Web probe to ground search in real facts
        search_snippets = self._web_probe(topic)

        # Step 2: Try AI-powered analysis with search grounding
        ai_result = self._call_ai(topic, search_snippets)
        if ai_result:
            logger.info("✅ Topic analyzed via AI: '%s' -> '%s' (Corrections: %s)",
                        topic, ai_result.corrected_topic, ai_result.has_corrections)
            if ai_result.has_corrections:
                logger.info("   Reason: %s", ai_result.correction_reason)
            return ai_result

        # Step 3: Heuristic fallback if AI unavailable
        logger.warning("AI model unavailable for topic analysis; using heuristic rule engine.")
        return self._heuristic_analysis(topic)

    def _web_probe(self, topic: str) -> str:
        """Perform a quick web search probe to discover if the entity/model exists."""
        try:
            # Clean topic to find base model/topic
            clean_topic = re.sub(r"[\d\.]+B\b", "", topic, flags=re.IGNORECASE).strip()
            probe_query = f"{topic} model parameters" if clean_topic == topic else f"{clean_topic} models"
            results = self.web.search(probe_query, max_results=4)
            if not results:
                results = self.web.search(topic, max_results=3)

            if results:
                lines = [f"- {r.title}: {r.snippet}" for r in results[:4]]
                return "\n".join(lines)
        except Exception as exc:
            logger.debug("Web probe failed: %s", exc)
        return "No pre-search results available."

    def _call_ai(self, topic: str, search_context: str) -> Optional[TopicAnalysis]:
        """Call AI backend (OpenRouter, Omniroute, OpenAI) to analyze the topic."""
        prompt = self.PROMPT_TEMPLATE.format(topic=topic, search_context=search_context)

        # 1. Try OpenRouter (high accuracy, fast)
        if OPENROUTER_API_KEY:
            try:
                req_data = json.dumps({
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a tech topic normalization expert. Always respond with valid JSON only."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                }).encode("utf-8")

                req = urllib.request.Request(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    data=req_data,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/omniroute/openstudio",
                        "X-Title": "ContentAutomation",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                    choices = data.get("choices", [])
                    if choices:
                        raw_text = choices[0].get("message", {}).get("content", "")
                        res = self._parse_json_response(raw_text, topic)
                        if res:
                            return res
            except Exception as exc:
                logger.debug("OpenRouter topic analysis failed: %s; falling back to Omniroute...", exc)

        # 2. Try Omniroute (1.6B tokens proxy)
        try:
            req_data = json.dumps({
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a tech topic normalization expert. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,  # Low temperature for strict factual accuracy
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self.endpoint}/v1/chat/completions",
                data=req_data,
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                choices = data.get("choices", [])
                if choices:
                    raw_text = choices[0].get("message", {}).get("content", "")
                    return self._parse_json_response(raw_text, topic)
        except Exception as exc:
            logger.debug("Omniroute topic analysis failed: %s", exc)

        # Try OpenAI if configured
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                resp = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                return self._parse_json_response(resp.choices[0].message.content or "", topic)
            except Exception as exc:
                logger.debug("OpenAI topic analysis failed: %s", exc)

        return None

    def _parse_json_response(self, raw_text: str, original_topic: str) -> Optional[TopicAnalysis]:
        """Extract and validate TopicAnalysis JSON from LLM response."""
        clean_text = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("`").strip()
        json_match = re.search(r"\{[\s\S]*\}", clean_text)
        if not json_match:
            return None
        try:
            data = json.loads(json_match.group(0))
            return TopicAnalysis(
                original_topic=original_topic,
                corrected_topic=data.get("corrected_topic", original_topic),
                has_corrections=bool(data.get("has_corrections", False)),
                correction_reason=data.get("correction_reason", ""),
                detected_category=data.get("detected_category", "Technology"),
                primary_keywords=data.get("primary_keywords", [original_topic]),
                youtube_queries=data.get("youtube_queries", [original_topic]),
                web_queries=data.get("web_queries", [original_topic]),
                key_concepts=data.get("key_concepts", []),
                context_summary=data.get("context_summary", ""),
            )
        except Exception as exc:
            logger.warning("Failed to parse topic analysis JSON: %s", exc)
            return None

    def _heuristic_analysis(self, topic: str) -> TopicAnalysis:
        """Rule-based heuristic analysis when LLM is offline."""
        corrected, has_corr, reason = heuristic_topic_correction(topic)

        # Generate standard variations
        yt_queries = [
            corrected,
            f"{corrected} review benchmark",
            f"{corrected} explainer guide",
        ]
        web_queries = [
            f"{corrected} documentation github",
            f"{corrected} architecture specifications",
        ]
        keywords = list(dict.fromkeys(corrected.split() + [corrected]))

        return TopicAnalysis(
            original_topic=topic,
            corrected_topic=corrected,
            has_corrections=has_corr,
            correction_reason=reason,
            detected_category="Technology & Software",
            primary_keywords=keywords[:5],
            youtube_queries=yt_queries,
            web_queries=web_queries,
            key_concepts=keywords[:3],
            context_summary=f"Technical topic regarding {corrected}.",
        )
