"""
ContentAutomation Configuration
================================
Central configuration for the entire content automation pipeline.
Edit this file to match your environment and preferences.
"""
import os
from pathlib import Path

# ─── Project Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"
TEMPLATES_DIR = BASE_DIR / "templates"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Load local .env if present
def _load_env_file():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v

_load_env_file()

# Ensure directories exist
for _d in [OUTPUT_DIR, ASSETS_DIR, LOGS_DIR, TEMPLATES_DIR, SCRIPTS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ─── VoiceStudio (KittenTTS & OmniVoice) Configuration ─────────────────────────
VOICESTUDIO_BASE_URL = os.getenv("VOICESTUDIO_URL", "http://localhost:3900")
VOICESTUDIO_API_KEY = os.getenv("VOICESTUDIO_API_KEY", "voicestudio")  # local instance key

# Voice Configuration: Default to KittenTTS for fast, effective explainer narration on any size audio
DEFAULT_TTS_MODEL = os.getenv("DEFAULT_TTS_MODEL", "kittentts")
DEFAULT_TTS_VOICE = os.getenv("DEFAULT_TTS_VOICE", "expr-voice-2-m")
CLONED_VOICE_ID = os.getenv("CLONED_VOICE_ID", "expr-voice-2-m")
CLONED_VOICE_NAME = os.getenv("CLONED_VOICE_NAME", "expr-voice-2-m")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "auto")        # "auto" or ISO code
LONG_FORM_THRESHOLD_SECONDS = float(os.getenv("LONG_FORM_THRESHOLD_SECONDS", "120.0"))

# TTS audio format: mp3, wav, opus, flac, aac, pcm
TTS_FORMAT = "mp3"
TTS_SPEED = 1.0   # 0.25 – 4.0

# ─── AI / LLM Configuration ───────────────────────────────────────────────────
# Backends: "omniroute" | "openrouter" | "ollama" | "openai" | "gemini"
LLM_BACKEND = os.getenv("LLM_BACKEND", "omniroute")

# OpenRouter (Global model gateway - used wisely with cost-effective, high-accuracy models)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

# Omniroute (1.6B tokens via local proxy http://localhost:20128)
OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_URL", "http://localhost:20128")
OMNIROUTE_AUTH_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN", "omniroute")
OMNIROUTE_MODEL = os.getenv("ANTHROPIC_MODEL", "auto/best-free")
IMAGE_GENERATION_URL = os.getenv("IMAGE_GENERATION_URL", "http://localhost:20128/v1/images/generations")

# Ollama settings (local, completely free)
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Optional paid alternatives (automatic quota failover)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ─── Content Research Configuration ───────────────────────────────────────────
# Social media platforms to search for ideas
RESEARCH_PLATFORMS = ["youtube", "tiktok", "instagram", "twitter"]

# yt-dlp settings for fetching video metadata
YT_DLP_MAX_RESULTS = 10        # Number of videos to analyze per search
YT_DLP_LANGUAGE = "en"        # Preferred language filter
YT_DLP_DATE_FILTER = "week"   # today | week | month | year

# Keywords/topics to research (can be overridden via CLI)
DEFAULT_TOPICS = [
    "AI tools 2026",
    "productivity hacks",
    "tech tutorials",
]

# ─── Video Generation Configuration ───────────────────────────────────────────
def _find_ffmpeg_path() -> str:
    """Auto-detect FFmpeg binary from multiple known locations."""
    env_path = os.getenv("FFMPEG_PATH", "")
    if env_path and os.path.isfile(env_path):
        return env_path

    candidates = [
        # imageio-ffmpeg (Python package that bundles FFmpeg)
        _get_imageio_ffmpeg(),
        # Common Windows install paths
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(os.environ.get("APPDATA", ""), "ffmpeg", "bin", "ffmpeg.exe"),
        # winget installs to ~/AppData/Local/Microsoft/WinGet
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe", "ffmpeg-7.1-full_build", "bin", "ffmpeg.exe"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c

    # Fall back to PATH lookup
    import shutil
    found = shutil.which("ffmpeg")
    return found or "ffmpeg"


def _get_imageio_ffmpeg() -> str:
    """Try to get ffmpeg path from imageio-ffmpeg package."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


FFMPEG_PATH = _find_ffmpeg_path()
FFPROBE_PATH = os.getenv("FFPROBE_PATH", "ffprobe")

# Video resolution and quality
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1920"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1080"))
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
VIDEO_BITRATE = os.getenv("VIDEO_BITRATE", "5000k")

# Short-form video (Reels/Shorts/TikTok)
SHORT_WIDTH = 1080
SHORT_HEIGHT = 1920

# Background video/image options
USE_BACKGROUND_VIDEO = True        # Use stock footage as background
BACKGROUND_VIDEO_DIR = ASSETS_DIR / "backgrounds"
BACKGROUND_COLOR = "#0d0d1a"      # Dark fallback background

# Captions / subtitles
GENERATE_CAPTIONS = True
CAPTION_FONT_SIZE = 60
CAPTION_FONT_COLOR = "white"
CAPTION_SHADOW_COLOR = "black"
CAPTION_POSITION = "center"       # top | center | bottom
WORDS_PER_SUBTITLE = 4            # Words per subtitle chunk

# ─── Content Scheduling ───────────────────────────────────────────────────────
# How many videos to produce per automation run
VIDEOS_PER_RUN = 1
# Output formats to generate
OUTPUT_FORMATS = ["youtube", "shorts", "tiktok"]

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "automation.log"
