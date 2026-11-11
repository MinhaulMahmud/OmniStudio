# 🎬 Content Automation — Voice-Cloned Video Creator

An end-to-end content automation pipeline that:
1. **Researches** trending topics using `yt-dlp` (YouTube, TikTok, Instagram)
2. **Writes scripts** using an LLM (OpenAI GPT or Google Gemini)
3. **Synthesizes narration** with your **cloned voice** from VoiceStudio
4. **Generates subtitles** (SRT, WebVTT, ASS)
5. **Composes videos** in multiple formats (YouTube 16:9, Shorts/TikTok 9:16)

## 🏗️ Architecture

```
ContentAutomation/
├── main.py               ← CLI entry point
├── pipeline.py           ← Full orchestration pipeline
├── config.py             ← All configuration settings
├── researcher.py         ← yt-dlp trend research engine
├── script_generator.py   ← LLM script writing (OpenAI/Gemini)
├── voice_client.py       ← VoiceStudio TTS client
├── subtitle_generator.py ← SRT/VTT/ASS subtitle generation
├── video_composer.py     ← FFmpeg video assembly
├── background_manager.py ← Stock background asset manager
├── composition_plan.py   ← Remotion-style composition plans
├── scheduler.py          ← Automated content scheduling
├── output/               ← Generated videos, audio, scripts
├── assets/backgrounds/   ← Background videos/images
└── logs/                 ← Run logs and research data
```

## ⚡ Quick Start

### Prerequisites

| Tool | Required | How to Get |
|------|----------|-----------|
| VoiceStudio | ✅ Yes | Already installed at `E:\Omniroute\openstudio\VoiceStudio` |
| Python 3.11+ | ✅ Yes | Already installed |
| yt-dlp | ✅ Yes | Already installed (`pip install yt-dlp`) |
| FFmpeg | ✅ For video | [Download](https://ffmpeg.org/download.html) → add to PATH |
| OpenAI API key | Recommended | [platform.openai.com](https://platform.openai.com) |

### Setup

1. **Configure your environment:**
   ```powershell
   cd E:\Omniroute\openstudio\ContentAutomation
   copy .env.example .env
   # Edit .env with your API keys and voice settings
   ```

2. **Start VoiceStudio** — open the VoiceStudio app and make sure your cloned voice is ready.

3. **Check system status:**
   ```powershell
   python main.py status
   ```

4. **List your cloned voices:**
   ```powershell
   python main.py list-voices
   ```

5. **Set your voice** in `config.py` or `.env`:
   ```
   CLONED_VOICE_NAME=My Voice Name
   ```

## 🚀 Usage

### Full Pipeline (Research → Script → Voice → Video)
```powershell
# Generate a YouTube video on a topic
python main.py run --topic "AI productivity tools 2026"

# Specific platform
python main.py run --topic "Python one-liners" --platform shorts

# Multiple topics
python main.py run --topics "AI tools,ChatGPT tips,Python 2026"

# Use your specific voice
python main.py run --topic "Tech news" --voice-name "My Voice"

# Generate both YouTube and Shorts formats
python main.py run --topic "AI tips" --formats youtube,shorts
```

### Individual Steps

```powershell
# Research only
python main.py research --topics "AI tools,productivity"

# Script only
python main.py script --topic "AI tools 2026" --platform youtube

# Synthesize audio only
python main.py synthesize --text "Hello world, this is a test of my cloned voice"

# Check status
python main.py status

# List available voices
python main.py list-voices
```

### Skip Steps
```powershell
# Skip research (faster, no yt-dlp calls)
python main.py run --topic "AI tips" --no-research

# Skip video (only generate audio + script)
python main.py run --topic "AI tips" --no-video
```

### Use an Existing Script
```powershell
python main.py run --from-script logs/script_AI_tips_20261109.json
```

## 🎙️ Voice Configuration

Your VoiceStudio cloned voice is used via the **OpenAI-compatible TTS API** at `http://localhost:3900`.

1. Open VoiceStudio
2. Create or select your cloned voice
3. Run `python main.py list-voices` to find your voice ID/name
4. Set in `config.py` or `.env`:
   ```
   CLONED_VOICE_ID=your-voice-id
   # OR
   CLONED_VOICE_NAME=Your Voice Name
   ```

## 🤖 LLM for Script Writing

Set ONE of:
```env
OPENAI_API_KEY=sk-...
# OR
GEMINI_API_KEY=...
```

Without an API key, the pipeline uses a **template-based fallback** that generates placeholder scripts. These work but won't be as engaging.

## 📹 FFmpeg Setup (Required for Video)

FFmpeg is required for video composition. Install it:

**Option 1: Download binary**
1. Go to https://ffmpeg.org/download.html
2. Download "Windows builds from gyan.dev"
3. Extract to `C:\ffmpeg\`
4. Add `C:\ffmpeg\bin` to your system PATH

**Option 2: via winget**
```powershell
winget install -e --id Gyan.FFmpeg
```

**Option 3: via chocolatey**
```powershell
choco install ffmpeg
```

Then set in `.env`:
```
FFMPEG_PATH=C:/ffmpeg/bin/ffmpeg.exe
```

## 📂 Adding Background Videos

Place video files (MP4, MOV) or images in `assets/backgrounds/`:
```powershell
# Copy a background video
copy my_background.mp4 E:\Omniroute\openstudio\ContentAutomation\assets\backgrounds\
```

Or use the Pexels API (set `PEXELS_API_KEY` in `.env`).

## ⏰ Automated Scheduling

### Run once daily at 9 AM via Windows Task Scheduler:
```powershell
python scheduler.py windows-task --name "ContentAutomation" --hour 9 --topic "AI tools 2026"
```

### Run as a background daemon:
```powershell
python scheduler.py daemon
```

## 🗂️ Output Structure

Each pipeline run creates a timestamped folder:
```
output/
└── 20261109_175000/
    ├── research_AI_tools_2026.json      ← Trend research data
    ├── script_AI_tools_2026.json        ← Generated script
    ├── audio_AI_tools_2026.mp3          ← Cloned voice narration
    ├── subtitles_AI_tools_2026.srt      ← Subtitle file
    ├── video_AI_tools_2026_youtube.mp4  ← YouTube 1920×1080
    └── video_AI_tools_2026_shorts.mp4   ← Shorts 1080×1920
```

## 🔮 Remotion Integration (Future)

For advanced motion graphics (animated titles, kinetic text, transitions),
the pipeline includes `composition_plan.py` which generates Remotion-compatible
configuration. See `composition_plan.py` for setup instructions.

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "VoiceStudio not running" | Open VoiceStudio app first |
| "No voices found" | Add a cloned voice in VoiceStudio |
| "FFmpeg not found" | Install FFmpeg and add to PATH |
| "OpenAI API error" | Check OPENAI_API_KEY in .env |
| yt-dlp errors | Some platforms require cookies; run `yt-dlp --cookies-from-browser chrome URL` |
