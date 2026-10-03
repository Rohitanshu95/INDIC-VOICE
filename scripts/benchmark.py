"""Benchmark latency, throughput, and memory consumption across languages."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from indicvoice.config import load_config
from indicvoice.pipeline import IndicVoicePipeline


def run_benchmark(iterations: int = 3, languages: list[str] | None = None) -> None:
    config = load_config(base_dir=ROOT_DIR)
    pipeline = IndicVoicePipeline(config=config)

    test_languages = languages or ["odia", "hindi", "bengali"]
    test_sample = "Welcome to Odisha. Bhubaneswar is known as the temple city of India."

    print("=" * 70)
    print(" IndicVoice - Pipeline Performance Benchmark")
    print("=" * 70)
    print(f"Device:      {pipeline.translator.device}")
    print(f"Iterations:  {iterations}")
    print(f"Input:       \"{test_sample}\" ({len(test_sample)} chars)")
    print("-" * 70)

    report: dict[str, dict[str, float]] = {}

    for lang in test_languages:
        print(f"\nBenchmarking {lang.upper()}...")
        latencies = []
        durations = []
        rtf_list = []

        for i in range(iterations):
            t0 = time.time()
            res = pipeline.translate_and_speak(
                text=test_sample,
                target_lang=lang,
                voice="female",
                use_cache=False,
            )
            lat = time.time() - t0
            rtf = lat / max(res.duration_sec, 0.001)

            latencies.append(lat)
            durations.append(res.duration_sec)
            rtf_list.append(rtf)
            print(f"  Run {i + 1}: latency={lat:.2f}s, audio={res.duration_sec:.2f}s, RTF={rtf:.2f}")

        avg_lat = sum(latencies) / len(latencies)
        avg_dur = sum(durations) / len(durations)
        avg_rtf = sum(rtf_list) / len(rtf_list)

        report[lang] = {
            "avg_latency_sec": round(avg_lat, 3),
            "avg_audio_duration_sec": round(avg_dur, 2),
            "real_time_factor": round(avg_rtf, 2),
        }

    print("\n" + "=" * 70)
    print(f"{'Language':<12} {'Avg Latency (s)':<18} {'Audio Len (s)':<16} {'RTF (Latency/Audio)':<20}")
    print("-" * 70)
    for lang, metrics in report.items():
        print(
            f"{lang:<12} {metrics['avg_latency_sec']:<18} {metrics['avg_audio_duration_sec']:<16} {metrics['real_time_factor']:<20}"
        )
    print("=" * 70)

    out_file = ROOT_DIR / "data" / "review" / "benchmark_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Results saved to: {out_file}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run pipeline benchmark.")
    parser.add_argument("--iterations", type=int, default=3, help="Number of runs per language.")
    parser.add_argument("--lang", nargs="*", default=None, help="Languages to benchmark.")
    args = parser.parse_args()

    run_benchmark(iterations=args.iterations, languages=args.lang)
