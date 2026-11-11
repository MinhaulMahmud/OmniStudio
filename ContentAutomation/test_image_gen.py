"""
Test Image Generation Script
=============================
Tests the image generation endpoint at http://localhost:20128/v1/images/generations
with an aesthetic prompt and saves the output to assets/backgrounds/
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

URL = os.getenv("IMAGE_GENERATION_URL", "http://localhost:20128/v1/images/generations")
AUTH_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN", "omniroute")

AESTHETIC_PROMPT = (
    "A stunning cyberpunk floating bonsai island glowing with iridescent neon violet and "
    "cyan lights, starry cosmic nebula background, reflections on dark water, cinematic, "
    "hyperrealistic, intricate detail, octane render, 8k"
)

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "x-api-key": AUTH_TOKEN,
    "Content-Type": "application/json",
}

print(f"Target URL: {URL}")
print(f"Auth Token: {AUTH_TOKEN}")
print(f"Prompt: {AESTHETIC_PROMPT}\n")

# Variations of model & format
candidates = [
    {"prompt": AESTHETIC_PROMPT, "model": "dall-e-3", "size": "1024x1024", "n": 1},
    {"prompt": AESTHETIC_PROMPT, "model": "auto/best-free", "size": "1024x1024", "n": 1},
    {"prompt": AESTHETIC_PROMPT, "model": "flux", "size": "1024x1024", "n": 1},
    {"prompt": AESTHETIC_PROMPT, "model": "sdxl", "size": "1024x1024", "n": 1},
    {"prompt": AESTHETIC_PROMPT, "size": "1024x1024", "n": 1},
    {"prompt": AESTHETIC_PROMPT, "n": 1},
    {"prompt": AESTHETIC_PROMPT},
]

success = False
for idx, payload in enumerate(candidates, 1):
    model_name = payload.get("model", "None")
    print(f"[{idx}/{len(candidates)}] Trying model: {model_name} ...")
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=HEADERS,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            print(f"  --> HTTP {resp.status} OK!")
            raw = resp.read()
            data = json.loads(raw.decode("utf-8", errors="replace"))
            print("  --> Response keys:", list(data.keys()))

            items = data.get("data", [])
            if not items:
                print("  --> Response JSON:", data)
                continue

            first = items[0]
            out_img = OUTPUT_DIR / f"aesthetic_cyberpunk_bonsai_{idx}.png"

            # Check if base64 encoded
            if "b64_json" in first:
                b64 = first["b64_json"]
                with open(out_img, "wb") as f:
                    f.write(base64.b64decode(b64))
                print(f"\nSUCCESS! Image saved to: {out_img} ({out_img.stat().st_size} bytes)")
                success = True
                break

            # Check if URL
            elif "url" in first:
                img_url = first["url"]
                print(f"  --> Downloading from URL: {img_url[:60]}...")
                urllib.request.urlretrieve(img_url, str(out_img))
                print(f"\nSUCCESS! Image downloaded to: {out_img} ({out_img.stat().st_size} bytes)")
                success = True
                break
            else:
                print("  --> Unexpected data item format:", first)

    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        print(f"  --> HTTP {exc.code} Error: {err_body[:300]}")
    except Exception as exc:
        print(f"  --> Error: {exc}")

if not success:
    print("\nAttempting to query /v1/models or related routes to see available image models...")
    for route in ["/v1/models", "/models"]:
        try:
            req = urllib.request.Request(
                f"http://localhost:20128{route}",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}", "x-api-key": AUTH_TOKEN},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"Route {route} -> HTTP {resp.status}:")
                m_data = json.loads(resp.read())
                for m in m_data.get("data", [])[:15]:
                    print("   -", m.get("id"))
        except Exception as e:
            print(f"Route {route} -> {e}")
