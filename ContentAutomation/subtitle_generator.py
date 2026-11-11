"""
Subtitle Generator
===================
Converts narration text into time-coded subtitle files (SRT, WebVTT, ASS)
for video overlays. Supports:
  - Word-level timing estimation from audio duration
  - Multiple subtitle formats
  - Custom styling for reels/shorts
"""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SubtitleChunk:
    """A single subtitle entry with timing."""
    index: int
    start_ms: int
    end_ms: int
    text: str

    @property
    def start_srt(self) -> str:
        return self._ms_to_srt(self.start_ms)

    @property
    def end_srt(self) -> str:
        return self._ms_to_srt(self.end_ms)

    @staticmethod
    def _ms_to_srt(ms: int) -> str:
        hours = ms // 3_600_000
        ms %= 3_600_000
        minutes = ms // 60_000
        ms %= 60_000
        seconds = ms // 1000
        ms %= 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

    def to_srt(self) -> str:
        return f"{self.index}\n{self.start_srt} --> {self.end_srt}\n{self.text}\n"

    def to_vtt(self) -> str:
        start = self.start_srt.replace(",", ".")
        end = self.end_srt.replace(",", ".")
        return f"{start} --> {end}\n{self.text}\n"


class SubtitleGenerator:
    """
    Generates subtitle files from narration text.

    When no audio duration is provided, timing is estimated based on
    average speaking rate (typically 140-160 words per minute).
    """

    WORDS_PER_MINUTE = 150   # Average conversational speaking rate
    WORDS_PER_CHUNK = 4      # Words per subtitle card (social media style)

    def __init__(
        self,
        words_per_chunk: int = WORDS_PER_CHUNK,
        words_per_minute: int = WORDS_PER_MINUTE,
    ):
        self.words_per_chunk = words_per_chunk
        self.words_per_minute = words_per_minute

    def generate(
        self,
        text: str,
        audio_duration_ms: Optional[int] = None,
    ) -> list[SubtitleChunk]:
        """
        Generate subtitle chunks from narration text.

        Args:
            text: The full narration text.
            audio_duration_ms: Actual audio duration (for accurate timing).
                               If None, timing is estimated from word count.

        Returns:
            List of SubtitleChunk objects with timing.
        """
        # Clean and tokenize text into words
        clean_text = re.sub(r"\s+", " ", text).strip()
        words = clean_text.split()
        if not words:
            return []

        # Estimate or use provided duration
        if audio_duration_ms:
            ms_per_word = audio_duration_ms / len(words)
        else:
            ms_per_word = (60 * 1000) / self.words_per_minute  # ~400ms/word at 150wpm

        chunks: list[SubtitleChunk] = []
        current_time = 0.0
        idx = 1

        for i in range(0, len(words), self.words_per_chunk):
            chunk_words = words[i:i + self.words_per_chunk]
            chunk_text = " ".join(chunk_words)
            chunk_ms = len(chunk_words) * ms_per_word

            # Add slight pause between sentences
            if any(w.endswith((".", "!", "?")) for w in chunk_words):
                chunk_ms += 300

            start_ms = int(current_time)
            end_ms = int(current_time + chunk_ms)

            chunks.append(SubtitleChunk(
                index=idx,
                start_ms=start_ms,
                end_ms=end_ms,
                text=chunk_text,
            ))
            current_time = end_ms + 50  # 50ms gap between subtitles
            idx += 1

        return chunks

    def generate_from_segments(
        self,
        segments: list[tuple[str, int]],  # (text, duration_ms) pairs
    ) -> list[SubtitleChunk]:
        """Generate subtitles from multiple text+duration pairs."""
        all_chunks = []
        time_offset = 0
        idx = 1
        for text, duration_ms in segments:
            chunks = self.generate(text, audio_duration_ms=duration_ms)
            for chunk in chunks:
                chunk.start_ms += time_offset
                chunk.end_ms += time_offset
                chunk.index = idx
                all_chunks.append(chunk)
                idx += 1
            time_offset += duration_ms + 100  # 100ms gap between segments
        return all_chunks

    def to_srt(self, chunks: list[SubtitleChunk]) -> str:
        """Generate SRT format subtitle string."""
        return "\n".join(c.to_srt() for c in chunks)

    def to_vtt(self, chunks: list[SubtitleChunk]) -> str:
        """Generate WebVTT format subtitle string."""
        lines = ["WEBVTT\n"]
        lines.extend(c.to_vtt() + "\n" for c in chunks)
        return "\n".join(lines)

    def to_ass(
        self,
        chunks: list[SubtitleChunk],
        style: str = "default",
    ) -> str:
        """
        Generate ASS (Advanced SubStation Alpha) subtitle string.
        ASS subtitles support rich styling for social media videos.
        """
        styles = {
            "default": {
                "fontname": "Arial",
                "fontsize": 60,
                "primary": "&H00FFFFFF",  # White
                "shadow": "&H00000000",   # Black shadow
                "bold": 1,
                "marginv": 50,
            },
            "reels": {
                "fontname": "Arial Black",
                "fontsize": 72,
                "primary": "&H00FFFFFF",
                "shadow": "&H80000000",
                "bold": 1,
                "marginv": 150,
            },
        }
        s = styles.get(style, styles["default"])

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{s['fontname']},{s['fontsize']},{s['primary']},&H00000000,{s['bold']},0,0,0,100,100,0,0,1,2,1,2,10,10,{s['marginv']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for c in chunks:
            start = self._ms_to_ass(c.start_ms)
            end = self._ms_to_ass(c.end_ms)
            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{c.text}")

        return header + "\n".join(events)

    @staticmethod
    def _ms_to_ass(ms: int) -> str:
        hours = ms // 3_600_000
        ms %= 3_600_000
        minutes = ms // 60_000
        ms %= 60_000
        seconds = ms // 1000
        cs = (ms % 1000) // 10  # centiseconds
        return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"

    def save(
        self,
        chunks: list[SubtitleChunk],
        path: Path,
        fmt: str = "srt",
        style: str = "default",
    ) -> Path:
        """Save subtitle file in the requested format."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = {
            "srt": self.to_srt,
            "vtt": self.to_vtt,
        }.get(fmt, self.to_srt)(chunks)
        if fmt == "ass":
            content = self.to_ass(chunks, style=style)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Subtitles saved → %s", path)
        return path
