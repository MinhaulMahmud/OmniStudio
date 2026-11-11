"""
OpenStudio Unified Content Automation Dashboard
================================================
A complete single dashboard providing:
  - Video Generation Studio (Pipeline runner with Live Autonomous Voice Routing)
  - Interactive Media Player (Videos, Audios, Subtitles, Backgrounds)
  - Voice Studio & TTS Playground (Cloned voices, Base TTS, KittenTTS)
  - Real-time System Status, Log Streamer, and Asset Manager

Run with:
  python dashboard.py --port 8080
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Ensure ContentAutomation root is on path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    OUTPUT_DIR,
    VOICESTUDIO_BASE_URL,
    FFMPEG_PATH,
    DEFAULT_TOPICS,
    OUTPUT_FORMATS,
    LOG_FILE,
)
from autonomous_voice_router import AutonomousVoiceRouter
from voice_client import VoiceStudioClient
from video_composer import VideoComposer

logger = logging.getLogger("dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="OpenStudio Content Automation Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory pipeline job tracker
active_job = {
    "status": "idle",  # idle | running | completed | failed
    "topic": "",
    "started_at": None,
    "finished_at": None,
    "progress_percent": 0,
    "current_step": "",
    "logs": [],
    "error": None,
    "result": None,
}


class PipelineRequest(BaseModel):
    topic: str
    platform: str = "youtube"
    formats: list[str] = ["youtube", "shorts"]
    language: str = "auto"
    voice: str = "auto"
    model: str = "auto"
    custom_script: Optional[dict] = None
    skip_research: bool = False
    skip_video: bool = False


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "auto"
    model: str = "auto"
    language: str = "auto"
    speed: float = 1.0


class RoutePreviewRequest(BaseModel):
    text: str
    language: Optional[str] = "auto"
    voice: Optional[str] = "auto"
    model: Optional[str] = "auto"


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/status")
def get_system_status():
    """Get health and diagnostic status of all subsystem components."""
    client = VoiceStudioClient()
    voice_running = client.is_running()
    voices = []
    if voice_running:
        try:
            raw_v = client.list_voices()
            voices = raw_v if isinstance(raw_v, list) else []
        except Exception:
            pass

    ffmpeg_valid = False
    ffmpeg_ver = ""
    try:
        res = subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            ffmpeg_valid = True
            m = re.search(r"ffmpeg version (\S+)", res.stdout)
            ffmpeg_ver = m.group(1) if m else "installed"
    except Exception:
        pass

    remotion_ready = bool(shutil.which("npx") or shutil.which("npx.cmd"))

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "voicestudio": {
            "online": voice_running,
            "url": VOICESTUDIO_BASE_URL,
            "voices_count": len(voices),
        },
        "ffmpeg": {
            "available": ffmpeg_valid,
            "path": FFMPEG_PATH,
            "version": ffmpeg_ver,
        },
        "remotion": {
            "ready": remotion_ready,
            "project_path": str(BASE_DIR / "remotion"),
        },
        "output_dir": str(OUTPUT_DIR),
        "job": active_job,
    }


@app.get("/api/voices")
def get_voices():
    """Return list of all available voices and engines."""
    client = VoiceStudioClient()
    voices = []
    engines = []
    if client.is_running():
        try:
            voices = client.list_voices()
        except Exception:
            pass
        try:
            resp = client.session.get(f"{client.base_url}/engines/tts", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                engines = data.get("backends", []) if isinstance(data, dict) else []
        except Exception:
            pass

    # Preset voices for quick selection
    presets = [
        {"id": "auto", "name": "🧠 Autonomous Decision (Recommended)", "type": "smart", "description": "Auto-selects KittenTTS for >2 min English, OmniVoice base for <=2 min English, and OmniVoice for other languages."},
        {"id": "onyx", "name": "Onyx (OmniVoice Base Narrator)", "type": "base", "description": "Authoritative, rich English narrator voice (best for tech explainers)."},
        {"id": "alloy", "name": "Alloy (OmniVoice Neutral / Multilingual)", "type": "base", "description": "Balanced, crisp voice suitable for English and multilingual narration."},
        {"id": "expr-voice-2-m", "name": "KittenTTS Male (expr-voice-2-m)", "type": "kittentts", "description": "Real-time CPU long-form English voice."},
        {"id": "expr-voice-2-f", "name": "KittenTTS Female (expr-voice-2-f)", "type": "kittentts", "description": "Real-time CPU long-form English female voice."},
        {"id": "e50a2165", "name": "Minhaz (Cloned Voice Profile)", "type": "clone", "description": "User's personalized cloned voice profile."},
    ]

    return {
        "presets": presets,
        "voices": voices,
        "engines": [e for e in engines if e.get("available")],
    }


@app.post("/api/route-preview")
def preview_voice_route(req: RoutePreviewRequest):
    """Preview the autonomous voice & model decision for a given script."""
    decision = AutonomousVoiceRouter.route_voice(
        text=req.text,
        requested_language=req.language if req.language != "auto" else None,
        requested_voice=req.voice if req.voice != "auto" else None,
        requested_model=req.model if req.model != "auto" else None,
    )
    return {
        "model": decision.model,
        "voice": decision.voice,
        "language_code": decision.language_code,
        "language_name": decision.language_name,
        "is_english": decision.language_code == "en",
        "estimated_duration_seconds": decision.estimated_duration_seconds,
        "is_long_form": decision.is_long_form,
        "reason": decision.reason,
    }


@app.post("/api/synthesize")
def synthesize_audio(req: SynthesizeRequest):
    """Quick TTS synthesis for the playground."""
    client = VoiceStudioClient()
    if not client.is_running():
        raise HTTPException(status_code=503, detail="VoiceStudio backend is not running at " + VOICESTUDIO_BASE_URL)

    timestamp = int(time.time())
    out_name = f"preview_{timestamp}.mp3"
    out_path = OUTPUT_DIR / out_name

    decision = AutonomousVoiceRouter.route_voice(
        text=req.text,
        requested_language=req.language if req.language != "auto" else None,
        requested_voice=req.voice if req.voice != "auto" else None,
        requested_model=req.model if req.model != "auto" else None,
    )

    path, timings = client.synthesize_chunked(
        text_or_chunks=req.text,
        output_path=out_path,
        voice_id=decision.voice,
        model=decision.model,
        language=decision.language_code,
        speed=req.speed,
    )

    if not path or not path.exists():
        raise HTTPException(status_code=500, detail="Synthesis failed")

    return {
        "status": "success",
        "filename": out_name,
        "url": f"/media/{out_name}",
        "decision": {
            "model": decision.model,
            "voice": decision.voice,
            "language": decision.language_code,
            "reason": decision.reason,
        },
        "duration": client.verify_audio(path),
        "timings": timings,
    }


def _run_pipeline_worker(req: PipelineRequest):
    global active_job
    active_job["status"] = "running"
    active_job["topic"] = req.topic
    active_job["started_at"] = datetime.now().isoformat()
    active_job["finished_at"] = None
    active_job["progress_percent"] = 5
    active_job["current_step"] = "Initializing Pipeline"
    active_job["logs"] = []
    active_job["error"] = None
    active_job["result"] = None

    def log_cb(msg: str, step: str = "", pct: int = -1):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"{timestamp} │ {msg}"
        active_job["logs"].append(entry)
        if step:
            active_job["current_step"] = step
        if pct >= 0:
            active_job["progress_percent"] = pct
        logger.info(entry)

    try:
        log_cb(f"🚀 Starting automation pipeline for: '{req.topic}'", "Research & Script", 10)

        from pipeline import ContentAutomationPipeline
        pipeline = ContentAutomationPipeline()

        custom_script_obj = None
        if req.custom_script:
            from script_generator import VideoScript
            custom_script_obj = VideoScript(
                title=req.custom_script.get("title", req.topic),
                platform=req.platform,
                hook=req.custom_script.get("hook", ""),
                sections=req.custom_script.get("sections", []),
                cta=req.custom_script.get("cta", ""),
            )

        log_cb("Analyzing topic and generating narration script...", "Script Generation", 25)
        results = pipeline.run(
            topics=[req.topic],
            platform=req.platform,
            formats=req.formats,
            voice_id=req.voice if req.voice != "auto" else None,
            voice_name=req.voice if req.voice != "auto" else None,
            language=req.language if req.language != "auto" else None,
            skip_research=req.skip_research,
            skip_video=req.skip_video,
            custom_script=custom_script_obj,
        )

        log_cb("🎉 Pipeline execution completed successfully!", "Finished", 100)
        active_job["status"] = "completed"
        active_job["finished_at"] = datetime.now().isoformat()
        active_job["result"] = results

    except Exception as exc:
        logger.exception("Pipeline execution failed: %s", exc)
        active_job["status"] = "failed"
        active_job["finished_at"] = datetime.now().isoformat()
        active_job["error"] = str(exc)
        log_cb(f"❌ Error: {exc}", "Failed", active_job["progress_percent"])


@app.post("/api/pipeline/run")
def trigger_pipeline(req: PipelineRequest, background_tasks: BackgroundTasks):
    global active_job
    if active_job["status"] == "running":
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress.")

    background_tasks.add_task(_run_pipeline_worker, req)
    return {"status": "started", "topic": req.topic}


@app.get("/api/pipeline/job")
def get_pipeline_job():
    return active_job


@app.get("/api/media")
def list_media():
    """List all generated media files (videos, audio, subtitles, images)."""
    items = []
    if OUTPUT_DIR.exists():
        for p in sorted(OUTPUT_DIR.glob("*.*"), key=os.path.getmtime, reverse=True):
            if p.is_file() and not p.name.startswith("."):
                size_mb = p.stat().st_size / (1024 * 1024)
                ext = p.suffix.lower()
                mtype = "other"
                if ext in [".mp4", ".mov", ".webm"]:
                    mtype = "video"
                elif ext in [".mp3", ".wav", ".opus", ".ogg"]:
                    mtype = "audio"
                elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    mtype = "image"
                elif ext in [".srt", ".ass", ".vtt"]:
                    mtype = "subtitle"

                items.append({
                    "name": p.name,
                    "type": mtype,
                    "size_mb": round(size_mb, 2),
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                    "url": f"/media/{p.name}",
                })

    return {"media": items, "total": len(items)}


@app.get("/media/{filename}")
def serve_media(filename: str):
    """Serve media files directly to the browser players."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    mime_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(file_path, media_type=mime_type or "application/octet-stream")


