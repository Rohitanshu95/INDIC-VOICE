"""Configuration loading and validation for IndicVoice."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from indicvoice.errors import UnsupportedLanguageError, UnsupportedVoiceError


class LanguageInfo(BaseModel):
    """Metadata for a supported language."""

    name: str
    label: str
    mt_code: str
    script: str
    default_voice: str = "female"


class Settings(BaseModel):
    """Runtime pipeline settings."""

    max_chars: int = 2000
    sentence_pause_ms: int = 250
    cache_enabled: bool = True
    mt_batch_size: int = 8
    mt_num_beams: int = 5
    device: str = "auto"
    translation_model_id: str = "ai4bharat/indictrans2-en-indic-dist-200M"
    tts_model_id: str = "ai4bharat/indic-parler-tts"
    default_sampling_rate: int = 44100
    output_dir: str = "data/outputs"
    cache_dir: str = "data/cache"
    review_dir: str = "data/review"

    # Environment variables
    hf_token: Optional[str] = None
    hf_home: Optional[str] = None


class Config:
    """Aggregated configuration object."""

    def __init__(
        self,
        settings: Settings,
        languages: dict[str, LanguageInfo],
        voices: dict[str, dict[str, str]],
        glossary: dict[str, dict[str, str]],
        base_dir: Path,
    ):
        self.settings = settings
        self.languages = languages
        self.voices = voices
        self.glossary = glossary
        self.base_dir = base_dir

    def get_language(self, name: str) -> LanguageInfo:
        """Retrieve language info by name (case-insensitive)."""
        key = name.lower().strip()
        if key not in self.languages:
            raise UnsupportedLanguageError(key, supported=list(self.languages.keys()))
        return self.languages[key]

    def get_voice_description(self, voice: str, language: str) -> str:
        """Get description prompt for a given voice preset and language."""
        v_key = voice.lower().strip()
        l_key = language.lower().strip()

        if v_key not in self.voices:
            raise UnsupportedVoiceError(v_key, l_key)

        lang_voices = self.voices[v_key]
        if l_key in lang_voices:
            return lang_voices[l_key]

        # Fallback to general description
        return f"A {v_key} speaker speaks in a clear, natural, moderately paced voice with close recording and no background noise."

    def get_glossary(self, language: str) -> dict[str, str]:
        """Get term replacements for a language."""
        l_key = language.lower().strip()
        return self.glossary.get(l_key, {})


def load_config(config_dir: Optional[Path | str] = None, base_dir: Optional[Path | str] = None) -> Config:
    """Load configuration YAMLs and environment variables."""
    # Find base directory (repository root)
    if base_dir is None:
        current = Path(__file__).resolve().parent
        if (current.parent / "config").exists():
            base_dir = current.parent
        else:
            base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir).resolve()

    if config_dir is None:
        cfg_path = base_dir / "config"
    else:
        cfg_path = Path(config_dir).resolve()

    # Load .env file
    env_file = base_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Settings
    settings_file = cfg_path / "settings.yaml"
    settings_dict: dict[str, Any] = {}
    if settings_file.exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            settings_dict = yaml.safe_load(f) or {}

    # Override settings with environment variables if present
    hf_token = os.getenv("HF_TOKEN") or settings_dict.get("hf_token")
    hf_home = os.getenv("HF_HOME") or settings_dict.get("hf_home")
    device = os.getenv("INDICVOICE_DEVICE") or settings_dict.get("device", "auto")

    settings_dict["hf_token"] = hf_token
    settings_dict["hf_home"] = hf_home
    settings_dict["device"] = device

    settings = Settings(**settings_dict)

    # If HF_HOME is set in settings/env, update os.environ so transformers/huggingface_hub honor it
    if settings.hf_home:
        abs_hf_home = str((base_dir / settings.hf_home).resolve())
        os.environ["HF_HOME"] = abs_hf_home

    # Languages
    lang_file = cfg_path / "languages.yaml"
    languages: dict[str, LanguageInfo] = {}
    if lang_file.exists():
        with open(lang_file, "r", encoding="utf-8") as f:
            raw_lang = yaml.safe_load(f) or {}
            for code, data in raw_lang.get("languages", {}).items():
                languages[code.lower()] = LanguageInfo(name=code.lower(), **data)

    # Voices
    voices_file = cfg_path / "voices.yaml"
    voices: dict[str, dict[str, str]] = {}
    if voices_file.exists():
        with open(voices_file, "r", encoding="utf-8") as f:
            raw_voices = yaml.safe_load(f) or {}
            voices = raw_voices.get("voices", {})

    # Glossary
    glossary_file = cfg_path / "glossary.yaml"
    glossary: dict[str, dict[str, str]] = {}
    if glossary_file.exists():
        with open(glossary_file, "r", encoding="utf-8") as f:
            raw_glossary = yaml.safe_load(f) or {}
            glossary = raw_glossary.get("glossary", {})

    return Config(
        settings=settings,
        languages=languages,
        voices=voices,
        glossary=glossary,
        base_dir=base_dir,
    )
