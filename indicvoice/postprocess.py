"""Audio postprocessing: chunk concatenation, pause insertion, volume normalization, and saving."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np

from indicvoice.utils.audio import (
    calculate_duration,
    create_silence,
    normalize_peak,
    save_wav,
)


def join_chunks(
    chunks: list[np.ndarray],
    pause_ms: int = 250,
    sampling_rate: int = 44100,
) -> np.ndarray:
    """Concatenate multiple sentence waveforms with a silent pause between each.

    Normalizes individual chunks to ensure volume consistency before merging.
    """
    valid_chunks = [c for c in chunks if len(c) > 0]
    if not valid_chunks:
        return np.zeros(0, dtype=np.float32)

    if len(valid_chunks) == 1:
        return normalize_peak(valid_chunks[0])

    silence = create_silence(pause_ms, sampling_rate)
    assembled: list[np.ndarray] = []

    for i, chunk in enumerate(valid_chunks):
        norm_chunk = normalize_peak(chunk)
        assembled.append(norm_chunk)
        if i < len(valid_chunks) - 1:
            assembled.append(silence)

    merged = np.concatenate(assembled, axis=0)
    # Final master peak normalization
    return normalize_peak(merged)


def save_output_audio(
    waveform: np.ndarray,
    sampling_rate: int,
    output_dir: Union[str, Path],
    language: str = "indic",
    text_for_hash: Optional[str] = None,
) -> Tuple[Path, float]:
    """Save finalized waveform to WAV file in output_dir.

    Filename is constructed from language and a short hash or timestamp.
    Returns (Path_to_wav, duration_seconds).
    """
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    if text_for_hash:
        hash_str = hashlib.sha256(text_for_hash.encode("utf-8")).hexdigest()[:8]
    else:
        hash_str = hashlib.sha256(waveform.tobytes()).hexdigest()[:8]

    timestamp = int(time.time())
    filename = f"{language.lower()}_{timestamp}_{hash_str}.wav"
    filepath = out_path / filename

    saved_path = save_wav(filepath, waveform, sampling_rate)
    duration = calculate_duration(waveform, sampling_rate)

    return saved_path, duration
