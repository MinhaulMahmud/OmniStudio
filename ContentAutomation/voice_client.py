"""
Voice Client
=============
Communicates with the local VoiceStudio (OmniVoice) backend to:
  - List available cloned voice profiles
  - Generate speech audio from text using a chosen voice
  - Query voice info and status

VoiceStudio exposes an OpenAI-compatible API at:
  POST /v1/audio/speech  →  TTS (text → audio)
  GET  /v1/audio/voices  →  list all voice profiles
  GET  /v1/models        →  list installed TTS engines
"""
from __future__ import annotations

import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Optional, Union

import requests

try:
    from autonomous_voice_router import AutonomousVoiceRouter, RoutingDecision
    from config import (
        VOICESTUDIO_BASE_URL,
        CLONED_VOICE_ID,
        CLONED_VOICE_NAME,
        TTS_FORMAT,
        TTS_SPEED,
        OUTPUT_DIR,
        FFMPEG_PATH,
    )
except ImportError:
    from ContentAutomation.autonomous_voice_router import AutonomousVoiceRouter, RoutingDecision
    from ContentAutomation.config import (
        VOICESTUDIO_BASE_URL,
        CLONED_VOICE_ID,
        CLONED_VOICE_NAME,
        TTS_FORMAT,
        TTS_SPEED,
        OUTPUT_DIR,
        FFMPEG_PATH,
    )

logger = logging.getLogger(__name__)


