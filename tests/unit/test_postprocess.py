"""Unit tests for audio postprocessing."""

import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from indicvoice.postprocess import join_chunks, save_output_audio
from indicvoice.utils.audio import create_silence, normalize_peak


def test_create_silence():
    s = create_silence(duration_ms=250, sampling_rate=16000)
    assert len(s) == 4000
    assert np.all(s == 0.0)


def test_normalize_peak():
    chunk = np.array([0.1, -0.2, 0.4, -0.5], dtype=np.float32)
    norm = normalize_peak(chunk, target_db=0.0)
    assert np.isclose(np.max(np.abs(norm)), 1.0, atol=1e-3)


def test_join_chunks():
    c1 = np.ones(1000, dtype=np.float32) * 0.5
    c2 = np.ones(1000, dtype=np.float32) * 0.5
    merged = join_chunks([c1, c2], pause_ms=100, sampling_rate=10000)
    # Length should be 1000 + (100ms * 10 = 1000) + 1000 = 3000
    assert len(merged) == 3000


def test_save_output_audio():
    waveform = np.sin(np.linspace(0, 2 * np.pi, 8000)).astype(np.float32)
    with tempfile.TemporaryDirectory() as tmpdir:
        path, duration = save_output_audio(
            waveform=waveform,
            sampling_rate=16000,
            output_dir=tmpdir,
            language="odia",
        )
        assert path.exists()
        assert np.isclose(duration, 0.5, atol=0.05)
        # Verify readable by soundfile
        data, sr = sf.read(str(path))
        assert sr == 16000
        assert len(data) == 8000
