"""Synthesizer module wrapping ai4bharat/indic-parler-tts."""

from __future__ import annotations

import logging
import os
from typing import Optional, Tuple
import numpy as np

from indicvoice.config import Config, load_config
from indicvoice.errors import (
    AuthenticationRequiredError,
    ModelInferenceError,
    ModelLoadError,
)
from indicvoice.utils.device import get_device_and_dtype

logger = logging.getLogger(__name__)


class Synthesizer:
    """Indic Parler-TTS speech synthesis engine."""

    def __init__(
        self,
        config: Optional[Config] = None,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self.config = config or load_config()
        self.model_id = model_id or self.config.settings.tts_model_id
        self.preferred_device = device or self.config.settings.device
        self.device, self.dtype = get_device_and_dtype(self.preferred_device)

        self.model = None
        self.tokenizer = None
        self.description_tokenizer = None
        self.sampling_rate = self.config.settings.default_sampling_rate
        self.is_loaded = False
        self.mock_mode = os.getenv("INDICVOICE_MOCK_MODELS", "0").lower() in ("1", "true")

    def load_model(self) -> None:
        """Load Parler-TTS model and dual tokenizers."""
        if self.is_loaded:
            return

        if self.mock_mode:
            logger.info("Synthesizer running in mock mode.")
            self.is_loaded = True
            return

        try:
            import torch
            from transformers import AutoTokenizer
            from parler_tts import ParlerTTSForConditionalGeneration

            hf_token = self.config.settings.hf_token or os.getenv("HF_TOKEN")

            logger.info(f"Loading Indic Parler-TTS model '{self.model_id}' on {self.device}...")

            kwargs = {}
            if hf_token:
                kwargs["token"] = hf_token
            if self.dtype is not None and "cuda" in self.device:
                kwargs["torch_dtype"] = self.dtype

            try:
                self.model = ParlerTTSForConditionalGeneration.from_pretrained(
                    self.model_id,
                    **kwargs,
                ).to(self.device)
                self.model.eval()

                self.sampling_rate = getattr(
                    self.model.config,
                    "sampling_rate",
                    self.config.settings.default_sampling_rate,
                )

                # 1. Prompt tokenizer (Indic text)
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_id,
                    token=hf_token,
                )

                # 2. Description tokenizer (from text_encoder)
                text_encoder_path = getattr(
                    self.model.config.text_encoder,
                    "_name_or_path",
                    "google/flan-t5-large",
                )
                self.description_tokenizer = AutoTokenizer.from_pretrained(
                    text_encoder_path,
                    token=hf_token,
                )

                self.is_loaded = True
                logger.info(f"Indic Parler-TTS loaded successfully. Sampling rate: {self.sampling_rate} Hz.")

            except Exception as e:
                err_str = str(e)
                if "401" in err_str or "gated" in err_str.lower() or "restricted" in err_str.lower():
                    raise AuthenticationRequiredError(self.model_id) from e
                raise

        except AuthenticationRequiredError:
            raise
        except Exception as e:
            logger.error(f"Failed to load TTS model '{self.model_id}': {e}", exc_info=True)
            raise ModelLoadError(self.model_id, str(e)) from e

    def speak(
        self,
        text: str,
        language: str,
        voice: str = "female",
        custom_description: Optional[str] = None,
    ) -> Tuple[np.ndarray, int]:
        """Synthesize speech audio waveform from Indic text.

        Args:
            text: Single sentence or short phrase in target Indic script.
            language: Language name (e.g. 'odia', 'hindi', 'bengali').
            voice: Voice preset name ('female', 'male').
            custom_description: Optional custom text description overriding the preset.

        Returns:
            Tuple of (waveform_numpy_array, sampling_rate_int).
        """
        if not text or not text.strip():
            return np.zeros(0, dtype=np.float32), self.sampling_rate

        if not self.is_loaded:
            self.load_model()

        # Determine description prompt
        if custom_description and custom_description.strip():
            description = custom_description.strip()
        else:
            description = self.config.get_voice_description(voice, language)

        if self.mock_mode or self.model is None:
            # Generate 1.0 second synthetic audio chime/tone for testing
            duration_s = max(0.8, min(4.0, len(text) * 0.08))
            t = np.linspace(0, duration_s, int(self.sampling_rate * duration_s), endpoint=False, dtype=np.float32)
            # 440 Hz gentle sine wave decaying envelope
            freq = 440.0 if voice == "female" else 220.0
            envelope = np.exp(-t * 0.8)
            waveform = (0.2 * np.sin(2 * np.pi * freq * t) * envelope).astype(np.float32)
            return waveform, self.sampling_rate

        try:
            import torch

            prompt_input_ids = self.tokenizer(
                text,
                return_tensors="pt",
            ).input_ids.to(self.device)

            description_input_ids = self.description_tokenizer(
                description,
                return_tensors="pt",
            ).input_ids.to(self.device)

            with torch.inference_mode():
                generation = self.model.generate(
                    input_ids=description_input_ids,
                    prompt_input_ids=prompt_input_ids,
                )

            # Squeeze tensor into 1D numpy array
            audio_arr = generation.cpu().numpy().squeeze().astype(np.float32)
            return audio_arr, self.sampling_rate

        except Exception as e:
            logger.error(f"TTS synthesis error for text '{text}': {e}", exc_info=True)
            raise ModelInferenceError("synthesis", str(e)) from e