class VoiceStudioClient:
    """HTTP client for the local VoiceStudio TTS backend."""

    def __init__(self, base_url: str = VOICESTUDIO_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": "Bearer voicestudio",  # local no-auth token
        })

    # ─── Health ──────────────────────────────────────────────────────────────

    def is_running(self) -> bool:
        """Return True if VoiceStudio backend is accessible."""
        for endpoint in ("/health", "/", "/v1/models"):
            try:
                resp = self.session.get(f"{self.base_url}{endpoint}", timeout=3)
                if resp.status_code in (200, 401, 403):
                    return True
            except Exception:
                continue
        return False

    def wait_until_ready(self, timeout: float = 60.0) -> bool:
        """Block until VoiceStudio is healthy or timeout expires."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_running():
                return True
            time.sleep(2)
        return False

    # ─── Voice Profiles ──────────────────────────────────────────────────────

    def list_voices(self) -> list[dict]:
        """Return all voice profiles from VoiceStudio (cloned + built-in)."""
        try:
            resp = self.session.get(f"{self.base_url}/v1/audio/voices", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                if "voices" in data and isinstance(data["voices"], list):
                    return data["voices"]
                if "data" in data and isinstance(data["data"], list):
                    return data["data"]
                return [v for v in data.values() if isinstance(v, dict)]
            return data if isinstance(data, list) else []
        except Exception as exc:
            logger.error("Failed to list voices: %s", exc)
            return []

    def get_voice_id(
        self,
        voice_id: Optional[str] = None,
        voice_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Resolve a voice to use for TTS.
        Priority: explicit voice_id > explicit voice_name > configured defaults > first available.
        Returns the voice ID string expected by the API.
        """
        # 1. Explicit ID passed in
        if voice_id:
            return voice_id

        # 2. Explicit voice name passed in
        if voice_name:
            voices = self.list_voices()
            for v in voices:
                name = v.get("name", "") or ""
                if name.lower() == voice_name.lower():
                    return v.get("id") or v.get("voice_id") or name
            logger.warning("Explicit voice '%s' not found; falling back to configured defaults", voice_name)

        # 3. Configured default ID (if not "auto")
        if CLONED_VOICE_ID and CLONED_VOICE_ID.lower() != "auto":
            return CLONED_VOICE_ID

        # 4. Resolve configured default name (if not "auto")
        target_name = CLONED_VOICE_NAME
        if target_name and target_name.lower() != "auto":
            voices = self.list_voices()
            for v in voices:
                name = v.get("name", "") or ""
                if name.lower() == target_name.lower():
                    return v.get("id") or v.get("voice_id") or name
            logger.warning("Configured voice '%s' not found; using first available", target_name)

        # 5. Fall back to first available profile
        voices = self.list_voices()
        if voices:
            first = voices[0]
            vid = first.get("id") or first.get("voice_id") or first.get("name")
            logger.info("Using voice: %s (%s)", first.get("name", vid), vid)
            return str(vid)

        logger.error("No voices found in VoiceStudio. Add a cloned voice first.")
        return None

    # ─── Audio Verification & Chunking ────────────────────────────────────────

    @staticmethod
    def split_into_chunks(text: str, max_sentences: int = 3, max_chars: int = 350) -> list[str]:
        """
        Split a narration script into smaller chunks suitable for VoiceStudio TTS.
        VoiceStudio works best generating shorter segments (3-4 sentences maximum).
        Guarantees that no chunk exceeds max_chars, even if a single sentence is long.
        """
        if not text or not text.strip():
            return []

        def split_oversized_sentence(sent: str, limit: int) -> list[str]:
            """Split an oversized sentence on clause punctuation, words, or character limits."""
            if len(sent) <= limit:
                return [sent]
            clauses = [c.strip() for c in re.split(r"(?<=[,;:])\s+", sent) if c.strip()]
            if not clauses:
                clauses = [sent]
            parts: list[str] = []
            curr: list[str] = []
            curr_len = 0
            for clause in clauses:
                if curr and curr_len + len(clause) + 1 > limit:
                    parts.append(" ".join(curr))
                    curr = [clause]
                    curr_len = len(clause)
                else:
                    curr.append(clause)
                    curr_len += len(clause) + (1 if curr else 0)
            if curr:
                parts.append(" ".join(curr))

            sub_parts: list[str] = []
            for part in parts:
                if len(part) <= limit:
                    sub_parts.append(part)
                else:
                    words = part.split()
                    if not words or len(words) == 1:
                        # Single oversized word or token with no whitespace: slice at limit
                        for i in range(0, len(part), limit):
                            sub_parts.append(part[i : i + limit])
                    else:
                        w_curr: list[str] = []
                        w_len = 0
                        for w in words:
                            if len(w) > limit:
                                if w_curr:
                                    sub_parts.append(" ".join(w_curr))
                                    w_curr = []
                                    w_len = 0
                                for i in range(0, len(w), limit):
                                    sub_parts.append(w[i : i + limit])
                            elif w_curr and w_len + len(w) + 1 > limit:
                                sub_parts.append(" ".join(w_curr))
                                w_curr = [w]
                                w_len = len(w)
                            else:
                                w_curr.append(w)
                                w_len += len(w) + (1 if len(w_curr) > 1 else 0)
                        if w_curr:
                            sub_parts.append(" ".join(w_curr))
            return sub_parts

        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        all_chunks: list[str] = []

        for para in paragraphs:
            raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]
            # Recombine incorrectly split abbreviations if any
            sentences: list[str] = []
            skip_next = False
            for s_idx, s in enumerate(raw_sentences):
                if skip_next:
                    skip_next = False
                    continue
                if s.lower().endswith(("e.g.", "i.e.", "vs.", "dr.", "mr.", "mrs.", "etc.")) and s_idx + 1 < len(raw_sentences):
                    sentences.append(s + " " + raw_sentences[s_idx + 1])
                    skip_next = True
                else:
                    sentences.append(s)

            expanded_sentences: list[str] = []
            for s in sentences:
                if len(s) > max_chars:
                    expanded_sentences.extend(split_oversized_sentence(s, max_chars))
                else:
                    expanded_sentences.append(s)

            current_chunk: list[str] = []
            current_len = 0
            for sent in expanded_sentences:
                would_exceed_sentences = len(current_chunk) >= max_sentences
                would_exceed_chars = bool(current_chunk and (current_len + len(sent) + 1 > max_chars))
                if would_exceed_sentences or would_exceed_chars:
                    all_chunks.append(" ".join(current_chunk))
                    current_chunk = [sent]
                    current_len = len(sent)
                else:
                    current_chunk.append(sent)
                    current_len += len(sent) + (1 if len(current_chunk) > 1 else 0)
            if current_chunk:
                all_chunks.append(" ".join(current_chunk))

        return all_chunks

    @staticmethod
    def verify_audio(path: Path) -> float:
        """
        Verify that an audio file exists, is not empty, and return its duration in seconds.
        Returns duration in seconds, or 0.0 if invalid.
        """
        path = Path(path)
        if not path.is_file() or path.stat().st_size < 1000:
            logger.warning("Audio verification failed: file '%s' missing or under 1KB", path)
            return 0.0

        try:
            res = subprocess.run(
                [FFMPEG_PATH, "-i", str(path)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", res.stderr)
            if match:
                h, m, s = match.groups()
                return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception as exc:
            logger.warning("Error inspecting audio duration with ffmpeg: %s", exc)

        return 0.0

    # ─── TTS Generation ──────────────────────────────────────────────────────

    def synthesize_single_chunk(
        self,
        text: str,
        output_path: Path,
        voice_id: Optional[str] = None,
        voice_name: Optional[str] = None,
        model: str = "omnivoice",
        language: Optional[str] = None,
        audio_format: str = "wav",
        speed: float = TTS_SPEED,
        max_retries: int = 3,
    ) -> Optional[Path]:
        """
        Convert a single short text chunk to speech and verify the audio output.
        Retries up to max_retries on failure.
        """
        vid = voice_id or voice_name
        if not vid:
            vid = self.get_voice_id(voice_id=voice_id, voice_name=voice_name)
        if not vid:
            vid = "onyx"  # Default base voice

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model": model,
            "input": text,
            "voice": vid,
            "response_format": audio_format,
            "speed": speed,
        }
        if language and language.lower() not in ["auto", "und"]:
            payload["language"] = language

        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Synthesizing chunk (%d chars) [model=%s, voice=%s, lang=%s, attempt %d/%d]...",
                            len(text), model, vid, language or "auto", attempt, max_retries)
                resp = self.session.post(
                    f"{self.base_url}/v1/audio/speech",
                    json=payload,
                    timeout=120,
                    stream=True,
                )
                resp.raise_for_status()

                with open(output_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                duration = self.verify_audio(output_path)
                if duration > 0.1:
                    logger.info("✅ Chunk synthesized: %s (%.2fs, %.1f KB)",
                                output_path.name, duration, output_path.stat().st_size / 1024)
                    return output_path
                else:
                    logger.warning("Chunk audio verification failed (duration <= 0.1s)")
            except Exception as exc:
                logger.warning("Chunk synthesis attempt %d failed: %s", attempt, exc)
                time.sleep(2)

        logger.error("Failed to synthesize chunk after %d attempts: %s", max_retries, text[:60])
        return None

    def synthesize_chunked(
        self,
        text_or_chunks: Union[str, list[str]],
        output_path: Path,
        voice_id: Optional[str] = None,
        voice_name: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        audio_format: str = TTS_FORMAT,
        speed: float = TTS_SPEED,
        pause_seconds: float = 0.25,
    ) -> tuple[Optional[Path], list[dict]]:
        """
        Synthesize text in short 3-4 sentence chunks, verify each chunk,
        and concatenate them seamlessly with FFmpeg into the final audio file.
        Autonomously routes between KittenTTS (>2 min English), OmniVoice base (<=2 min English),
        and OmniVoice multilingual (non-English) when model/voice are not explicitly fixed.
        """
        chunks = text_or_chunks if isinstance(text_or_chunks, list) else self.split_into_chunks(text_or_chunks)
        if not chunks:
            logger.error("No chunks to synthesize.")
            return None, []

        full_script = " ".join(chunks)

        # Voice and model routing (defaults to KittenTTS for fast explainer narration)
        decision = AutonomousVoiceRouter.route_voice(
            text=full_script,
            requested_language=language,
            requested_voice=voice_id or voice_name,
            requested_model=model if (model and model != "auto") else None,
        )
        model = decision.model
        voice_id = decision.voice
        if not language or language == "auto":
            language = decision.language_code
        logger.info("🧠 Voice Decision: %s / %s (%s)", model, voice_id, decision.reason)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = output_path.parent / f"chunks_{output_path.stem}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Beginning chunked synthesis of %d chunks with VoiceStudio (%s / %s)...", len(chunks), model, voice_id)

        # Generate silence wav file for inter-chunk pauses if requested
        silence_wav = temp_dir / "pause.wav"
        if pause_seconds > 0:
            subprocess.run([
                FFMPEG_PATH, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", str(pause_seconds), str(silence_wav)
            ], capture_output=True, check=True)

        segment_timings: list[dict] = []
        chunk_files: list[Path] = []
        accumulated_time = 0.0

        for idx, chunk_text in enumerate(chunks):
            chunk_wav = temp_dir / f"chunk_{idx:03d}.wav"
            saved = self.synthesize_single_chunk(
                text=chunk_text,
                output_path=chunk_wav,
                voice_id=voice_id,
                voice_name=voice_name,
                model=model,
                language=language,
                audio_format="wav",
                speed=speed,
            )
            if not saved:
                raise RuntimeError(f"Failed to generate chunk {idx}: {chunk_text[:50]}")

            duration = self.verify_audio(chunk_wav)
            segment_timings.append({
                "index": idx,
                "text": chunk_text,
                "path": str(chunk_wav),
                "duration": duration,
                "start": round(accumulated_time, 3),
                "end": round(accumulated_time + duration, 3),
            })
            chunk_files.append(chunk_wav)
            accumulated_time += duration + pause_seconds

        # Stitch all chunks seamlessly with FFmpeg
        logger.info("Concatenating %d chunks into %s...", len(chunk_files), output_path.name)
        ffmpeg_inputs: list[str] = []
        filter_converts: list[str] = []
        concat_inputs: list[str] = []
        input_count = 0

        for idx, c_file in enumerate(chunk_files):
            ffmpeg_inputs.extend(["-i", str(c_file)])
            filter_converts.append(f"[{input_count}:a]aformat=sample_rates=24000:channel_layouts=mono[a{input_count}];")
            concat_inputs.append(f"[a{input_count}]")
            input_count += 1
            if idx < len(chunk_files) - 1 and pause_seconds > 0:
                ffmpeg_inputs.extend(["-i", str(silence_wav)])
                filter_converts.append(f"[{input_count}:a]aformat=sample_rates=24000:channel_layouts=mono[a{input_count}];")
                concat_inputs.append(f"[a{input_count}]")
                input_count += 1

        filter_str = "".join(filter_converts) + "".join(concat_inputs) + f"concat=n={input_count}:v=0:a=1[outa]"
        codec_args = ["-c:a", "libmp3lame", "-b:a", "192k"] if audio_format == "mp3" else ["-c:a", "pcm_s16le"]

        cmd = [FFMPEG_PATH, "-y"] + ffmpeg_inputs + ["-filter_complex", filter_str, "-map", "[outa]"] + codec_args + [str(output_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error("FFmpeg concat failed:\n%s", res.stderr)
            raise RuntimeError(f"FFmpeg concat failed: {res.stderr[:300]}")

        final_duration = self.verify_audio(output_path)
        logger.info("🎉 Chunked voiceover complete: %s (Total duration: %.2fs)", output_path.name, final_duration)

        return output_path, segment_timings

    def synthesize(
        self,
        text: str,
        output_path: Path,
        voice_id: Optional[str] = None,
        voice_name: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        audio_format: str = TTS_FORMAT,
        speed: float = TTS_SPEED,
        force_single: bool = False,
    ) -> Optional[Path]:
        """
        Convert text to speech using autonomous voice routing and save to output_path.
        Automatically chunks into 3-4 sentence segments for high fidelity and stability.
        """
        chunks = self.split_into_chunks(text)
        if len(chunks) > 1 and not force_single:
            path, _ = self.synthesize_chunked(
                text_or_chunks=chunks,
                output_path=output_path,
                voice_id=voice_id,
                voice_name=voice_name,
                model=model,
                language=language,
                audio_format=audio_format,
                speed=speed,
            )
            return path

        return self.synthesize_single_chunk(
            text=text,
            output_path=output_path,
            voice_id=voice_id,
            voice_name=voice_name,
            model=model or "omnivoice",
            language=language,
            audio_format=audio_format,
            speed=speed,
        )

    def synthesize_segments(
        self,
        segments: list[str],
        output_dir: Path,
        voice_id: Optional[str] = None,
        prefix: str = "segment",
    ) -> list[Path]:
        """
        Synthesize multiple text segments into separate audio files.
        Useful for paragraph-by-paragraph narration with sync points.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        vid = self.get_voice_id(voice_id=voice_id)
        results = []
        for i, text in enumerate(segments):
            if not text.strip():
                continue
            path = output_dir / f"{prefix}_{i:03d}.{TTS_FORMAT}"
            try:
                self.synthesize(text, path, voice_id=vid)
                results.append(path)
            except Exception as exc:
                logger.error("Segment %d synthesis failed: %s", i, exc)
        return results
