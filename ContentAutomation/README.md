# 🎬 Content Automation — Autonomous AI Video & Motion Graphics Engine

An end-to-end content automation pipeline that:
1. **Researches** trending topics & extracts **spoken video transcripts** using `yt-dlp` (YouTube, Shorts, TikTok)
2. **Writes technical scripts** using **Llama 3.3 70B** (via OpenRouter or Omniroute 1.6B token proxy)
3. **Synthesizes studio voiceover** using **KittenTTS** or **OmniVoice cloned voices** (with 32-bit float original quality, refinement passes, and EBU R128 volume leveling)
4. **Renders direct React motion graphics** via **Remotion** (turbofan jet engines, engine cutaways, constant-mesh gearboxes, compute matrices, TopoJSON maps, and floating telemetry HUDs)
5. **Generates synchronized subtitles** (ASS karaoke, SRT, WebVTT)
6. **Composes final videos** across multiple aspect ratios (16:9 Landscape, 9:16 Vertical, 1:1 Square, 4:5 Portrait)

## 🏗️ Architecture

```
ContentAutomation/
├── pipeline.py                    ← Master orchestrator pipeline
├── config.py                      ← Central configuration & audio defaults
├── researcher.py                  ← yt-dlp competitor metadata & spoken transcript extractor
├── topic_intelligence.py          ← AI typo corrector & search grounding agent
├── script_generator.py            ← OpenRouter Llama 3.3 70B visual storyboard generator
├── autonomous_voice_router.py     ← Smart voice & engine router (KittenTTS / OmniVoice)
├── voice_client.py                ← VoiceStudio client (32-bit float, refinement, volume leveling)
├── remotion_renderer.py           ← Remotion CLI Node.js renderer with dynamic props
├── video_composer.py              ← FFmpeg multi-format compositor & subtitle burning
├── subtitle_generator.py          ← Word-level subtitle generator (ASS/SRT/VTT)
├── platform_profiles.py           ← Platform safe zones, layout modes, duration budgeting
├── remotion/                      ← Remotion React motion graphics project
│   └── src/
│       ├── DynamicExplainer.tsx   ← Core multi-layer motion graphics canvas
│       └── components/            ← TurbofanJetMechanism, VisualMechanismViewport, etc.
├── tests/                         ← Automated test suite (66 unit tests)
└── output/                        ← Delivered MP4 videos, scripts, audio & subtitles
```

## ⚡ Quick Start

### Prerequisites

| Tool | Required | How to Get |
|------|----------|-----------|
| VoiceStudio | ✅ Yes | Local app running at `http://localhost:3900` |
| Python 3.11+ | ✅ Yes | Installed in environment |
| Node.js 18+ | ✅ Yes | Required for Remotion rendering |
| yt-dlp | ✅ Yes | Included in `requirements.txt` |
| FFmpeg | ✅ Yes | Installed and in system PATH |
| OpenRouter API key | Recommended | Set `OPENROUTER_API_KEY` in `.env` |

### Running the Pipeline

```powershell
# 1. Jet Propulsion explainer for YouTube Shorts (9:16 Vertical)
python pipeline.py --topic "Jet Propulsion Basics" --ratio 9:16

# 2. Mechanical Gearbox explainer with explicit 60-second duration budget (16:9 Landscape)
python pipeline.py --topic "how bike gearbox works" --ratio 16:9 --duration 60

# 3. AI Model Weights explainer with your cloned voice and studio editing quality
python pipeline.py --topic "AI model weights" --voice-name Minhaz --audio-quality editing

# 4. List available voices in VoiceStudio
python pipeline.py --list-voices

# 5. Run automated test suite
python -m pytest tests/
```
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
