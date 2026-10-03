"""Unit tests for preprocessing, sentence splitting, script validation, and glossary."""

import pytest
from indicvoice.errors import EmptyInputError, ScriptMismatchError, TextTooLongError
from indicvoice.preprocess import (
    apply_glossary,
    clean_text,
    detect_script,
    preprocess,
    split_sentences,
)


def test_clean_text():
    raw = "  Hello   world! \t\n\n\nHow are you?  "
    cleaned = clean_text(raw)
    assert cleaned == "Hello world!\n\nHow are you?"


def test_split_sentences_english():
    text = "Hello world. How are you today? I am fine! Dr. Smith arrived at 5 p.m."
    sentences = split_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Hello world."
    assert sentences[1] == "How are you today?"
    assert sentences[2] == "I am fine! Dr. Smith arrived at 5 p.m."


def test_split_sentences_indic():
    text = "ଓଡ଼ିଶା କୁ ସ୍ୱାଗତ । ଆପଣ କେମିତି ଅଛନ୍ତି ? ମୁଁ ଭଲ ଅଛି ।"
    sentences = split_sentences(text)
    assert len(sentences) == 3
    assert "ଓଡ଼ିଶା" in sentences[0]
    assert "କେମିତି" in sentences[1]


def test_detect_script():
    assert detect_script("Welcome to Odisha") == "Latin"
    assert detect_script("ଓଡ଼ିଶା କୁ ସ୍ୱାଗତ") == "Oriya"
    assert detect_script("नमस्ते भारत") == "Devanagari"
    assert detect_script("স্বাগতম") == "Bengali"


def test_preprocess_validation_errors():
    with pytest.raises(EmptyInputError):
        preprocess("")

    with pytest.raises(EmptyInputError):
        preprocess("   \n\t  ")

    with pytest.raises(TextTooLongError):
        preprocess("a" * 2001, max_chars=2000)


def test_preprocess_script_mismatch():
    # If skip_translation is True, input must match the expected script
    with pytest.raises(ScriptMismatchError):
        preprocess(
            text="This is English text.",
            expected_script="Oriya",
            language_name="odia",
            skip_translation=True,
        )

    # Valid Odia text with skip_translation=True should pass
    sentences = preprocess(
        text="ଓଡ଼ିଶା କୁ ସ୍ୱାଗତ ।",
        expected_script="Oriya",
        language_name="odia",
        skip_translation=True,
    )
    assert len(sentences) == 1
    assert "ଓଡ଼ିଶା" in sentences[0]


def test_apply_glossary():
    glossary = {"Odisha": "ଓଡ଼ିଶା", "Bhubaneswar": "ଭୁବନେଶ୍ୱର"}
    text = "Welcome to Odisha and visit Bhubaneswar."
    replaced = apply_glossary(text, glossary)
    assert "ଓଡ଼ିଶା" in replaced
    assert "ଭୁବନେଶ୍ୱର" in replaced
