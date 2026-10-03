"""Unit tests for config loading and validation."""

import pytest
from pathlib import Path
from indicvoice.config import load_config
from indicvoice.errors import UnsupportedLanguageError, UnsupportedVoiceError


def test_load_config_defaults():
    config = load_config()
    assert config.settings.max_chars == 2000
    assert config.settings.sentence_pause_ms == 250
    assert "odia" in config.languages
    assert "hindi" in config.languages
    assert "bengali" in config.languages


def test_get_language():
    config = load_config()
    odia = config.get_language("odia")
    assert odia.mt_code == "ory_Orya"
    assert odia.script == "Oriya"
    assert odia.default_voice == "female"

    # Case insensitive
    hindi = config.get_language("HINDI")
    assert hindi.mt_code == "hin_Deva"

    with pytest.raises(UnsupportedLanguageError):
        config.get_language("klingon")


def test_get_voice_description():
    config = load_config()
    desc_female = config.get_voice_description("female", "odia")
    assert "female" in desc_female.lower()

    desc_male = config.get_voice_description("male", "hindi")
    assert "rohit" in desc_male.lower()

    with pytest.raises(UnsupportedVoiceError):
        config.get_voice_description("robot", "odia")


def test_get_glossary():
    config = load_config()
    glossary = config.get_glossary("odia")
    assert "Odisha" in glossary
    assert glossary["Odisha"] == "ଓଡ଼ିଶା"
