"""Pre-download and cache model weights and tokenizers into HF_HOME."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from indicvoice.config import load_config


def download_models(check_only: bool = False) -> None:
    """Download IndicTrans2 and Indic Parler-TTS into persistent cache."""
    config = load_config(base_dir=ROOT_DIR)
    hf_token = config.settings.hf_token or os.getenv("HF_TOKEN")
    hf_home = config.settings.hf_home or os.getenv("HF_HOME", "./.hf_cache")

    cache_dir = (ROOT_DIR / hf_home).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_dir)

    print("=" * 60)
    print(" IndicVoice - Model Pre-Download Tool")
    print("=" * 60)
    print(f"HF_HOME directory: {cache_dir}")
    print(f"HF_TOKEN detected: {'Yes' if hf_token else 'No (set HF_TOKEN in .env for gated models)'}")
    print(f"Translation Model: {config.settings.translation_model_id}")
    print(f"TTS Model:         {config.settings.tts_model_id}")
    print("-" * 60)

    if check_only:
        print("Check completed. Exiting.")
        return

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Error: huggingface_hub is not installed. Run 'pip install huggingface-hub'.")
        sys.exit(1)

    # 1. Download Translation Model
    mt_id = config.settings.translation_model_id
    print(f"\n[1/2] Downloading Translation model ({mt_id})...")
    try:
        path = snapshot_download(
            repo_id=mt_id,
            token=hf_token,
            local_files_only=False,
        )
        print(f"  ✓ Translation model cached at: {path}")
    except Exception as e:
        print(f"  ✗ Failed to download {mt_id}: {e}")
        if "401" in str(e) or "gated" in str(e).lower():
            print("  Note: Check if access requires accepting terms on Hugging Face or providing HF_TOKEN.")

    # 2. Download TTS Model
    tts_id = config.settings.tts_model_id
    print(f"\n[2/2] Downloading TTS model ({tts_id})...")
    try:
        path = snapshot_download(
            repo_id=tts_id,
            token=hf_token,
            local_files_only=False,
        )
        print(f"  ✓ Indic Parler-TTS model cached at: {path}")
    except Exception as e:
        print(f"  ✗ Failed to download {tts_id}: {e}")
        if "401" in str(e) or "gated" in str(e).lower():
            print(f"  ! Access to {tts_id} requires acceptance of terms and a valid HF_TOKEN.")
            print(f"  ! Visit: https://huggingface.co/{tts_id}")

    print("\n" + "=" * 60)
    print(" Download process finished.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-download IndicVoice models.")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check configuration and credentials without downloading.",
    )
    args = parser.parse_args()
    download_models(check_only=args.check_only)