@app.get("/api/logs")
def get_logs(lines: int = Query(default=100)):
    """Return the last N lines from automation.log."""
    if not LOG_FILE.exists():
        return {"logs": ["Log file does not exist yet."]}

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            return {"logs": [l.strip() for l in all_lines[-lines:]]}
    except Exception as exc:
        return {"logs": [f"Error reading logs: {exc}"]}


# ─── HTML Single Page Application Dashboard ───────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OpenStudio — Autonomous Content & Voice Studio</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #090d16; color: #f1f5f9; }
    code, pre { font-family: 'JetBrains Mono', monospace; }
    .glass { background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .glass-active { background: rgba(30, 41, 59, 0.85); border-color: rgba(99, 102, 241, 0.4); }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0b0f19; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }
    .gradient-text { background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  </style>
</head>
<body class="min-h-screen flex flex-col">

  <!-- Top Navigation Header -->
  <header class="glass sticky top-0 z-50 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
        <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" /></svg>
      </div>
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          OpenStudio <span class="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 font-semibold border border-indigo-500/30">Autonomous</span>
        </h1>
        <p class="text-xs text-slate-400">Unified Content Automation, VoiceStudio & Video Dashboard</p>
      </div>
    </div>

    <!-- Subsystem Health Indicators -->
    <div class="flex items-center gap-3 text-xs">
      <div id="badge-voice" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700">
        <span class="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse"></span>
        <span class="font-medium text-slate-300">VoiceStudio : Checking</span>
      </div>
      <div id="badge-ffmpeg" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700">
        <span class="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
        <span class="font-medium text-slate-300">FFmpeg</span>
      </div>
      <div id="badge-remotion" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700">
        <span class="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
        <span class="font-medium text-slate-300">Remotion</span>
      </div>
    </div>
  </header>

  <!-- Main Tabs Navigation -->
  <div class="border-b border-slate-800 bg-slate-900/60 px-6 py-2.5 flex items-center gap-2">
    <button onclick="switchTab('studio')" id="tab-btn-studio" class="px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 bg-indigo-600 text-white shadow-md shadow-indigo-600/20">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
      🎬 Pipeline Studio
    </button>
    <button onclick="switchTab('library')" id="tab-btn-library" class="px-4 py-2 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition flex items-center gap-2">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
      📁 Media Library & Player
    </button>
    <button onclick="switchTab('tts')" id="tab-btn-tts" class="px-4 py-2 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition flex items-center gap-2">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z"/></svg>
      🎙️ Voice Studio Playground
    </button>
    <button onclick="switchTab('logs')" id="tab-btn-logs" class="px-4 py-2 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition flex items-center gap-2">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
      📊 System Logs & Monitor
    </button>
  </div>

  <!-- Main Content Container -->
  <main class="flex-1 p-6 max-w-7xl w-full mx-auto">

    <!-- ─────────────────────────────────────────────────────────────
         TAB 1: PIPELINE STUDIO
         ───────────────────────────────────────────────────────────── -->
    <div id="tab-studio" class="space-y-6">

      <!-- Autonomous Routing Status Banner -->
      <div id="auto-route-card" class="glass p-5 rounded-2xl border-l-4 border-l-indigo-500 shadow-xl transition-all">
        <div class="flex items-start justify-between">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold uppercase tracking-wider text-indigo-400">Autonomous Voice Decision</span>
              <span id="route-badge-model" class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Auto Routing Active</span>
              <span id="route-badge-lang" class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">English (en)</span>
            </div>
            <p id="route-reason" class="text-sm text-slate-300">Type a topic or script below to see real-time engine routing.</p>
          </div>
          <div class="text-right">
            <span class="text-xs text-slate-400 block">Est. Video Length</span>
            <span id="route-duration" class="text-lg font-bold text-white">~0s</span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Left Column: Input Form (2 Cols) -->
        <div class="lg:col-span-2 space-y-5">
          <div class="glass p-6 rounded-2xl space-y-5">
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-indigo-500"></span> Video Topic & Parameters
            </h2>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">Video Topic or Idea Prompt</label>
              <input type="text" id="topic-input" class="w-full bg-slate-900/90 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm font-medium transition"
                     placeholder="e.g. Spark-X2.6-71.7B a fine model that can run on home laptop"
                     value="Spark-X2.6-71.7B a fine model that can run on home laptop"
                     oninput="updateRoutePreview()">
            </div>

            <!-- Quick Preset Topics -->
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-xs text-slate-500 font-medium">Try:</span>
              <button onclick="setTopic('Spark-X2.6-71.7B a fine model that can run on home laptop')" class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition">Spark-X2.6-71.7B</button>
              <button onclick="setTopic('How AI Model Weights Determine Compute Power and VRAM')" class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition">Model Weights</button>
              <button onclick="setTopic('Top 5 Open Source AI Models in 2026 for Developers')" class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition">Top 5 Models</button>
              <button onclick="setTopic('¿Cómo funciona la cuantización en modelos de lenguaje?', 'es')" class="text-xs px-2.5 py-1 rounded-lg bg-purple-900/40 text-purple-300 border border-purple-500/30 hover:bg-purple-900/60 transition">Español (AI)</button>
              <button onclick="setTopic('কীভাবে এআই মডেল কাজ করে এবং জিপিইউ মেমোরি ব্যবহার করে', 'bn')" class="text-xs px-2.5 py-1 rounded-lg bg-emerald-900/40 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-900/60 transition">বাংলা (AI)</button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Target Language</label>
                <select id="lang-select" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500" onchange="updateRoutePreview()">
                  <option value="auto">🧠 Auto-Detect Language</option>
                  <option value="en">English (en)</option>
                  <option value="es">Spanish (Español)</option>
                  <option value="bn">Bengali (বাংলা)</option>
                  <option value="fr">French (Français)</option>
                  <option value="de">German (Deutsch)</option>
                  <option value="hi">Hindi (हिन्दी)</option>
                  <option value="ja">Japanese (日本語)</option>
                  <option value="zh">Chinese (中文)</option>
                  <option value="ar">Arabic (العربية)</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Voice Preference</label>
                <select id="voice-select" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500" onchange="updateRoutePreview()">
                  <option value="auto">🧠 Autonomous Voice Router</option>
                  <option value="onyx">Onyx (OmniVoice Male Narrator)</option>
                  <option value="alloy">Alloy (OmniVoice Multilingual)</option>
                  <option value="expr-voice-2-m">KittenTTS Male (expr-voice-2-m)</option>
                  <option value="expr-voice-2-f">KittenTTS Female (expr-voice-2-f)</option>
                  <option value="e50a2165">Minhaz (Cloned Voice Profile)</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Primary Format</label>
                <select id="platform-select" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500">
                  <option value="youtube">YouTube (16:9 Landscape)</option>
                  <option value="shorts">Shorts / TikTok (9:16 Vertical)</option>
                  <option value="instagram">Instagram (1:1 Square)</option>
                </select>
              </div>
            </div>

            <!-- Custom Script Collapsible -->
            <details class="group bg-slate-900/60 rounded-xl border border-slate-800">
              <summary class="cursor-pointer p-4 text-xs font-semibold text-slate-300 flex items-center justify-between select-none">
                <span class="flex items-center gap-2">✍️ Custom Script Override (Optional)</span>
                <span class="text-slate-500 group-open:rotate-180 transition">▼</span>
              </summary>
              <div class="p-4 pt-0 space-y-3">
                <textarea id="custom-script-text" rows="5" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                          placeholder="Paste or write custom narration text here to bypass AI script generation..."
                          oninput="updateRoutePreview()"></textarea>
                <p class="text-xs text-slate-500">Leaving this blank allows the AI to automatically research and script the topic.</p>
              </div>
            </details>

            <!-- Submit Button -->
            <div class="pt-2">
              <button onclick="runPipeline()" id="btn-run-pipeline" class="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white font-bold text-base shadow-xl shadow-indigo-600/30 hover:shadow-indigo-600/50 hover:brightness-110 active:scale-[0.99] transition flex items-center justify-center gap-3">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                Launch Full Automation Pipeline
              </button>
            </div>
          </div>
        </div>

        <!-- Right Column: Live Progress & Status (1 Col) -->
        <div class="space-y-5">
          <div class="glass p-6 rounded-2xl space-y-4">
            <h3 class="text-sm font-bold text-white flex items-center justify-between">
              <span>Pipeline Live Status</span>
              <span id="job-status-badge" class="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400">Idle</span>
            </h3>

            <!-- Progress Bar -->
            <div>
              <div class="flex justify-between text-xs text-slate-400 mb-1">
                <span id="job-step-text">Ready to run</span>
                <span id="job-pct-text">0%</span>
              </div>
              <div class="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <div id="job-progress-bar" class="bg-gradient-to-r from-indigo-500 to-pink-500 h-2.5 rounded-full transition-all duration-300" style="width: 0%"></div>
              </div>
            </div>

            <!-- Live Output Terminal -->
            <div>
              <label class="block text-xs font-semibold text-slate-400 mb-1">Pipeline Console Log</label>
              <div id="job-logs-box" class="h-64 bg-slate-950 rounded-xl p-3 text-[11px] text-slate-300 overflow-y-auto space-y-1 font-mono border border-slate-800/80">
                <div class="text-slate-500">// Ready. Logs will appear here in real time...</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ─────────────────────────────────────────────────────────────
         TAB 2: MEDIA LIBRARY & VIDEO PLAYER
         ───────────────────────────────────────────────────────────── -->
    <div id="tab-library" class="hidden space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Embedded Video Player Preview (2 Cols) -->
        <div class="lg:col-span-2 glass p-6 rounded-2xl space-y-4">
          <div class="flex items-center justify-between">
            <h2 id="player-title" class="text-base font-bold text-white truncate max-w-lg">Preview Player</h2>
            <a id="player-download" href="#" download class="text-xs px-3 py-1.5 rounded-lg bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 hover:bg-indigo-600/50 transition">Download File</a>
          </div>

          <!-- Video Container -->
          <div class="w-full aspect-video bg-black rounded-xl overflow-hidden flex items-center justify-center border border-slate-800 relative">
            <video id="video-preview" controls class="w-full h-full object-contain"></video>
            <div id="audio-preview-wrap" class="hidden w-full p-8 flex flex-col items-center justify-center space-y-3">
              <div class="w-16 h-16 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
                <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/></svg>
              </div>
              <audio id="audio-preview" controls class="w-full max-w-md"></audio>
            </div>
          </div>
        </div>

        <!-- Media Assets List (1 Col) -->
        <div class="glass p-6 rounded-2xl space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-white">Generated Assets (<span id="media-count">0</span>)</h3>
            <button onclick="loadMedia()" class="text-xs text-indigo-400 hover:text-indigo-300 transition">↻ Refresh</button>
          </div>
          <div id="media-list" class="space-y-2 h-[420px] overflow-y-auto pr-1">
            <div class="text-xs text-slate-500 text-center py-8">Loading media assets...</div>
          </div>
        </div>

      </div>
    </div>

    <!-- ─────────────────────────────────────────────────────────────
         TAB 3: VOICE STUDIO PLAYGROUND
         ───────────────────────────────────────────────────────────── -->
    <div id="tab-tts" class="hidden space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Playground Synthesizer (2 Cols) -->
        <div class="lg:col-span-2 glass p-6 rounded-2xl space-y-5">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-bold text-white">VoiceStudio TTS Playground</h2>
              <p class="text-xs text-slate-400">Synthesize text on-the-fly using any VoiceStudio base engine or cloned profile.</p>
            </div>
            <span class="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Backend: Port 3900</span>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">Script Text to Synthesize</label>
            <textarea id="tts-input" rows="4" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                      placeholder="Enter any text to hear VoiceStudio speak in real time...">Hello! Welcome to OpenStudio. This audio is synthesized using VoiceStudio's base TTS engine.</textarea>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">Voice Selection</label>
              <select id="tts-voice-select" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white text-xs focus:outline-none">
                <option value="auto">🧠 Autonomous Decision</option>
                <option value="onyx">Onyx (OmniVoice Base)</option>
                <option value="alloy">Alloy (OmniVoice Base)</option>
                <option value="expr-voice-2-m">KittenTTS Male (expr-voice-2-m)</option>
                <option value="expr-voice-2-f">KittenTTS Female (expr-voice-2-f)</option>
                <option value="e50a2165">Minhaz (Cloned Voice)</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">Model Engine</label>
              <select id="tts-model-select" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white text-xs focus:outline-none">
                <option value="auto">Auto Engine</option>
                <option value="omnivoice">OmniVoice (GPU)</option>
                <option value="kittentts">KittenTTS (CPU Realtime)</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">Language</label>
              <select id="tts-lang-select" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white text-xs focus:outline-none">
                <option value="auto">Auto-Detect</option>
                <option value="en">English (en)</option>
                <option value="es">Spanish (es)</option>
                <option value="bn">Bengali (bn)</option>
                <option value="fr">French (fr)</option>
                <option value="de">German (de)</option>
              </select>
            </div>
          </div>

          <div class="flex items-center gap-4 pt-2">
            <button onclick="synthesizePlayground()" id="btn-synth" class="px-6 py-3 rounded-xl bg-indigo-600 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/></svg>
              Synthesize Speech
            </button>
            <span id="synth-status" class="text-xs text-slate-400"></span>
          </div>

          <!-- Playground Audio Player Output -->
          <div id="playground-output" class="hidden p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div class="flex items-center justify-between text-xs">
              <span id="playground-meta" class="font-semibold text-indigo-400">Generated Audio</span>
              <a id="playground-dl" href="#" download class="text-slate-400 hover:text-white transition">Download</a>
            </div>
            <audio id="playground-audio" controls class="w-full"></audio>
          </div>
        </div>

        <!-- Voice Profiles & Models Catalog (1 Col) -->
        <div class="glass p-6 rounded-2xl space-y-4">
          <h3 class="text-sm font-bold text-white">Voice Catalogue</h3>
          <div id="catalog-list" class="space-y-3 h-[420px] overflow-y-auto pr-1 text-xs">
            <div class="text-slate-500 text-center py-8">Loading catalogue...</div>
          </div>
        </div>

      </div>
    </div>

    <!-- ─────────────────────────────────────────────────────────────
         TAB 4: LOGS & MONITOR
         ───────────────────────────────────────────────────────────── -->
    <div id="tab-logs" class="hidden space-y-6">
      <div class="glass p-6 rounded-2xl space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-base font-bold text-white">System Logs Stream</h2>
            <p class="text-xs text-slate-400">Real-time automation logs from ContentAutomation/logs/automation.log</p>
          </div>
          <button onclick="loadLogs()" class="text-xs px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition">↻ Refresh Logs</button>
        </div>

        <div id="full-logs-box" class="h-[520px] bg-slate-950 rounded-xl p-4 text-xs text-slate-300 font-mono overflow-y-auto space-y-1 border border-slate-800">
          <div class="text-slate-500">Loading logs...</div>
        </div>
      </div>
    </div>

  </main>

  <footer class="mt-auto px-6 py-4 border-t border-slate-800/80 text-center text-xs text-slate-500">
    OpenStudio ContentAutomation &bull; Powered by VoiceStudio, OmniVoice, KittenTTS, FFmpeg & Remotion
  </footer>

  <script>
    let currentTab = 'studio';

    function switchTab(tab) {
      currentTab = tab;
      ['studio', 'library', 'tts', 'logs'].forEach(t => {
        document.getElementById(`tab-${t}`).classList.toggle('hidden', t !== tab);
        const btn = document.getElementById(`tab-btn-${t}`);
        if (t === tab) {
          btn.className = 'px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 bg-indigo-600 text-white shadow-md shadow-indigo-600/20';
        } else {
          btn.className = 'px-4 py-2 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition flex items-center gap-2';
        }
      });
      if (tab === 'library') loadMedia();
      if (tab === 'logs') loadLogs();
      if (tab === 'tts') loadCatalog();
    }

    function setTopic(text, lang = 'auto') {
      document.getElementById('topic-input').value = text;
      document.getElementById('lang-select').value = lang;
      updateRoutePreview();
    }

    async function checkStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        // VoiceStudio badge
        const badgeVoice = document.getElementById('badge-voice');
        if (data.voicestudio.online) {
          badgeVoice.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span><span class="font-medium text-emerald-300">VoiceStudio : Online (${data.voicestudio.voices_count} voices)</span>`;
        } else {
          badgeVoice.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-red-500"></span><span class="font-medium text-red-300">VoiceStudio : Offline</span>`;
        }

        // FFmpeg badge
        const badgeFfmpeg = document.getElementById('badge-ffmpeg');
        if (data.ffmpeg.available) {
          badgeFfmpeg.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span><span class="font-medium text-slate-300">FFmpeg v${data.ffmpeg.version}</span>`;
        } else {
          badgeFfmpeg.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span><span class="font-medium text-amber-300">FFmpeg missing</span>`;
        }

        // Remotion badge
        const badgeRemotion = document.getElementById('badge-remotion');
        if (data.remotion.ready) {
          badgeRemotion.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-indigo-500"></span><span class="font-medium text-slate-300">Remotion Ready</span>`;
        } else {
          badgeRemotion.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-slate-500"></span><span class="font-medium text-slate-400">Remotion (npx needed)</span>`;
        }

        // Update Job status
        if (data.job) {
          updateJobUI(data.job);
        }
      } catch (err) {
        console.error("Status check failed", err);
      }
    }

    let routeTimeout = null;
    function updateRoutePreview() {
      clearTimeout(routeTimeout);
      routeTimeout = setTimeout(async () => {
        const text = document.getElementById('custom-script-text').value.trim() || document.getElementById('topic-input').value.trim();
        const lang = document.getElementById('lang-select').value;
        const voice = document.getElementById('voice-select').value;

        if (!text) return;

        try {
          const res = await fetch('/api/route-preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, language: lang, voice })
          });
          const d = await res.json();
          document.getElementById('route-badge-model').innerText = `${d.model.toUpperCase()} : ${d.voice}`;
          document.getElementById('route-badge-lang').innerText = `${d.language_name} (${d.language_code})`;
          document.getElementById('route-reason').innerText = d.reason;
          document.getElementById('route-duration').innerText = `~${d.estimated_duration_seconds}s`;
        } catch (err) {
          console.error("Route preview failed", err);
        }
      }, 300);
    }

    async function runPipeline() {
      const topic = document.getElementById('topic-input').value.trim();
      if (!topic) {
        alert("Please enter a video topic!");
        return;
      }
      const platform = document.getElementById('platform-select').value;
      const language = document.getElementById('lang-select').value;
      const voice = document.getElementById('voice-select').value;
      const customScript = document.getElementById('custom-script-text').value.trim();

      const payload = {
        topic,
        platform,
        formats: [platform],
        language,
        voice,
        custom_script: customScript ? { title: topic, hook: customScript, full_narration: customScript } : null
      };

      try {
        const btn = document.getElementById('btn-run-pipeline');
        btn.disabled = true;
        btn.innerHTML = `<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Launching Pipeline...`;

        const res = await fetch('/api/pipeline/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const err = await res.json();
          alert(`Error: ${err.detail || 'Could not launch pipeline'}`);
        }
      } catch (err) {
        alert(`Error: ${err}`);
      } finally {
        setTimeout(pollJob, 500);
      }
    }

    function updateJobUI(job) {
      const badge = document.getElementById('job-status-badge');
      const stepText = document.getElementById('job-step-text');
      const pctText = document.getElementById('job-pct-text');
      const bar = document.getElementById('job-progress-bar');
      const btn = document.getElementById('btn-run-pipeline');

      if (job.status === 'running') {
        badge.className = 'px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 animate-pulse';
        badge.innerText = 'Running';
        btn.disabled = true;
      } else if (job.status === 'completed') {
        badge.className = 'px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
        badge.innerText = 'Completed';
        btn.disabled = false;
        btn.innerHTML = `Launch Full Automation Pipeline`;
      } else if (job.status === 'failed') {
        badge.className = 'px-2 py-0.5 rounded-full text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/30';
        badge.innerText = 'Failed';
        btn.disabled = false;
        btn.innerHTML = `Launch Full Automation Pipeline`;
      } else {
        badge.className = 'px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400';
        badge.innerText = 'Idle';
        btn.disabled = false;
        btn.innerHTML = `Launch Full Automation Pipeline`;
      }

      stepText.innerText = job.current_step || 'Ready';
      pctText.innerText = `${job.progress_percent}%`;
      bar.style.width = `${job.progress_percent}%`;

      const box = document.getElementById('job-logs-box');
      if (job.logs && job.logs.length) {
        box.innerHTML = job.logs.map(l => `<div class="truncate leading-relaxed">${escapeHtml(l)}</div>`).join('');
        box.scrollTop = box.scrollHeight;
      }
    }

    async function pollJob() {
      try {
        const res = await fetch('/api/pipeline/job');
        const job = await res.json();
        updateJobUI(job);
        if (job.status === 'running') {
          setTimeout(pollJob, 1500);
        } else if (job.status === 'completed') {
          loadMedia();
        }
      } catch (e) {
        console.error(e);
      }
    }

    async function loadMedia() {
      try {
        const res = await fetch('/api/media');
        const data = await res.json();
        document.getElementById('media-count').innerText = data.total;
        const list = document.getElementById('media-list');

        if (!data.media || !data.media.length) {
          list.innerHTML = `<div class="text-xs text-slate-500 text-center py-8">No generated assets found in output directory.</div>`;
          return;
        }

        list.innerHTML = data.media.map(m => {
          let icon = '📁';
          if (m.type === 'video') icon = '🎬';
          if (m.type === 'audio') icon = '🎵';
          if (m.type === 'image') icon = '🖼️';
          if (m.type === 'subtitle') icon = '📝';

          return `
            <div onclick="selectMedia('${m.name}', '${m.type}', '${m.url}')" class="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 transition cursor-pointer flex items-center justify-between">
              <div class="flex items-center gap-2.5 truncate max-w-[200px]">
                <span class="text-base">${icon}</span>
                <span class="text-xs font-semibold text-slate-200 truncate">${m.name}</span>
              </div>
              <span class="text-[10px] text-slate-500 font-mono">${m.size_mb} MB</span>
            </div>
          `;
        }).join('');

        // Auto select first video
        const firstVideo = data.media.find(m => m.type === 'video') || data.media[0];
        if (firstVideo) {
          selectMedia(firstVideo.name, firstVideo.type, firstVideo.url);
        }
      } catch (err) {
        console.error("Failed to load media", err);
      }
    }

    function selectMedia(name, type, url) {
      document.getElementById('player-title').innerText = name;
      document.getElementById('player-download').href = url;

      const video = document.getElementById('video-preview');
      const audioWrap = document.getElementById('audio-preview-wrap');
      const audio = document.getElementById('audio-preview');

      if (type === 'video') {
        video.classList.remove('hidden');
        audioWrap.classList.add('hidden');
        video.src = url;
        video.load();
      } else if (type === 'audio') {
        video.classList.add('hidden');
        audioWrap.classList.remove('hidden');
        audio.src = url;
        audio.load();
      }
    }

    async function synthesizePlayground() {
      const text = document.getElementById('tts-input').value.trim();
      if (!text) { alert("Enter text to speak"); return; }
      const voice = document.getElementById('tts-voice-select').value;
      const model = document.getElementById('tts-model-select').value;
      const language = document.getElementById('tts-lang-select').value;

      const btn = document.getElementById('btn-synth');
      const status = document.getElementById('synth-status');
      btn.disabled = true;
      status.innerText = "Synthesizing with VoiceStudio...";

      try {
        const res = await fetch('/api/synthesize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice, model, language })
        });
        const d = await res.json();
        if (!res.ok) throw new Error(d.detail || "Synthesis error");

        const outBox = document.getElementById('playground-output');
        const audio = document.getElementById('playground-audio');
        const dl = document.getElementById('playground-dl');
        const meta = document.getElementById('playground-meta');

        outBox.classList.remove('hidden');
        audio.src = d.url;
        audio.play();
        dl.href = d.url;
        meta.innerText = `Synthesized via ${d.decision.model} (${d.decision.voice}) &bull; ${d.duration.toFixed(1)}s`;
        status.innerText = "✅ Generated successfully!";
      } catch (err) {
        status.innerText = `❌ ${err.message}`;
      } finally {
        btn.disabled = false;
      }
    }

    async function loadCatalog() {
      try {
        const res = await fetch('/api/voices');
        const d = await res.json();
        const list = document.getElementById('catalog-list');
        list.innerHTML = (d.presets || []).map(p => `
          <div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-200">${p.name}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400 uppercase">${p.type}</span>
            </div>
            <p class="text-[11px] text-slate-400">${p.description}</p>
          </div>
        `).join('');
      } catch (e) {
        console.error(e);
      }
    }

    async function loadLogs() {
      try {
        const res = await fetch('/api/logs?lines=100');
        const d = await res.json();
        const box = document.getElementById('full-logs-box');
        box.innerHTML = (d.logs || []).map(l => `<div class="truncate">${escapeHtml(l)}</div>`).join('');
        box.scrollTop = box.scrollHeight;
      } catch (e) {
        console.error(e);
      }
    }

    function escapeHtml(str) {
      return (str || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Initialize on load
    window.addEventListener('DOMContentLoaded', () => {
      checkStatus();
      updateRoutePreview();
      setInterval(checkStatus, 5000);
    });
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index_page():
    return DASHBOARD_HTML


def start_server(port: int = 8080):
    print(f"\n" + "═" * 70)
    print(f"  🎬 OPENSTUDIO UNIFIED CONTENT AUTOMATION DASHBOARD")
    print(f"═" * 70)
    print(f"  🌐 Dashboard URL: http://localhost:{port}")
    print(f"  🎙️ VoiceStudio Backend: {VOICESTUDIO_BASE_URL}")
    print(f"  📁 Media Outputs: {OUTPUT_DIR}")
    print(f"═" * 70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenStudio Unified Content Automation Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind dashboard server (default: 8080)")
    args = parser.parse_args()
    start_server(port=args.port)
