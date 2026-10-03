"""Main pipeline orchestrator for IndicVoice."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import numpy as np

from indicvoice.cache import AudioCache
from indicvoice.config import Config, load_config
from indicvoice.errors import (
    ModelInferenceError,
)
from indicvoice.postprocess import join_chunks, save_output_audio
from indicvoice.preprocess import preprocess
from indicvoice.synthesize import Synthesizer
from indicvoice.translate import Translator

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result returned by the translate_and_speak pipeline."""

    source_text: str
    translated_text: str
    target_lang: str
    audio_path: str
    duration_sec: float
    cached: bool = False
    failed_sentences: list[str] = field(default_factory=list)
    waveform: Optional[np.ndarray] = None
    sampling_rate: int = 44100
    timing_ms: dict[str, float] = field(default_factory=dict)


class IndicVoicePipeline:
    """End-to-end translate-and-speak pipeline."""

    def __init__(
        self,
        config: Optional[Config] = None,
        translator: Optional[Translator] = None,
        synthesizer: Optional[Synthesizer] = None,
    ):
        self.config = config or load_config()
        self.translator = translator or Translator(config=self.config)
        self.synthesizer = synthesizer or Synthesizer(config=self.config)

        cache_path = self.config.base_dir / self.config.settings.cache_dir
        self.cache = AudioCache(cache_path) if self.config.settings.cache_enabled else None

    def translate_and_speak(
        self,
        text: str,
        target_lang: str = "odia",
        voice: str = "female",
        skip_translation: bool = False,
        custom_description: Optional[str] = None,
        use_cache: Optional[bool] = None,
    ) -> PipelineResult:
        """Execute end-to-end pipeline.

        Args:
            text: Input text (English, or Indic if skip_translation=True).
            target_lang: Target language code name (e.g. 'odia', 'hindi', 'bengali').
            voice: Voice preset ('female', 'male').
            skip_translation: If True, skips translation and speaks input text directly.
            custom_description: Optional custom voice description overriding preset.
            use_cache: Override cache setting if specified.

        Returns:
            PipelineResult with translated text, audio file path, duration, and metrics.
        """
        start_time = time.time()
        timing: dict[str, float] = {}

        lang_info = self.config.get_language(target_lang)
        lang_key = lang_info.name

        # Check Cache
        check_cache = self.config.settings.cache_enabled if use_cache is None else use_cache
        cache_key = ""
        if check_cache and self.cache:
            cache_key = self.cache.compute_key(
                text=text,
                language=lang_key,
                voice=voice,
                skip_translation=skip_translation,
                custom_description=custom_description,
            )
            cached_item = self.cache.get(cache_key)
            if cached_item is not None:
                meta, waveform, srate = cached_item
                logger.info(f"Serving cached request for key {cache_key[:8]}")
                return PipelineResult(
                    source_text=meta.get("source_text", text),
                    translated_text=meta.get("translated_text", ""),
                    target_lang=lang_key,
                    audio_path=meta.get("audio_path", ""),
                    duration_sec=meta.get("duration_sec", 0.0),
                    cached=True,
                    failed_sentences=meta.get("failed_sentences", []),
                    waveform=waveform,
                    sampling_rate=srate,
                    timing_ms={"total": (time.time() - start_time) * 1000.0},
                )

        # 1. Preprocess
        t_prep_start = time.time()
        glossary = self.config.get_glossary(lang_key)
        sentences = preprocess(
            text=text,
            max_chars=self.config.settings.max_chars,
            expected_script=lang_info.script,
            language_name=lang_info.name,
            skip_translation=skip_translation,
            glossary=glossary,
        )
        timing["preprocess"] = (time.time() - t_prep_start) * 1000.0

        # 2. Translate (if not skipped)
        t_trans_start = time.time()
        if skip_translation:
            indic_sentences = sentences
        else:
            indic_sentences = self.translator.translate(
                sentences=sentences,
                target_lang=lang_key,
            )
        timing["translate"] = (time.time() - t_trans_start) * 1000.0

        full_translated_text = " ".join(indic_sentences)

        # 3. Synthesize speech per sentence with 1 retry on failure
        t_synth_start = time.time()
        audio_chunks: list[np.ndarray] = []
        failed_sentences: list[str] = []
        sampling_rate = self.synthesizer.sampling_rate

        for sentence in indic_sentences:
            if not sentence.strip():
                continue

            success = False
            for attempt in range(2):  # initial attempt + 1 retry
                try:
                    chunk, srate = self.synthesizer.speak(
                        text=sentence,
                        language=lang_key,
                        voice=voice,
                        custom_description=custom_description,
                    )
                    sampling_rate = srate
                    if len(chunk) > 0:
                        audio_chunks.append(chunk)
                        success = True
                        break
                except Exception as e:
                    logger.warning(
                        f"Attempt {attempt + 1} failed for sentence '{sentence}': {e}"
                    )
                    time.sleep(0.05)

            if not success:
                logger.error(f"Sentence failed after retry: '{sentence}'")
                failed_sentences.append(sentence)

        timing["synthesize"] = (time.time() - t_synth_start) * 1000.0

        if not audio_chunks:
            raise ModelInferenceError(
                "synthesis",
                f"Failed to generate audio for all {len(indic_sentences)} sentences.",
            )

        # 4. Postprocess & Save Audio
        t_post_start = time.time()
        merged_waveform = join_chunks(
            chunks=audio_chunks,
            pause_ms=self.config.settings.sentence_pause_ms,
            sampling_rate=sampling_rate,
        )

        out_dir = self.config.base_dir / self.config.settings.output_dir
        saved_path, duration_sec = save_output_audio(
            waveform=merged_waveform,
            sampling_rate=sampling_rate,
            output_dir=out_dir,
            language=lang_key,
            text_for_hash=text,
        )
        timing["postprocess"] = (time.time() - t_post_start) * 1000.0
        timing["total"] = (time.time() - start_time) * 1000.0

        result = PipelineResult(
            source_text=text,
            translated_text=full_translated_text,
            target_lang=lang_key,
            audio_path=str(saved_path),
            duration_sec=round(duration_sec, 2),
            cached=False,
            failed_sentences=failed_sentences,
            waveform=merged_waveform,
            sampling_rate=sampling_rate,
            timing_ms=timing,
        )

        # Store in cache if enabled
        if check_cache and self.cache and cache_key:
            meta = {
                "source_text": result.source_text,
                "translated_text": result.translated_text,
                "target_lang": result.target_lang,
                "audio_path": result.audio_path,
                "duration_sec": result.duration_sec,
                "failed_sentences": result.failed_sentences,
            }
            self.cache.set(
                key=cache_key,
                metadata=meta,
                waveform=merged_waveform,
                sampling_rate=sampling_rate,
            )

        return result
