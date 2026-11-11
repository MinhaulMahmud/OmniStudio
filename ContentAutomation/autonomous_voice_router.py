"""
Autonomous Voice & TTS Engine Router
====================================
Automatically decides the best TTS engine and voice based on:
  1. Detected language (English vs Multilingual / non-English)
  2. Video size / script duration:
     - English & > 2 minutes (120s): uses KittenTTS (real-time long-form English)
     - English & <= 2 minutes (120s): uses OmniVoice base models (e.g. Onyx/Alloy for high-fidelity short-form)
     - Different language (non-English): uses OmniVoice multilingual engine (supports 600+ languages)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional, Union

logger = logging.getLogger("voice_router")

# Threshold for switching to KittenTTS for long-form English (2 minutes in seconds)
LONG_FORM_THRESHOLD_SECONDS = 120.0
# Average speaking rate: ~145-155 words per minute (~2.5 words per second)
WORDS_PER_MINUTE = 150.0


@dataclass
class LanguageInfo:
    code: str
    name: str
    is_english: bool
    confidence: float


@dataclass
class RoutingDecision:
    model: str
    voice: str
    language_code: str
    language_name: str
    estimated_duration_seconds: float
    is_long_form: bool
    reason: str


class AutonomousVoiceRouter:
    """Detects script language and decides the optimal TTS model & voice."""

    # Common stop-word sets for Latin-script languages
    _LATIN_STOPWORDS = {
        "en": {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it",
            "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
            "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
            "an", "will", "my", "one", "all", "would", "there", "their", "what",
            "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
            "when", "make", "can", "like", "time", "no", "just", "him", "know",
            "take", "people", "into", "year", "your", "good", "some", "could",
            "them", "see", "other", "than", "then", "now", "look", "only", "come",
            "its", "over", "think", "also", "back", "after", "use", "two", "how",
            "our", "work", "first", "well", "way", "even", "new", "want", "because",
        },
        "es": {
            "de", "la", "que", "el", "en", "y", "a", "los", "se", "del", "las",
            "por", "un", "para", "con", "no", "una", "su", "al", "lo", "como",
            "más", "pero", "sus", "le", "ya", "o", "este", "sí", "porque", "esta",
            "entre", "cuando", "muy", "sin", "sobre", "también", "me", "hasta",
            "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos",
            "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos",
            "hola", "amigo", "amigos", "gracias", "video", "explicar", "inteligencia",
        },
        "fr": {
            "de", "la", "le", "et", "les", "des", "en", "un", "du", "une", "que",
            "est", "pour", "qui", "dans", "a", "par", "plus", "pas", "au", "sur",
            "ne", "se", "avec", "ce", "il", "sont", "ont", "vous", "mais", "nous",
            "comme", "ou", "si", "leur", "y", "elle", "cette", "sans", "faire",
            "bonjour", "monde", "tout", "tous", "merci", "ici", "bienvenue", "cette",
            "video", "pourquoi", "votre", "notre", "leurs", "comment",
        },
        "de": {
            "der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich",
            "des", "auf", "für", "ist", "im", "dem", "nicht", "ein", "eine", "als",
            "auch", "es", "an", "werden", "aus", "er", "hat", "dass", "sie", "nach",
            "wird", "bei", "einer", "um", "am", "sind", "noch", "wie", "einem",
            "guten", "tag", "hallo", "danke", "bitte", "ihnen", "über", "haben",
        },
        "pt": {
            "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com",
            "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos",
            "como", "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua",
        },
        "it": {
            "di", "e", "il", "che", "la", "a", "in", "per", "una", "un", "del",
            "da", "non", "i", "con", "si", "le", "dei", "delle", "nel", "ma",
            "ha", "come", "ed", "se", "della", "al", "sono", "gli", "questo",
        },
    }

    # Unicode blocks for non-Latin scripts (order matters: check language-specific scripts before common Han)
    _UNICODE_SCRIPTS = [
        (re.compile(r"[\u3040-\u309F\u30A0-\u30FF]"), "ja", "Japanese"),
        (re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF]"), "ko", "Korean"),
        (re.compile(r"[\u0980-\u09FF]"), "bn", "Bengali"),
        (re.compile(r"[\u0900-\u097F]"), "hi", "Hindi"),
        (re.compile(r"[\u0600-\u06FF\u0750-\u077F]"), "ar", "Arabic"),
        (re.compile(r"[\u4E00-\u9FFF]"), "zh", "Chinese"),
        (re.compile(r"[\u0400-\u04FF]"), "ru", "Russian"),
        (re.compile(r"[\u0B80-\u0BFF]"), "ta", "Tamil"),
        (re.compile(r"[\u0C00-\u0C7F]"), "te", "Telugu"),
        (re.compile(r"[\u0E00-\u0E7F]"), "th", "Thai"),
    ]

    _LANG_NAMES = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "pt": "Portuguese",
        "it": "Italian",
        "bn": "Bengali",
        "hi": "Hindi",
        "ar": "Arabic",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ru": "Russian",
        "ta": "Tamil",
        "te": "Telugu",
        "th": "Thai",
    }

    @classmethod
    def detect_language(cls, text: str) -> LanguageInfo:
        """
        Accurately detect the language of a narration script.
        Uses Unicode script recognition and Latin stopword statistical profiling.
        """
        if not text or not text.strip():
            return LanguageInfo("en", "English", True, 1.0)

        clean_text = text.strip()

        # 1. Check Unicode script ranges first (for non-Latin alphabets)
        for pattern, code, name in cls._UNICODE_SCRIPTS:
            matches = pattern.findall(clean_text)
            if len(matches) > 5:
                ratio = len(matches) / max(len(clean_text), 1)
                return LanguageInfo(code, name, False, min(0.99, ratio * 2 + 0.5))

        # 2. For Latin scripts, analyze stopword frequency
        words = [w.lower() for w in re.findall(r"\b[a-zA-Záéíóúüñàèìòùâêîôûäëïöüçãõ]+\b", clean_text)]
        if not words:
            return LanguageInfo("en", "English", True, 0.5)

        total_words = len(words)
        scores: dict[str, int] = {}
        for lang_code, sw_set in cls._LATIN_STOPWORDS.items():
            matches = sum(1 for w in words if w in sw_set)
            scores[lang_code] = matches

        best_lang = max(scores, key=scores.get)
        best_count = scores[best_lang]

        if best_count > 0:
            confidence = min(0.99, best_count / (total_words * 0.4 + 1))
            name = cls._LANG_NAMES.get(best_lang, best_lang)
            return LanguageInfo(best_lang, name, best_lang == "en", confidence)

        # Default fallback to English
        return LanguageInfo("en", "English", True, 0.6)

    @classmethod
    def estimate_duration_seconds(cls, text: str) -> float:
        """Estimate spoken narration duration from text word count and punctuation."""
        words = [w for w in text.split() if w.strip()]
        base_seconds = (len(words) / WORDS_PER_MINUTE) * 60.0
        # Add slight buffer for sentence pauses
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        pause_buffer = len(sentences) * 0.3
        return round(base_seconds + pause_buffer, 2)

    @classmethod
    def route_voice(
        cls,
        text: str,
        requested_language: Optional[str] = None,
        requested_voice: Optional[str] = None,
        requested_model: Optional[str] = None,
        force_kittentts: bool = False,
        force_omnivoice: bool = False,
    ) -> RoutingDecision:
        """
        Autonomous routing engine.

        Decides model & voice based on:
          - Detected Language (English vs Non-English)
          - Video length / script duration:
            - English & > 2 minutes (120s): KittenTTS
            - English & <= 2 minutes (120s): OmniVoice (Onyx/Alloy)
            - Different Language: OmniVoice (Multilingual 600+ languages)
        """
        # Determine language
        if requested_language and requested_language.lower() not in ["auto", ""]:
            lang_code = requested_language.lower().strip()
            lang_name = cls._LANG_NAMES.get(lang_code, lang_code.capitalize())
            is_english = (lang_code in ["en", "english"])
            lang_info = LanguageInfo(lang_code, lang_name, is_english, 1.0)
        else:
            lang_info = cls.detect_language(text)

        est_duration = cls.estimate_duration_seconds(text)
        is_long_form = est_duration > LONG_FORM_THRESHOLD_SECONDS

        # If user explicitly specified both model and voice, honor the explicit request
        if requested_model and requested_voice:
            return RoutingDecision(
                model=requested_model,
                voice=requested_voice,
                language_code=lang_info.code,
                language_name=lang_info.name,
                estimated_duration_seconds=est_duration,
                is_long_form=is_long_form,
                reason=f"User explicitly requested model='{requested_model}' and voice='{requested_voice}'.",
            )

        # ─── Autonomous Decision Matrix ──────────────────────────────────────

        # CASE 1: Non-English Language (Multilingual)
        # KittenTTS only supports English, so any other language MUST use OmniVoice.
        if not lang_info.is_english:
            selected_model = "omnivoice"
            # In OmniVoice, base preset or profile supporting target language
            selected_voice = requested_voice or "alloy"
            reason = (
                f"🌍 Autonomous Decision: Language detected as '{lang_info.name}' ({lang_info.code}). "
                f"KittenTTS only supports English. Routed to OmniVoice multilingual engine "
                f"(600+ languages) with voice='{selected_voice}'."
            )
            return RoutingDecision(
                model=selected_model,
                voice=selected_voice,
                language_code=lang_info.code,
                language_name=lang_info.name,
                estimated_duration_seconds=est_duration,
                is_long_form=is_long_form,
                reason=reason,
            )

        # CASE 2: English Language — KittenTTS is the DEFAULT for ANY size audio
        # User requirement: "default is kitten tts for any size audio but keep option to use other voice models"
        if requested_voice and requested_voice.lower() in ["minhaz", "e50a2165", "onyx", "alloy"]:
            selected_model = requested_model or "omnivoice"
            selected_voice = requested_voice
            reason = (
                f"🎙️ User Selection: Explicit voice '{requested_voice}' requested. "
                f"Routed to OmniVoice model with voice='{selected_voice}'."
            )
            return RoutingDecision(
                model=selected_model,
                voice=selected_voice,
                language_code=lang_info.code,
                language_name=lang_info.name,
                estimated_duration_seconds=est_duration,
                is_long_form=is_long_form,
                reason=reason,
            )

        # Default for any size audio: KittenTTS
        selected_model = requested_model or "kittentts"
        selected_voice = requested_voice or "expr-voice-2-m"
        reason = (
            f"⚡ KittenTTS Explainer (Default): Script (~{est_duration:.1f}s) routed to KittenTTS "
            f"with voice='{selected_voice}' for fast, effective, and authentic explainer narration."
        )
        return RoutingDecision(
            model=selected_model,
            voice=selected_voice,
            language_code=lang_info.code,
            language_name=lang_info.name,
            estimated_duration_seconds=est_duration,
            is_long_form=is_long_form,
            reason=reason,
        )
