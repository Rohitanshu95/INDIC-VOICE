"""Hash-keyed disk cache for synthesized audio and translations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional, Tuple, Union
import numpy as np
import soundfile as sf


class AudioCache:
    """Manages cached request outputs on disk."""

    def __init__(self, cache_dir: Union[str, Path]):
        self.cache_dir = Path(cache_dir).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_key(
        text: str,
        language: str,
        voice: str = "female",
        skip_translation: bool = False,
        custom_description: Optional[str] = None,
    ) -> str:
        """Create a deterministic SHA-256 hash key for the input parameters."""
        raw = f"{text.strip()}|{language.lower()}|{voice.lower()}|{skip_translation}|{custom_description or ''}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Tuple[dict[str, Any], np.ndarray, int]]:
        """Retrieve cached metadata and audio if present.

        Returns:
            Tuple of (metadata_dict, waveform, sampling_rate) or None.
        """
        meta_file = self.cache_dir / f"{key}.json"
        audio_file = self.cache_dir / f"{key}.wav"

        if not meta_file.exists() or not audio_file.exists():
            return None

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

            waveform, sampling_rate = sf.read(str(audio_file), dtype="float32")
            return meta, waveform, sampling_rate
        except Exception:
            return None

    def set(
        self,
        key: str,
        metadata: dict[str, Any],
        waveform: np.ndarray,
        sampling_rate: int,
    ) -> None:
        """Store metadata and audio waveform to cache directory."""
        meta_file = self.cache_dir / f"{key}.json"
        audio_file = self.cache_dir / f"{key}.wav"

        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            clipped = np.clip(waveform, -1.0, 1.0)
            sf.write(str(audio_file), clipped, sampling_rate, subtype="PCM_16")
        except Exception:
            # Cache failure should never break the request
            pass
