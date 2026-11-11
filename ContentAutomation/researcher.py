"""
Content Researcher
==================
Uses yt-dlp to fetch trending video metadata from YouTube and other platforms,
then extracts ideas, titles, scripts, and hooks for content creation.

Integrated with:
  1. TopicIntelligenceAgent: AI typo/error detection and keyword generation.
  2. WebResearcher: Automatic cascading internet search fallback when yt-dlp has 0 results.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import (
    YT_DLP_MAX_RESULTS,
    YT_DLP_DATE_FILTER,
    DEFAULT_TOPICS,
    LOGS_DIR,
)
from topic_intelligence import (
    TopicIntelligenceAgent,
    TopicAnalysis,
    WebResearcher,
    WebSearchResult,
)

logger = logging.getLogger(__name__)


@dataclass
class VideoIdea:
    """Structured research idea extracted from video metadata or web research."""
    platform: str
    title: str
    url: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    duration: int = 0            # seconds
    description: str = ""
    tags: list[str] = field(default_factory=list)
    uploader: str = ""
    upload_date: str = ""
    thumbnail: str = ""
    # Computed / Intelligence fields
    hook: str = ""               # First compelling sentence or key fact
    suggested_title: str = ""   # AI-suggested title for our content
    engagement_rate: float = 0.0
    source_type: str = "video"  # "video" or "web"

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "title": self.title,
            "url": self.url,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "duration": self.duration,
            "hook": self.hook,
            "description": self.description[:300],
            "suggested_title": self.suggested_title,
            "tags": self.tags,
            "uploader": self.uploader,
            "upload_date": self.upload_date,
            "engagement_rate": self.engagement_rate,
            "source_type": self.source_type,
        }


class ContentResearcher:
    """
    Discovers trending content ideas using yt-dlp and cascading web search.
    Analyzes topics for typos, fetches video metadata without downloading,
    and falls back to live internet search if video results are unavailable.
    """

    SEARCH_URLS = {
        "youtube": "ytsearch{n}:{query}",
        "youtube_trending": "https://www.youtube.com/feed/trending",
        "tiktok": "https://www.tiktok.com/tag/{query}",
    }

    def __init__(self):
        self._check_ytdlp()
        self.web_researcher = WebResearcher()
        self.topic_agent = TopicIntelligenceAgent(web_researcher=self.web_researcher)

    def _check_ytdlp(self):
        """Verify yt-dlp is available."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "yt_dlp", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                logger.info("yt-dlp version: %s", result.stdout.strip())
            else:
                logger.warning("yt-dlp check failed: %s", result.stderr)
        except FileNotFoundError:
            logger.error("yt-dlp not found. Install with: pip install yt-dlp")

    def _run_ytdlp(self, args: list[str]) -> Optional[dict]:
        """
        Run yt-dlp with --dump-json (metadata only, no download).
        Returns parsed JSON or None on error.
        """
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json",          # Print metadata as JSON
            "--no-download",        # Never download the actual video
            "--no-warnings",
            "--quiet",
            "--skip-download",
            "--flat-playlist",      # Don't recurse into playlists deeply
        ] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0 and not result.stdout:
                logger.debug("yt-dlp error: %s", result.stderr[:500])
                return None
            lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
            parsed = []
            for line in lines:
                try:
                    parsed.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return {"entries": parsed} if parsed else None
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp timed out for: %s", args[-1] if args else "unknown")
            return None
        except Exception as exc:
            logger.error("yt-dlp failed: %s", exc)
            return None

    def search_youtube(
        self,
        query: str,
        max_results: int = YT_DLP_MAX_RESULTS,
    ) -> list[VideoIdea]:
        """Search YouTube for trending videos on a topic."""
        logger.info("🔍 Searching YouTube: '%s' (top %d)", query, max_results)
        url = f"ytsearch{max_results}:{query}"
        data = self._run_ytdlp([url])
        if not data:
            return []
        entries = data.get("entries", [data]) if isinstance(data, dict) else []
        return [self._parse_entry(e, "youtube") for e in entries if e]

    def search_youtube_shorts(
        self,
        query: str,
        max_results: int = YT_DLP_MAX_RESULTS,
    ) -> list[VideoIdea]:
        """Search YouTube Shorts."""
        logger.info("🔍 Searching YouTube Shorts: '%s'", query)
        url = f"ytsearch{max_results}:{query} #shorts"
        data = self._run_ytdlp([url])
        if not data:
            return []
        entries = data.get("entries", [data]) if isinstance(data, dict) else []
        ideas = []
        for e in entries:
            if e:
                idea = self._parse_entry(e, "youtube_shorts")
                if idea.duration <= 90 or "shorts" in (idea.url or "").lower():
                    ideas.append(idea)
        return ideas

    def research_topic(
        self,
        raw_topic: str,
        max_results: int = YT_DLP_MAX_RESULTS,
    ) -> tuple[list[VideoIdea], TopicAnalysis]:
        """
        Intelligent multi-tier topic research:
          1. Topic Intelligence Agent analyzes input topic, fixes typos/notation errors,
             and generates optimized search keywords.
          2. Runs yt-dlp search on YouTube (long-form and shorts).
          3. Cascades to Internet Web Search (DuckDuckGo + Wikipedia) if yt-dlp yields no results.
        """
        # ─── Stage 1: Topic Intelligence & Typo Correction ──────────────────
        analysis = self.topic_agent.analyze(raw_topic)

        print("\n" + "═" * 70)
        print("  🧠 TOPIC INTELLIGENCE AGENT")
        print("═" * 70)
        print(f"  • Input Topic     : {analysis.original_topic}")
        print(f"  • Canonical Topic : {analysis.corrected_topic}")
        if analysis.has_corrections:
            print(f"  • Typo Detected   : ⚠️ YES - Corrected!")
            print(f"  • Reason          : {analysis.correction_reason}")
        else:
            print(f"  • Typo Check      : ✅ Clean (No spelling errors detected)")
        print(f"  • Category        : {analysis.detected_category}")
        print(f"  • Key Concepts    : {', '.join(analysis.key_concepts[:4])}")
        print(f"  • Primary Keywords: {', '.join(analysis.primary_keywords[:5])}")
        print("═" * 70 + "\n")

        # ─── Stage 2: Search via yt-dlp ──────────────────────────────────────
        ideas: list[VideoIdea] = []
        seen_urls = set()

        # Try search queries generated by AI
        search_queries = [analysis.corrected_topic] + analysis.youtube_queries[:2]
        for query in search_queries:
            logger.info("Searching yt-dlp for query: '%s'", query)
            yt_results = self.search_youtube(query, max_results=max_results)
            for item in yt_results:
                if item.url and item.url not in seen_urls:
                    seen_urls.add(item.url)
                    ideas.append(item)

            if len(ideas) >= max_results:
                break

        # Also probe shorts if needed
        if len(ideas) < max_results:
            shorts_results = self.search_youtube_shorts(analysis.corrected_topic, max_results=max_results // 2)
            for s in shorts_results:
                if s.url and s.url not in seen_urls:
                    seen_urls.add(s.url)
                    ideas.append(s)

        # ─── Stage 3: Cascading Web Fallback (If yt-dlp yields 0 or < 2) ─────
        if len(ideas) < 2:
            print(f"⚠️  yt-dlp found {len(ideas)} videos for '{analysis.corrected_topic}'.")
            print("🌐 Cascading to Live Internet Search (DuckDuckGo + Wikipedia)...\n")

            web_queries = analysis.web_queries if analysis.web_queries else [
                f"{analysis.corrected_topic} architecture specifications",
                f"{analysis.corrected_topic} github documentation",
            ]

            web_results: list[WebSearchResult] = []
            for wq in web_queries[:3]:
                res = self.web_researcher.search(wq, max_results=3)
                web_results.extend(res)

            # Convert web results into VideoIdea structures for downstream consumption
            for w in web_results:
                if w.url and w.url not in seen_urls:
                    seen_urls.add(w.url)
                    idea = VideoIdea(
                        platform="web_research",
                        title=w.title,
                        url=w.url,
                        description=w.snippet,
                        hook=w.snippet[:200],
                        uploader=w.source.upper(),
                        tags=analysis.primary_keywords,
                        source_type="web",
                    )
                    ideas.append(idea)

            print(f"✅ Retrieved {len(web_results)} technical web sources from internet search.")

        # Compute engagement & sort
        for idea in ideas:
            if idea.view_count > 0:
                idea.engagement_rate = (
                    (idea.like_count + idea.comment_count) / idea.view_count * 100
                )

        ideas.sort(
            key=lambda x: (x.view_count * 0.6 + x.like_count * 100 + (100 if x.source_type == "web" else 0)),
            reverse=True,
        )

        return ideas, analysis

    def research_topics(
        self,
        topics: list[str] = None,
        max_per_topic: int = YT_DLP_MAX_RESULTS,
    ) -> list[VideoIdea]:
        """
        Research multiple topics using intelligent analysis, yt-dlp, and web search.
        """
        topics = topics or DEFAULT_TOPICS
        all_ideas: list[VideoIdea] = []

        for topic in topics:
            ideas, _ = self.research_topic(raw_topic=topic, max_results=max_per_topic)
            all_ideas.extend(ideas)

        return all_ideas

    def _parse_entry(self, entry: dict, platform: str) -> VideoIdea:
        """Parse a yt-dlp metadata entry into a VideoIdea."""
        title = entry.get("title", "")
        description = entry.get("description", "") or ""

        hook = ""
        if description:
            sentences = re.split(r"(?<=[.!?])\s+", description.strip())
            for s in sentences:
                if len(s) > 20:
                    hook = s[:200]
                    break

        return VideoIdea(
            platform=platform,
            title=title,
            url=entry.get("webpage_url") or entry.get("url", ""),
            view_count=entry.get("view_count") or 0,
            like_count=entry.get("like_count") or 0,
            comment_count=entry.get("comment_count") or 0,
            duration=entry.get("duration") or 0,
            description=description[:500],
            tags=entry.get("tags") or [],
            uploader=entry.get("uploader") or entry.get("channel", ""),
            upload_date=entry.get("upload_date", ""),
            thumbnail=entry.get("thumbnail", ""),
            hook=hook,
            source_type="video",
        )

    def save_research(self, ideas: list[VideoIdea], output_path: Optional[Path] = None) -> Path:
        """Save research results to a JSON file."""
        output_path = output_path or (
            LOGS_DIR / f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total": len(ideas),
                    "ideas": [i.to_dict() for i in ideas],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        logger.info("Research saved → %s", output_path)
        return output_path

    def print_summary(self, ideas: list[VideoIdea], top: int = 10) -> None:
        """Print a human-readable summary of top ideas (videos and web sources)."""
        print(f"\n{'═'*70}")
        print(f"  📊 TOP {min(top, len(ideas))} RESEARCH DISCOVERIES")
        print(f"{'═'*70}")
        for i, idea in enumerate(ideas[:top], 1):
            if idea.source_type == "web" or idea.platform == "web_research":
                print(f"\n  {i}. [🌐 INTERNET RESEARCH] {idea.title[:65]}")
                print(f"     🔗 Source: {idea.url}")
                if idea.hook:
                    print(f"     📄 Fact: {idea.hook[:120]}...")
            else:
                views = f"{idea.view_count:,}" if idea.view_count else "N/A"
                duration = f"{idea.duration//60}:{idea.duration%60:02d}" if idea.duration else "?"
                print(f"\n  {i}. [📹 {idea.platform.upper()}] {idea.title[:65]}")
                print(f"     👁 {views} views | ⏱ {duration} | 💬 {idea.comment_count:,}")
                if idea.hook:
                    print(f"     💡 Hook: {idea.hook[:100]}")
        print(f"\n{'═'*70}\n")
