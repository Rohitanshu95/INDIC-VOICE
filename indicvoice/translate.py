"""Translation module wrapping ai4bharat/indictrans2-en-indic-dist-200M."""

from __future__ import annotations

import logging
import os
from typing import Optional

from indicvoice.config import Config, load_config
from indicvoice.errors import (
    ModelInferenceError,
    ModelLoadError,
    UnsupportedLanguageError,
)
from indicvoice.utils.device import get_device_and_dtype

logger = logging.getLogger(__name__)


class Translator:
    """IndicTrans2 translation engine."""

    def __init__(
        self,
        config: Optional[Config] = None,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self.config = config or load_config()
        self.model_id = model_id or self.config.settings.translation_model_id
        self.preferred_device = device or self.config.settings.device
        self.device, self.dtype = get_device_and_dtype(self.preferred_device)

        self.model = None
        self.tokenizer = None
        self.ip = None  # IndicProcessor from IndicTransToolkit if present
        self.is_loaded = False
        self.mock_mode = os.getenv("INDICVOICE_MOCK_MODELS", "0").lower() in ("1", "true")

    def load_model(self) -> None:
        """Load tokenizer and model weights onto target device."""
        if self.is_loaded:
            return

        if self.mock_mode:
            logger.info("Translator running in mock mode.")
            self.is_loaded = True
            return

        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            logger.info(f"Loading IndicTrans2 model '{self.model_id}' on {self.device}...")

            # Attempt to initialize IndicProcessor if IndicTransToolkit is installed
            try:
                try:
                    from IndicTransToolkit.processor import IndicProcessor
                except ImportError:
                    from IndicTransToolkit import IndicProcessor

                self.ip = IndicProcessor(inference=True)
            except ImportError:
                logger.warning(
                    "IndicTransToolkit not installed. Falling back to direct Hugging Face tokenizer."
                )
                self.ip = None


            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True,
            )

            kwargs = {"trust_remote_code": True}
            if self.dtype is not None and "cuda" in self.device:
                kwargs["torch_dtype"] = self.dtype

            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_id,
                **kwargs,
            ).to(self.device)
            self.model.eval()

            self.is_loaded = True
            logger.info("IndicTrans2 model loaded successfully.")

        except Exception as e:
            logger.error(f"Failed to load translation model '{self.model_id}': {e}", exc_info=True)
            raise ModelLoadError(self.model_id, str(e)) from e

    def translate(
        self,
        sentences: list[str],
        target_lang: str,
        source_lang_code: str = "eng_Latn",
    ) -> list[str]:
        """Translate a list of sentences from English to target language.

        Args:
            sentences: List of English sentences.
            target_lang: Language key (e.g. 'odia', 'hindi', 'bengali').
            source_lang_code: IndicTrans2 source code (default 'eng_Latn').

        Returns:
            List of translated sentences.
        """
        if not sentences:
            return []

        lang_info = self.config.get_language(target_lang)
        target_lang_code = lang_info.mt_code

        if not self.is_loaded:
            self.load_model()

        if self.mock_mode or self.model is None:
            # Deterministic mock translation for local testing
            mock_translations = {
                "odia": "ଓଡ଼ିଶା କୁ ସ୍ୱାଗତ ।",
                "hindi": "ओडिशा में आपका स्वागत है।",
                "bengali": "ওড়িশায় আপনাকে স্বাগতম।",
            }
            default_mock = f"[{lang_info.label}] "
            return [
                mock_translations.get(target_lang.lower(), f"{default_mock}{s}")
                for s in sentences
            ]

        try:
            import torch

            batch_size = self.config.settings.mt_batch_size
            num_beams = self.config.settings.mt_num_beams
            translated: list[str] = []

            for i in range(0, len(sentences), batch_size):
                batch = sentences[i : i + batch_size]

                if self.ip is not None:
                    # Preprocess with IndicTransToolkit
                    preprocessed_batch = self.ip.preprocess_batch(
                        batch,
                        src_lang=source_lang_code,
                        tgt_lang=target_lang_code,
                    )
                    inputs = self.tokenizer(
                        preprocessed_batch,
                        padding="longest",
                        truncation=True,
                        max_length=256,
                        return_tensors="pt",
                    ).to(self.device)

                    with torch.inference_mode():
                        outputs = self.model.generate(
                            **inputs,
                            num_beams=num_beams,
                            num_return_sequences=1,
                            max_length=256,
                        )

                    decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
                    postprocessed = self.ip.postprocess_batch(
                        decoded,
                        lang=target_lang_code,
                    )
                    translated.extend(postprocessed)
                else:
                    # Direct transformer generation
                    # Prepend target language tag to prompt if supported
                    tagged_batch = [f">{target_lang_code}< {s}" for s in batch]
                    inputs = self.tokenizer(
                        tagged_batch,
                        padding=True,
                        truncation=True,
                        max_length=256,
                        return_tensors="pt",
                    ).to(self.device)

                    with torch.inference_mode():
                        outputs = self.model.generate(
                            **inputs,
                            num_beams=num_beams,
                            max_length=256,
                        )

                    decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
                    translated.extend(decoded)

            return translated

        except Exception as e:
            logger.error(f"Translation inference error: {e}", exc_info=True)
            raise ModelInferenceError("translation", str(e)) from e
