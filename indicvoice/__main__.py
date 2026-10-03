"""Command-line interface for IndicVoice."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from indicvoice.config import load_config
from indicvoice.errors import IndicVoiceError
from indicvoice.pipeline import IndicVoicePipeline


def main() -> None:
    """CLI entry point for python -m indicvoice."""
    parser = argparse.ArgumentParser(
        prog="indicvoice",
        description="Translate English text to Indian languages and speak as natural audio.",
    )

    parser.add_argument(
        "text",
        nargs="?",
        default="",
        help="Text to translate and speak (English, or target script if --skip-translation is set).",
    )
    parser.add_argument(
        "--lang",
        "-l",
        default="odia",
        help="Target language (default: odia).",
    )
    parser.add_argument(
        "--voice",
        "-v",
        default="female",
        choices=["female", "male"],
        help="Voice preset (default: female).",
    )
    parser.add_argument(
        "--skip-translation",
        "-s",
        action="store_true",
        help="Skip translation; directly synthesize audio from text in the target script.",
    )
    parser.add_argument(
        "--custom-voice",
        default=None,
        help="Custom voice description prompt (overrides the voice preset).",
    )
    parser.add_argument(
        "--out",
        "-o",
        default=None,
        help="Destination path for output WAV file.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass request cache.",
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="Show all supported languages and exit.",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="Show available voices and exit.",
    )

    args = parser.parse_args()
    config = load_config()

    if args.list_languages:
        print("\nSupported Languages:")
        for name, info in config.languages.items():
            print(f"  • {name:<12} {info.label:<24} [Script: {info.script}, MT: {info.mt_code}]")
        sys.exit(0)

    if args.list_voices:
        print("\nAvailable Voices:")
        for voice_type in config.voices:
            print(f"  • {voice_type}")
        sys.exit(0)

    if not args.text.strip():
        parser.print_help()
        print("\nError: Please provide text to speak, or use --list-languages.")
        sys.exit(1)

    try:
        pipeline = IndicVoicePipeline(config=config)
        print(f"\nProcessing in {args.lang.capitalize()} (voice: {args.voice})...")

        result = pipeline.translate_and_speak(
            text=args.text,
            target_lang=args.lang,
            voice=args.voice,
            skip_translation=args.skip_translation,
            custom_description=args.custom_voice,
            use_cache=not args.no_cache,
        )

        # Copy to custom destination if requested
        final_audio_path = result.audio_path
        if args.out:
            dest = Path(args.out).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(result.audio_path, str(dest))
            final_audio_path = str(dest)

        print("\n" + "=" * 50)
        print(f"Source Text:     {result.source_text}")
        print(f"Translated Text: {result.translated_text}")
        print(f"Audio File:      {final_audio_path}")
        print(f"Audio Duration:  {result.duration_sec} s")
        print(f"Cached Result:   {'Yes' if result.cached else 'No'}")
        if result.failed_sentences:
            print(f"Failed sentences: {len(result.failed_sentences)}")
        print("=" * 50 + "\n")

    except IndicVoiceError as e:
        print(f"\nError: {e.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
