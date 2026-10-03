"""Pydantic schemas for the IndicVoice API."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    """Request payload for POST /synthesize."""

    text: str = Field(
        ...,
        description="Text to translate and speak, or direct target script text if skip_translation=True.",
        examples=["Welcome to Odisha."],
    )
    target_lang: str = Field(
        default="odia",
        description="Target Indian language (e.g. odia, hindi, bengali).",
        examples=["odia"],
    )
    voice: str = Field(
        default="female",
        description="Voice preset (female or male).",
        examples=["female"],
    )
    skip_translation: bool = Field(
        default=False,
        description="If True, synthesizes directly from target script text without translation.",
    )
    custom_voice: Optional[str] = Field(
        default=None,
        description="Optional custom voice description prompt overriding default preset.",
    )


class SynthesizeResponse(BaseModel):
    """Response payload for POST /synthesize."""

    source_text: str
    translated_text: str
    target_lang: str
    audio_url: str
    duration_sec: float
    cached: bool = False
    failed_sentences: list[str] = Field(default_factory=list)


class LanguageDetail(BaseModel):
    """Metadata for an individual supported language."""

    name: str
    label: str
    script: str
    default_voice: str
    mt_code: str


class LanguagesResponse(BaseModel):
    """Response payload for GET /languages."""

    languages: list[LanguageDetail]
    voices: list[str]


class HealthResponse(BaseModel):
    """Response payload for GET /health."""

    status: str
    version: str
    device: str
    models_loaded: bool
    translation_model_id: str
    tts_model_id: str


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    error: str
    code: int
    detail: Optional[str] = None
