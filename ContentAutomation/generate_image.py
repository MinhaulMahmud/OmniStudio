#!/usr/bin/env python3
"""
Aesthetic Image Generator
==========================
Standalone script to test and generate aesthetic AI images.

Supports:
  1. Omniroute Proxy (http://localhost:20128/v1/images/generations)
  2. Free Direct AI Engine (Pollinations Flux / SDXL - no key required)

Usage:
  python generate_image.py
  python generate_image.py --prompt "neon cyberpunk city in the rain, 8k, cinematic"
  python generate_image.py --aspect 16:9 --output "assets/backgrounds/hero.jpg"
"""
import argparse
import base64
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Add ContentAutomation to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ASSETS_DIR,
    OUTPUT_DIR,
    IMAGE_GENERATION_URL,
    OMNIROUTE_AUTH_TOKEN,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("image_gen")

DEFAULT_AESTHETIC_PROMPT = (
    "A breathtaking cinematic landscape of ethereal floating crystal islands over a calm "
    "mirror ocean at twilight, bioluminescent purple and cyan flora glowing softly, "
    "distant auroras in a deep indigo starry sky, raytraced reflections, hyper-detailed, "
    "octane render, 8k wallpaper"
)


class AestheticImageGenerator:
    """Multi-backend image generator for video backgrounds and assets."""

    def __init__(
        self,
        endpoint_url: str = IMAGE_GENERATION_URL,
        auth_token: str = OMNIROUTE_AUTH_TOKEN,
    ):
        self.endpoint_url = endpoint_url
        self.auth_token = auth_token

    def generate(
        self,
        prompt: str,
        output_path: Path,
        width: int = 1024,
        height: int = 1024,
        seed: int = None,
    ) -> Path:
        """
        Generate an image and save it to output_path.
        Tries Omniroute proxy first, then falls back to the direct free AI engine.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("🎨 Generating image with prompt:\n   \"%s\"", prompt[:100] + ("..." if len(prompt) > 100 else ""))
        logger.info("📐 Target dimensions: %dx%d", width, height)

        # 1. Try Omniroute Proxy if reachable
        omniroute_success = self._try_omniroute(prompt, output_path, width, height)
        if omniroute_success:
            return output_path

        # 2. Fall back to Direct Free AI Engine (Pollinations Flux / SDXL)
        logger.info("🌐 Using Direct AI Generation Engine (Flux / SDXL)...")
        self._generate_direct(prompt, output_path, width, height, seed=seed)
        return output_path

    def _try_omniroute(
        self, prompt: str, output_path: Path, width: int, height: int
    ) -> bool:
        """Attempt image generation via Omniroute endpoint."""
        if not self.endpoint_url:
            return False

        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "x-api-key": self.auth_token,
            "Content-Type": "application/json",
        }

        # Try supported image models
        candidate_models = ["flux", "pollinations/flux", "sdxl", "dall-e-3"]
        for model in candidate_models:
            payload = json.dumps({
                "prompt": prompt,
                "model": model,
                "size": f"{width}x{height}",
                "n": 1,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.endpoint_url,
                data=payload,
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8", errors="replace"))
                        items = data.get("data", [])
                        if items:
                            first = items[0]
                            if "b64_json" in first:
                                with open(output_path, "wb") as f:
                                    f.write(base64.b64decode(first["b64_json"]))
                                logger.info("✅ Image received from Omniroute (%s)", model)
                                return True
                            elif "url" in first:
                                urllib.request.urlretrieve(first["url"], str(output_path))
                                logger.info("✅ Image downloaded from Omniroute (%s)", model)
                                return True
            except urllib.error.HTTPError as exc:
                err = exc.read().decode("utf-8", errors="replace")
                logger.debug("Omniroute model %s returned: %s", model, err[:150])
            except Exception as exc:
                logger.debug("Omniroute attempt failed: %s", exc)

        return False

    def _generate_direct(
        self,
        prompt: str,
        output_path: Path,
        width: int,
        height: int,
        seed: int = None,
    ):
        """Generate high-quality image using direct AI engine (Flux)."""
        encoded_prompt = urllib.parse.quote(prompt)
        seed_param = f"&seed={seed}" if seed else f"&seed={int(time.time()) % 100000}"
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&nologo=true&enhance=true{seed_param}"
        )

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
                with open(output_path, "wb") as f:
                    f.write(data)
                logger.info("✅ Image saved: %s (%.1f KB)", output_path.name, len(data) / 1024)
        except Exception as exc:
            logger.error("Direct AI generation error: %s", exc)
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Aesthetic Image Generator for Video Backgrounds & Thumbnails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_AESTHETIC_PROMPT,
        help="Custom image generation prompt",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Destination path for the image (defaults to output/aesthetic_image.jpg)",
    )
    parser.add_argument(
        "--aspect",
        choices=["1:1", "16:9", "9:16"],
        default="16:9",
        help="Aspect ratio: 16:9 (YouTube), 9:16 (Shorts/TikTok), 1:1 (Square)",
    )
    parser.add_argument(
        "--copy-to-backgrounds",
        action="store_true",
        default=True,
        help="Also copy to assets/backgrounds for automatic video pipeline use",
    )
    args = parser.parse_args()

    # Determine resolution from aspect ratio
    resolutions = {
        "1:1": (1024, 1024),
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
    }
    width, height = resolutions.get(args.aspect, (1920, 1080))

    out_file = args.output or (
        OUTPUT_DIR / f"aesthetic_image_{int(time.time())}.jpg"
    )

    print("\n" + "═" * 70)
    print("  🎨 AESTHETIC AI IMAGE GENERATOR")
    print("═" * 70)

    gen = AestheticImageGenerator()
    result_path = gen.generate(
        prompt=args.prompt,
        output_path=out_file,
        width=width,
        height=height,
    )

    # Copy to backgrounds directory so the video pipeline can pick it up
    if args.copy_to_backgrounds:
        bg_dest = ASSETS_DIR / "backgrounds" / f"bg_{result_path.name}"
        import shutil
        shutil.copy2(str(result_path), str(bg_dest))
        print(f"  📁 Background asset added: {bg_dest}")

    # Inspect with Pillow
    try:
        from PIL import Image
        with Image.open(result_path) as img:
            fmt, size, mode = img.format, img.size, img.mode
            print(f"  🖼️  Image Specs: {size[0]}x{size[1]} | Format: {fmt} | Mode: {mode}")
    except Exception:
        pass

    print(f"\n  ✅ Successfully generated: {result_path}")
    print(f"     Size: {result_path.stat().st_size / 1024:.1f} KB")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
