"""
Orchestrator to generate VoiceStudio cloned voiceover ("Minhaz" - ID: e50a2165),
verify each chunk, stitch them seamlessly with FFmpeg, and update both
Remotion and FFmpeg compositions.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Add ContentAutomation to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    VOICESTUDIO_BASE_URL,
    CLONED_VOICE_ID,
    CLONED_VOICE_NAME,
    OUTPUT_DIR,
    FFMPEG_PATH,
    SHORT_WIDTH,
    SHORT_HEIGHT,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
)
from voice_client import VoiceStudioClient
from subtitle_generator import SubtitleGenerator, SubtitleChunk
from video_composer import VideoComposer
from autonomous_voice_router import AutonomousVoiceRouter, RoutingDecision

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("model_weights_generator")

# The 6 scene sections (3-4 sentences max per chunk for stability)
SECTIONS = [
    {
        "id": "scene1_hook",
        "scene_name": "TitleScene",
        "title": "Hook & Title",
        "text": "Ever wondered why running an AI model like Llama 70B makes your GPU scream, while a 7B model runs effortlessly on a laptop? It all comes down to model weights.",
    },
    {
        "id": "scene2_weights",
        "scene_name": "WeightsMatrixScene",
        "title": "What Are Weights?",
        "text": "In modern AI, weights are the learned numerical parameters stored in memory that determine how neural activations flow. A 7-billion parameter model literally holds seven billion distinct floating point numbers.",
    },
    {
        "id": "scene3_memory",
        "scene_name": "MemoryEquationScene",
        "title": "The Memory Equation",
        "text": "Here is the exact formula. At standard 16-bit precision, every single parameter requires two bytes of storage. That means a 70-billion parameter model demands a staggering 140 gigabytes of ultra-fast VRAM just to load the weights into GPU memory.",
    },
    {
        "id": "scene4_bandwidth",
        "scene_name": "BandwidthScene",
        "title": "The Bandwidth Bottleneck",
        "text": "During inference, text generation is strictly memory-bandwidth bound. For every single token generated, the GPU must stream every active weight from VRAM into the compute cores. More weights mean more gigabytes transferred per second.",
    },
    {
        "id": "scene5_quantization",
        "scene_name": "QuantizationScene",
        "title": "Quantization Magic",
        "text": "This is why quantization is revolutionary. By compressing weights from 16-bit down to 4-bit, we slash memory requirements by four times, enabling massive models to run on consumer hardware with virtually zero loss in intelligence.",
    },
    {
        "id": "scene6_outro",
        "scene_name": "OutroScene",
        "title": "Outro & Takeaways",
        "text": "Now you know: model weight size and precision directly dictate your compute costs. Follow for more deep-dive AI engineering breakdowns!",
    },
]


def update_remotion_composition(scene_timings: list[dict], total_frames: int):
    """Update ModelWeightsComposition.tsx and Root.tsx with exact audio frame boundaries."""
    remotion_dir = BASE_DIR / "remotion"
    comp_file = remotion_dir / "src" / "ModelWeightsComposition.tsx"
    root_file = remotion_dir / "src" / "Root.tsx"

    if not comp_file.exists() or not root_file.exists():
        logger.warning("Remotion files not found. Skipping Remotion code update.")
        return

    # Build sequences JSX
    sequences_jsx = []
    for st in scene_timings:
        scene_name = st["scene_name"]
        start_frame = st["start_frame"]
        duration_frames = st["duration_frames"]
        title = st["title"]
        sequences_jsx.append(f"""      {{/* {title} (frame {start_frame} -> {start_frame + duration_frames}) */}}
      <Sequence from={{{start_frame}}} durationInFrames={{{duration_frames}}}>
        <{scene_name} />
      </Sequence>""")

    comp_content = f"""import React from "react";
import {{ Audio, Sequence, staticFile }} from "remotion";
import {{ TitleScene }} from "./scenes/TitleScene";
import {{ WeightsMatrixScene }} from "./scenes/WeightsMatrixScene";
import {{ MemoryEquationScene }} from "./scenes/MemoryEquationScene";
import {{ BandwidthScene }} from "./scenes/BandwidthScene";
import {{ QuantizationScene }} from "./scenes/QuantizationScene";
import {{ OutroScene }} from "./scenes/OutroScene";

export interface CompositionProps {{
  audioSrc?: string;
}}

export const ModelWeightsComposition: React.FC<CompositionProps> = () => {{
  return (
    <div style={{{{ flex: 1, backgroundColor: "#000000", position: "relative" }}}}>
      {{/* Background Audio Narration synthesized via VoiceStudio Base TTS */}}
      <Audio src={{staticFile("narration.mp3")}} />

{chr(10).join(sequences_jsx)}
    </div>
  );
}};
"""
    comp_file.write_text(comp_content, encoding="utf-8")
    logger.info("✅ Updated Remotion composition: %s", comp_file)

    root_content = f"""import React from "react";
