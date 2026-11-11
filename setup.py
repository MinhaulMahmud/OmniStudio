#!/usr/bin/env python3
"""
OmniStudio Setup Wizard & Environment Diagnostic
================================================
Automated setup and validation for OmniStudio.

Usage:
  python setup.py                # Interactive setup wizard
  python setup.py --check        # Run diagnostics only (no writes/installs)
  python setup.py --non-interactive  # Automated setup using existing env vars
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
CONTENT_AUTOMATION_DIR = ROOT_DIR / "ContentAutomation"
REMOTION_DIR = CONTENT_AUTOMATION_DIR / "remotion"
ENV_FILE = CONTENT_AUTOMATION_DIR / ".env"
REQUIREMENTS_FILE = CONTENT_AUTOMATION_DIR / "requirements.txt"


def mask_secret(secret: str) -> str:
    """Mask secret key showing only first 6 and last 4 chars."""
    if not secret:
        return "[NOT SET]"
    if len(secret) <= 10:
        return "*" * len(secret)
    return secret[:6] + "*" * (len(secret) - 10) + secret[-4:]


def check_python_version() -> bool:
    v = sys.version_info
    print(f"[*] Python Version: {v.major}.{v.minor}.{v.micro}", end="")
    if v.major > 3 or (v.major == 3 and v.minor >= 10):
        print(" -> [OK]")
        return True
    print(" -> [FAIL] (Python >= 3.10 required)")
    return False


def find_node() -> str | None:
    # Check PATH first
    node_bin = shutil.which("node")
    if node_bin:
        return node_bin
    # Fallback to local python playwright driver node if available on Windows
    local_driver = Path(r"C:\Users\MSI\AppData\Roaming\Python\Python313\site-packages\playwright\driver\node.exe")
    if local_driver.exists():
        return str(local_driver)
    return None


def find_npm() -> str | None:
    npm_bin = shutil.which("npm")
    if npm_bin:
        return npm_bin
    node = find_node()
    if node:
        npm_candidate = Path(node).parent / ("npm.cmd" if platform.system() == "Windows" else "npm")
        if npm_candidate.exists():
            return str(npm_candidate)
    return None


def find_npx() -> str | None:
    npx_bin = shutil.which("npx")
    if npx_bin:
        return npx_bin
    node = find_node()
    if node:
        npx_candidate = Path(node).parent / ("npx.cmd" if platform.system() == "Windows" else "npx")
        if npx_candidate.exists():
            return str(npx_candidate)
    return None


def check_node_version() -> tuple[bool, str | None]:
    node = find_node()
    if not node:
        print("[*] Node.js: [FAIL] (node not found in PATH)")
        return False, None
    try:
        res = subprocess.run([node, "-v"], capture_output=True, text=True, timeout=5)
        v_str = res.stdout.strip()
        print(f"[*] Node.js Version: {v_str} ({node}) -> [OK]")
        return True, node
    except Exception as e:
        print(f"[*] Node.js: [FAIL] ({e})")
        return False, None


def check_chrome_headless_shell() -> bool:
    system = platform.system()
    binary_name = "chrome-headless-shell.exe" if system == "Windows" else "chrome-headless-shell"

    # Search in remotion node_modules/.remotion
    remotion_cache = REMOTION_DIR / "node_modules" / ".remotion"
    found = list(remotion_cache.glob(f"**/{binary_name}")) if remotion_cache.exists() else []

    if found:
        print(f"[*] Chrome Headless Shell: {found[0]} -> [OK]")
        return True

    # Search PATH
    in_path = shutil.which(binary_name)
    if in_path:
        print(f"[*] Chrome Headless Shell: {in_path} -> [OK]")
        return True

    print(f"[*] Chrome Headless Shell: [WARN] (Not found, run `npx remotion browser ensure` inside ContentAutomation/remotion)")
    return False


def load_env_dict() -> dict[str, str]:
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


def run_diagnostics() -> bool:
    print("\n" + "=" * 60)
    print("  OmniStudio System Diagnostics")
    print("=" * 60)

    all_good = True
    if not check_python_version():
        all_good = False

    node_ok, _ = check_node_version()
    if not node_ok:
        all_good = False

    remotion_modules = REMOTION_DIR / "node_modules"
    if remotion_modules.exists() and (remotion_modules / "remotion").exists():
        print(f"[*] Remotion node_modules: {remotion_modules} -> [OK]")
    else:
        print(f"[*] Remotion node_modules: [FAIL] (Run npm install in {REMOTION_DIR})")
        all_good = False

    check_chrome_headless_shell()

    # Check .env
    env_vars = load_env_dict()
    key = env_vars.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
    voice_url = env_vars.get("VOICESTUDIO_URL", "http://localhost:3900")
    model = env_vars.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

    print(f"[*] OPENROUTER_API_KEY: {mask_secret(key)}", end="")
    if key and not key.startswith("your_"):
        print(" -> [OK]")
    else:
        print(" -> [WARN] (Key missing or placeholder)")
        all_good = False

    print(f"[*] OPENROUTER_MODEL: {model} -> [OK]")
    print(f"[*] VOICESTUDIO_URL: {voice_url} -> [OK]")

    skills_file = CONTENT_AUTOMATION_DIR / "skills" / "remotion" / "SKILLS_VERSION"
    if skills_file.exists():
        v = skills_file.read_text(encoding="utf-8").strip()
        print(f"[*] Remotion Skills Version: {v[:10]}... -> [OK]")
    else:
        print("[*] Remotion Skills Version: [WARN] (skills/remotion/SKILLS_VERSION not found)")

    print("=" * 60)
    if all_good:
        print("  All primary dependencies are satisfied.\n")
    else:
        print("  Some dependencies or configurations need attention.\n")
    return all_good


def run_setup(non_interactive: bool = False):
    print("\n" + "=" * 60)
    print("  OmniStudio Setup Wizard")
    print("=" * 60 + "\n")

    if not check_python_version():
        print("[!] Incompatible Python version. Please use Python 3.10+.")
        if not non_interactive:
            sys.exit(1)

    # 1. Install python dependencies if requirements.txt exists
    if REQUIREMENTS_FILE.exists():
        print("[*] Checking Python dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS_FILE)], check=True)
            print("[+] Python requirements installed -> [OK]")
        except Exception as e:
            print(f"[!] Warning: pip install returned: {e}")

    # 2. Check Node & npm install
    node_ok, _ = check_node_version()
    if node_ok:
        remotion_modules = REMOTION_DIR / "node_modules"
        if not remotion_modules.exists() or not (remotion_modules / "remotion").exists():
            npm = find_npm()
            if npm:
                print(f"[*] Installing Remotion npm dependencies in {REMOTION_DIR}...")
                try:
                    subprocess.run([npm, "install"], cwd=str(REMOTION_DIR), check=True)
                    print("[+] Remotion packages installed successfully -> [OK]")
                except Exception as e:
                    print(f"[!] Warning: npm install failed: {e}")

        # Ensure chrome headless shell
        npx = find_npx()
        if npx:
            print("[*] Ensuring Chrome Headless Shell...")
            try:
                subprocess.run([npx, "remotion", "browser", "ensure"], cwd=str(REMOTION_DIR), timeout=45)
            except Exception:
                pass

    # 3. Configure .env
    current_env = load_env_dict()
    default_key = current_env.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
    default_voice_url = current_env.get("VOICESTUDIO_URL", "http://localhost:3900")
    default_voice = current_env.get("DEFAULT_VOICE", "kitten")
    default_model = "meta-llama/llama-3.3-70b-instruct"

    api_key = default_key
    voice_url = default_voice_url
    voice_choice = default_voice

    if not non_interactive:
        print("\n--- Configuration Settings ---")
        prompt_key = input(f"Enter OpenRouter API Key [{mask_secret(default_key)}]: ").strip()
        if prompt_key:
            api_key = prompt_key

        prompt_url = input(f"Enter VoiceStudio URL [{default_voice_url}]: ").strip()
        if prompt_url:
            voice_url = prompt_url

        prompt_voice = input(f"Enter Default Voice Engine (kitten/omnico) [{default_voice}]: ").strip()
        if prompt_voice:
            voice_choice = prompt_voice

    # Write .env
    env_content = f"""# OmniStudio Generated Environment Configuration
OPENROUTER_API_KEY={api_key}
OPENROUTER_MODEL={default_model}
VOICESTUDIO_URL={voice_url}
DEFAULT_VOICE={voice_choice}
VOICE_MODEL=expr-voice-2-m
TTS_PROVIDER=kitten
"""
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(env_content, encoding="utf-8")
    print(f"\n[+] Configuration saved to {ENV_FILE}")

    run_diagnostics()


def main():
    parser = argparse.ArgumentParser(description="OmniStudio Setup Wizard & Diagnostics")
    parser.add_argument("--check", action="store_true", help="Run diagnostics check only")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive setup using env vars")
    args = parser.parse_args()

    if args.check:
        success = run_diagnostics()
        sys.exit(0 if success else 1)
    else:
        run_setup(non_interactive=args.non_interactive)


if __name__ == "__main__":
    main()
