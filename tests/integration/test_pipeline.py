"""Integration tests for the complete IndicVoice pipeline."""

import os
import pytest
from indicvoice.config import load_config
from indicvoice.pipeline import IndicVoicePipeline


@pytest.fixture(autouse=True)
def enable_mock_models(monkeypatch):
    """Enable mock models for pipeline integration testing without GPU/4GB weights."""
    monkeypatch.setenv("INDICVOICE_MOCK_MODELS", "1")
    monkeypatch.setenv("INDICVOICE_DEVICE", "cpu")


def test_pipeline_end_to_end(tmp_path, monkeypatch):
    config = load_config()
    config.base_dir = tmp_path
    config.settings.output_dir = "outputs"
    config.settings.cache_dir = "cache"

    pipeline = IndicVoicePipeline(config=config)

    # 1. Translate and speak English to Odia
    result = pipeline.translate_and_speak(
        text="Welcome to Odisha. Bhubaneswar is the temple city.",
        target_lang="odia",
        voice="female",
    )

    assert result.target_lang == "odia"
    assert "ଓଡ଼ିଶା" in result.translated_text
    assert result.duration_sec > 0
    assert os.path.exists(result.audio_path)
    assert not result.cached
    assert len(result.failed_sentences) == 0

    # 2. Second request should hit cache
    cached_result = pipeline.translate_and_speak(
        text="Welcome to Odisha. Bhubaneswar is the temple city.",
        target_lang="odia",
        voice="female",
    )
    assert cached_result.cached is True
    assert cached_result.audio_path == result.audio_path


def test_pipeline_skip_translation(tmp_path):
    config = load_config()
    config.base_dir = tmp_path
    config.settings.output_dir = "outputs"
    config.settings.cache_dir = "cache"

    pipeline = IndicVoicePipeline(config=config)

    odia_input = "ଓଡ଼ିଶା କୁ ସ୍ୱାଗତ ।"
    result = pipeline.translate_and_speak(
        text=odia_input,
        target_lang="odia",
        skip_translation=True,
    )

    assert result.translated_text == odia_input
    assert os.path.exists(result.audio_path)
    assert result.duration_sec > 0