import {{ Composition }} from "remotion";
import {{ ModelWeightsComposition }} from "./ModelWeightsComposition";

export const Root: React.FC = () => {{
  return (
    <>
      {{/* 16:9 YouTube / Desktop Full HD Composition */}}
      <Composition
        id="ModelWeightsExplainer"
        component={{ModelWeightsComposition}}
        durationInFrames={{{total_frames}}} // Exactly matched to VoiceStudio narration
        fps={{30}}
        width={{1920}}
        height={{1080}}
        defaultProps={{{{
          audioSrc: undefined,
        }}}}
      />
    </>
  );
}};
"""
    root_file.write_text(root_content, encoding="utf-8")
    logger.info("✅ Updated Remotion root: %s (Total frames: %d)", root_file, total_frames)


def main():
    parser = argparse.ArgumentParser(description="Generate voiceover using autonomous routing or explicit TTS model")
    parser.add_argument("--voice", default="auto", help="Voice profile ID or preset (default: auto; e.g. onyx, expr-voice-2-m, alloy)")
    parser.add_argument("--model", default="auto", help="TTS Engine ID (default: auto; e.g. omnivoice, kittentts)")
    parser.add_argument("--language", "--lang", default="auto", help="Language code or auto (default: auto; e.g. en, es, bn, fr)")
    args = parser.parse_args()

    full_text = " ".join(sec["text"] for sec in SECTIONS)
    decision = AutonomousVoiceRouter.route_voice(
        text=full_text,
        requested_language=args.language if args.language != "auto" else None,
        requested_voice=args.voice if args.voice != "auto" else None,
        requested_model=args.model if args.model != "auto" else None,
    )

    voice_target = decision.voice
    model_target = decision.model
    lang_target = decision.language_code

    logger.info("=" * 70)
    logger.info("🧠 AUTONOMOUS VOICE ROUTER DECISION:")
    logger.info("   • Language: %s (%s)", decision.language_name, decision.language_code)
    logger.info("   • Estimated Duration: %.1fs (%s)", decision.estimated_duration_seconds, "> 2 min" if decision.is_long_form else "<= 2 min")
    logger.info("   • Selected Model: %s", decision.model)
    logger.info("   • Selected Voice: %s", decision.voice)
    logger.info("   • Strategy Reason: %s", decision.reason)
    logger.info("=" * 70)

    client = VoiceStudioClient()
    is_live = client.is_running()
    if not is_live:
        logger.warning("⚠️ VoiceStudio backend not reachable at %s. Will reuse existing verified chunks if present.", VOICESTUDIO_BASE_URL)

    # 1. Resolve Voice Profile
    vid = client.get_voice_id(voice_id=voice_target, voice_name=voice_target) or voice_target
    logger.info("✅ Target Voice: %s (ID: %s)", voice_target, vid)

    # 2. Synthesize each chunk
    chunk_dir = OUTPUT_DIR / f"tts_{model_target}_{voice_target}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    pause_sec = 0.25

    silence_wav = chunk_dir / "pause.wav"
    subprocess.run([
        FFMPEG_PATH, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(pause_sec), str(silence_wav)
    ], capture_output=True, check=True)

    chunk_results: list[dict] = []
    accumulated_seconds = 0.0
    current_frame = 0

    for i, sec in enumerate(SECTIONS):
        sec_id = sec["id"]
        sec_text = sec["text"]
        out_wav = chunk_dir / f"{i:02d}_{sec_id}.wav"

        logger.info("\n🎙️ [%d/%d] Chunk '%s' (%d words)...", i + 1, len(SECTIONS), sec["title"], len(sec_text.split()))
        logger.info("   Script: \"%s\"", sec_text)

        duration = client.verify_audio(out_wav)
        if out_wav.exists() and duration > 0.5:
            logger.info("   ⚡ Found existing verified chunk: %s (%.2fs)", out_wav.name, duration)
        else:
            if not is_live:
                raise RuntimeError(f"VoiceStudio is not running and chunk {out_wav.name} does not exist.")
            saved = client.synthesize_single_chunk(
                text=sec_text,
                output_path=out_wav,
                voice_id=vid,
                voice_name=voice_target,
                model=model_target,
                language=lang_target,
                audio_format="wav",
                speed=1.0,
                max_retries=3,
            )
            if not saved or not out_wav.exists():
                raise RuntimeError(f"Failed to synthesize chunk {i} ({sec['title']})")

            duration = client.verify_audio(out_wav)
            if duration <= 0.2:
                raise RuntimeError(f"Chunk {i} audio duration too short: {duration}s")

        start_sec = accumulated_seconds
        end_sec = start_sec + duration
        duration_frames = int(round((duration + pause_sec) * 30))

        chunk_info = {
            "index": i,
            "id": sec_id,
            "title": sec["title"],
            "scene_name": sec["scene_name"],
            "text": sec_text,
            "wav_path": out_wav,
            "duration": duration,
            "start_time": start_sec,
            "end_time": end_sec,
            "start_frame": current_frame,
            "duration_frames": duration_frames,
        }
        current_frame += duration_frames
        chunk_results.append(chunk_info)
        logger.info("   ✅ Chunk %d OK: %.2fs (frames %d to %d)",
                    i + 1, duration, chunk_info["start_frame"],
                    chunk_info["start_frame"] + chunk_info["duration_frames"])

        accumulated_seconds = end_sec + pause_sec

    # 3. Concatenate all chunks seamlessly with FFmpeg
    final_mp3 = OUTPUT_DIR / "narration_minhaz_model_weights.mp3"
    final_wav = OUTPUT_DIR / "narration_minhaz_model_weights.wav"
    remotion_public_mp3 = BASE_DIR / "remotion" / "public" / "narration.mp3"
    remotion_public_mp3.parent.mkdir(parents=True, exist_ok=True)

    logger.info("\n🔗 Concatenating %d chunks into final narration files...", len(chunk_results))

    ffmpeg_inputs = []
    filter_converts = []
    concat_inputs = []
    inp_idx = 0
    for idx, c in enumerate(chunk_results):
        ffmpeg_inputs.extend(["-i", str(c["wav_path"])])
        filter_converts.append(f"[{inp_idx}:a]aformat=sample_rates=24000:channel_layouts=mono[a{inp_idx}];")
        concat_inputs.append(f"[a{inp_idx}]")
        inp_idx += 1
        if idx < len(chunk_results) - 1 and pause_sec > 0:
            ffmpeg_inputs.extend(["-i", str(silence_wav)])
            filter_converts.append(f"[{inp_idx}:a]aformat=sample_rates=24000:channel_layouts=mono[a{inp_idx}];")
            concat_inputs.append(f"[a{inp_idx}]")
            inp_idx += 1

    filter_str = "".join(filter_converts) + "".join(concat_inputs) + f"concat=n={inp_idx}:v=0:a=1[outa]"

    # Output MP3
    cmd_mp3 = [
        FFMPEG_PATH, "-y", *ffmpeg_inputs,
        "-filter_complex", filter_str,
        "-map", "[outa]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(final_mp3)
    ]
    res_mp3 = subprocess.run(cmd_mp3, capture_output=True, text=True)
    if res_mp3.returncode != 0:
        raise RuntimeError(f"FFmpeg MP3 concat failed: {res_mp3.stderr}")

    # Output WAV
    cmd_wav = [
        FFMPEG_PATH, "-y", *ffmpeg_inputs,
        "-filter_complex", filter_str,
        "-map", "[outa]",
        "-c:a", "pcm_s16le",
        str(final_wav)
    ]
    subprocess.run(cmd_wav, capture_output=True, check=True)

    # Sync to Remotion public path
    shutil.copy2(final_mp3, remotion_public_mp3)

    total_duration = client.verify_audio(final_mp3)
    total_frames = int(round(total_duration * 30)) + 30  # 1s buffer for clean fade

    # Make the last scene extend seamlessly to total composition frames
    if chunk_results:
        chunk_results[-1]["duration_frames"] = total_frames - chunk_results[-1]["start_frame"]

    logger.info("🎉 Final Narration stitched successfully!")
    logger.info("   Total Duration: %.2fs (~%.1f min)", total_duration, total_duration / 60)
    logger.info("   MP3 Path: %s (%.1f KB)", final_mp3, final_mp3.stat().st_size / 1024)
    logger.info("   Remotion Audio: %s", remotion_public_mp3)

    # 4. Update Remotion scenes and root
    update_remotion_composition(chunk_results, total_frames)

    # 5. Generate Chunk-Aligned Subtitles (never bleed across scene boundaries)
    logger.info("\n📝 Generating Chunk-Aligned Subtitles...")
    sub_gen = SubtitleGenerator(words_per_chunk=4)
    all_sub_chunks: list[SubtitleChunk] = []
    sub_counter = 1

    for c in chunk_results:
        c_duration_ms = int(c["duration"] * 1000)
        c_start_ms = int(c["start_time"] * 1000)
        sec_subtitles = sub_gen.generate(c["text"], c_duration_ms)
        for s in sec_subtitles:
            all_sub_chunks.append(SubtitleChunk(
                index=sub_counter,
                start_ms=c_start_ms + s.start_ms,
                end_ms=min(c_start_ms + s.end_ms, c_start_ms + c_duration_ms),
                text=s.text,
            ))
            sub_counter += 1

    srt_path = OUTPUT_DIR / "remotion_model_weights_explainer.srt"
    ass_path = OUTPUT_DIR / "model_weights_shorts_9x16.ass"
    sub_gen.save(all_sub_chunks, srt_path, fmt="srt")
    sub_gen.save(all_sub_chunks, ass_path, fmt="ass", style="reels")
    logger.info("   ✅ Saved SRT: %s (%d subtitles)", srt_path, len(all_sub_chunks))
    logger.info("   ✅ Saved ASS: %s (%d subtitles)", ass_path, len(all_sub_chunks))

    # 6. Compose Video using FFmpeg
    logger.info("\n🎬 Composing FFmpeg Videos...")
    composer = VideoComposer()

    # Find aesthetic background image if exists
    bg_candidates = list(OUTPUT_DIR.glob("aesthetic_*.jpg")) + list(OUTPUT_DIR.glob("image_*.jpg"))
    bg_path = bg_candidates[0] if bg_candidates else None

    # Compose 9:16 Shorts
    shorts_out = OUTPUT_DIR / "model_weights_shorts_9x16.mp4"
    logger.info("   Composing Shorts 9:16: %s...", shorts_out.name)
    composer.compose(
        audio_path=final_mp3,
        output_path=shorts_out,
        title="How AI Model Weights Determine Compute Power",
        subtitle_chunks=all_sub_chunks,
        background_path=bg_path,
        format_name="shorts",
    )

    # Compose 16:9 YouTube
    youtube_out = OUTPUT_DIR / "model_weights_youtube_16x9.mp4"
    logger.info("   Composing YouTube 16:9: %s...", youtube_out.name)
    composer.compose(
        audio_path=final_mp3,
        output_path=youtube_out,
        title="How AI Model Weights Determine Compute Power",
        subtitle_chunks=all_sub_chunks,
        background_path=bg_path,
        format_name="youtube",
    )

    # 7. Render Remotion
    remotion_out = OUTPUT_DIR / "remotion_model_weights_explainer.mp4"
    logger.info("\n🎬 Attempting Remotion Video Render: %s...", remotion_out.name)
    try:
        playwright_node_dir = r"C:\Users\MSI\AppData\Roaming\Python\Python313\site-packages\playwright\driver"
        env = os.environ.copy()
        if os.path.isdir(playwright_node_dir) and playwright_node_dir not in env.get("PATH", ""):
            env["PATH"] = playwright_node_dir + os.path.pathsep + env.get("PATH", "")

        npx = shutil.which("npx", path=env["PATH"]) or shutil.which("npx.cmd", path=env["PATH"])
        if npx:
            cmd = [
                npx, "remotion", "render",
                "src/index.ts", "ModelWeightsExplainer",
                str(remotion_out),
                "--codec", "h264",
                "--overwrite",
            ]
            logger.info("Running: %s", " ".join(cmd))
            r_res = subprocess.run(cmd, cwd=str(BASE_DIR / "remotion"), env=env, capture_output=True, text=True, timeout=900)
            if r_res.returncode == 0:
                logger.info("✅ Remotion video successfully rendered: %s (%.1f MB)",
                            remotion_out, remotion_out.stat().st_size / 1024 / 1024)
            else:
                logger.warning("Remotion render returned code %d:\n%s", r_res.returncode, r_res.stderr[-500:])
        else:
            logger.info("npx not found in current PATH. FFmpeg videos were composed directly.")
    except Exception as exc:
        logger.warning("Remotion render exception: %s", exc)

    logger.info("\n" + "=" * 70)
    logger.info("🎉 ALL PIPELINE TASKS COMPLETED SUCCESSFULLY!")
    logger.info("=" * 70)
    logger.info("Outputs:")
    logger.info("  1. Final Audio: %s (%.2fs)", final_mp3, total_duration)
    logger.info("  2. Remotion Audio: %s", remotion_public_mp3)
    logger.info("  3. Shorts Video (9:16): %s", shorts_out)
    logger.info("  4. YouTube Video (16:9): %s", youtube_out)
    if remotion_out.exists():
        logger.info("  5. Remotion Video: %s", remotion_out)
    logger.info("  6. Subtitles: %s & %s", srt_path, ass_path)
    logger.info("=" * 70)
    logger.info("  1. Final Audio: %s (%.2fs)", final_mp3, total_duration)
    logger.info("  2. Remotion Audio: %s", remotion_public_mp3)
    logger.info("  3. Shorts Video (9:16): %s", shorts_out)
    logger.info("  4. YouTube Video (16:9): %s", youtube_out)
    if remotion_out.exists():
        logger.info("  5. Remotion Video: %s", remotion_out)
    logger.info("  6. Subtitles: %s & %s", srt_path, ass_path)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
