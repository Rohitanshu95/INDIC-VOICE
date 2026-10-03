"""API route definitions for IndicVoice."""

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse

from api.schemas import (
    HealthResponse,
    LanguageDetail,
    LanguagesResponse,
    SynthesizeRequest,
    SynthesizeResponse,
)
from indicvoice import __version__
from indicvoice.errors import IndicVoiceError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check(request: Request) -> HealthResponse:
    """Check system health, compute device, and model load status."""
    pipeline = getattr(request.app.state, "pipeline", None)
    device = pipeline.translator.device if pipeline else "unknown"
    models_loaded = (
        pipeline.translator.is_loaded and pipeline.synthesizer.is_loaded
        if pipeline
        else False
    )

    return HealthResponse(
        status="ok",
        version=__version__,
        device=device,
        models_loaded=models_loaded,
        translation_model_id=pipeline.config.settings.translation_model_id if pipeline else "",
        tts_model_id=pipeline.config.settings.tts_model_id if pipeline else "",
    )


@router.get("/languages", response_model=LanguagesResponse, tags=["Configuration"])
async def list_languages(request: Request) -> LanguagesResponse:
    """Retrieve supported languages, scripts, and voice presets."""
    pipeline = request.app.state.pipeline
    config = pipeline.config

    languages = [
        LanguageDetail(
            name=name,
            label=info.label,
            script=info.script,
            default_voice=info.default_voice,
            mt_code=info.mt_code,
        )
        for name, info in config.languages.items()
    ]
    voices = list(config.voices.keys())

    return LanguagesResponse(languages=languages, voices=voices)


@router.post("/synthesize", response_model=SynthesizeResponse, tags=["Synthesis"])
async def synthesize_speech(
    payload: SynthesizeRequest,
    request: Request,
) -> SynthesizeResponse:
    """Translate English text to target Indian language and synthesize speech audio."""
    pipeline = request.app.state.pipeline

    try:
        result = pipeline.translate_and_speak(
            text=payload.text,
            target_lang=payload.target_lang,
            voice=payload.voice,
            skip_translation=payload.skip_translation,
            custom_description=payload.custom_voice,
        )

        audio_filename = Path(result.audio_path).name
        audio_url = f"/audio/{audio_filename}"

        return SynthesizeResponse(
            source_text=result.source_text,
            translated_text=result.translated_text,
            target_lang=result.target_lang,
            audio_url=audio_url,
            duration_sec=result.duration_sec,
            cached=result.cached,
            failed_sentences=result.failed_sentences,
        )

    except IndicVoiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    except Exception as e:
        logger.error(f"Synthesis failed with unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while generating audio. Please try again.",
        ) from e


@router.get("/audio/{filename}", tags=["Audio"])
async def get_audio_file(filename: str, request: Request) -> FileResponse:
    """Stream or download a generated WAV audio file."""
    pipeline = request.app.state.pipeline
    config = pipeline.config

    # Security check on filename
    safe_filename = Path(filename).name
    if not safe_filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Invalid audio file requested.")

    # Check output directory first, then cache directory
    out_dir = config.base_dir / config.settings.output_dir
    cache_dir = config.base_dir / config.settings.cache_dir

    cand1 = out_dir / safe_filename
    cand2 = cache_dir / safe_filename

    if cand1.exists():
        filepath = cand1
    elif cand2.exists():
        filepath = cand2
    else:
        raise HTTPException(status_code=404, detail="Audio file not found.")

    return FileResponse(
        path=str(filepath),
        media_type="audio/wav",
        filename=safe_filename,
    )
