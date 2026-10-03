"""Unit tests for cache manager."""

import tempfile
import numpy as np
from indicvoice.cache import AudioCache


def test_cache_set_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = AudioCache(tmpdir)
        key = cache.compute_key(
            text="Hello Odisha",
            language="odia",
            voice="female",
            skip_translation=False,
        )

        assert cache.get(key) is None

        waveform = np.sin(np.linspace(0, 10, 16000)).astype(np.float32)
        meta = {"source_text": "Hello Odisha", "duration_sec": 1.0}
        cache.set(key, meta, waveform, 16000)

        retrieved = cache.get(key)
        assert retrieved is not None
        cached_meta, cached_audio, cached_sr = retrieved
        assert cached_meta["source_text"] == "Hello Odisha"
        assert cached_sr == 16000
        assert len(cached_audio) == 16000
