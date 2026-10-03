"""Audio processing and file handling utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Union
import numpy as np
import soundfile as sf


def create_silence(duration_ms: int, sampling_rate: int) -> np.ndarray:
    """Generate a silent audio chunk of given duration in milliseconds."""
    num_samples = int((duration_ms / 1000.0) * sampling_rate)
    return np.zeros(num_samples, dtype=np.float32)


def normalize_peak(waveform: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    """Normalize peak volume of a waveform to target decibels (default -1.0 dBFS)."""
    if len(waveform) == 0:
        return waveform

    peak = np.max(np.abs(waveform))
    if peak <= 1e-6:
        return waveform

    target_amplitude = 10.0 ** (target_db / 20.0)
    gain = target_amplitude / peak
    return (waveform * gain).astype(np.float32)


def calculate_duration(waveform: np.ndarray, sampling_rate: int) -> float:
    """Calculate duration of audio waveform in seconds."""
    if sampling_rate <= 0 or len(waveform) == 0:
        return 0.0
    return float(len(waveform) / sampling_rate)


def save_wav(
    filepath: Union[str, Path],
    waveform: np.ndarray,
    sampling_rate: int,
) -> Path:
    """Save float32 audio waveform to standard 16-bit PCM WAV file."""
    path = Path(filepath).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Clip to [-1.0, 1.0] before writing
    clipped = np.clip(waveform, -1.0, 1.0)
    sf.write(str(path), clipped, sampling_rate, subtype="PCM_16")
    return path
