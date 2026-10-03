"""Run standard test set from tests/data/test_sentences.csv and save audio to data/review/."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from indicvoice.config import load_config
from indicvoice.pipeline import IndicVoicePipeline


def run_test_set(
    csv_file: Path,
    output_dir: Path,
    target_language: str | None = None,
    voice: str = "female",
) -> None:
    config = load_config(base_dir=ROOT_DIR)
    pipeline = IndicVoicePipeline(config=config)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "review_summary.csv"

    print("=" * 65)
    print(" IndicVoice - Test Set Evaluation Runner")
    print("=" * 65)
    print(f"Test CSV:   {csv_file}")
    print(f"Output Dir: {output_dir}")
    print(f"Language:   {target_language or 'All languages in CSV'}")
    print(f"Voice:      {voice}")
    print("-" * 65)

    results = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_id = row.get("id")
            s_lang = row.get("language", "odia").lower().strip()
            s_text = row.get("english", "").strip()
            s_notes = row.get("notes", "")

            if target_language and s_lang != target_language.lower():
                continue

            print(f"[{s_id}] ({s_lang}) Processing: \"{s_text[:45]}...\"")
            t0 = time.time()
            try:
                res = pipeline.translate_and_speak(
                    text=s_text,
                    target_lang=s_lang,
                    voice=voice,
                    use_cache=False,
                )
                latency = round(time.time() - t0, 3)
                results.append({
                    "id": s_id,
                    "language": s_lang,
                    "english": s_text,
                    "translated": res.translated_text,
                    "duration_sec": res.duration_sec,
                    "latency_sec": latency,
                    "audio_file": res.audio_path,
                    "status": "SUCCESS" if not res.failed_sentences else "PARTIAL",
                    "notes": s_notes,
                })
                print(f"   ✓ Done in {latency}s -> Audio: {Path(res.audio_path).name}")
            except Exception as e:
                latency = round(time.time() - t0, 3)
                results.append({
                    "id": s_id,
                    "language": s_lang,
                    "english": s_text,
                    "translated": "",
                    "duration_sec": 0.0,
                    "latency_sec": latency,
                    "audio_file": "",
                    "status": f"FAILED: {e}",
                    "notes": s_notes,
                })
                print(f"   ✗ Error: {e}")

    # Write summary report
    fieldnames = [
        "id", "language", "english", "translated",
        "duration_sec", "latency_sec", "audio_file", "status", "notes"
    ]
    with open(summary_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    print("\n" + "=" * 65)
    print(f" Completed {len(results)} sentences.")
    print(f" Successful: {success_count}/{len(results)} ({round(success_count/max(len(results),1)*100, 1)}%)")
    print(f" Summary written to: {summary_csv}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run test set sentences and save audio.")
    parser.add_argument("--csv", default=str(ROOT_DIR / "tests" / "data" / "test_sentences.csv"))
    parser.add_argument("--out-dir", default=str(ROOT_DIR / "data" / "review"))
    parser.add_argument("--lang", default=None, help="Filter by language (e.g. odia, hindi, bengali).")
    parser.add_argument("--voice", default="female", help="Voice preset.")
    args = parser.parse_args()

    run_test_set(
        csv_file=Path(args.csv),
        output_dir=Path(args.out_dir),
        target_language=args.lang,
        voice=args.voice,
    )
