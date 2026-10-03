"""Custom exceptions for the IndicVoice package."""

from typing import Optional


class IndicVoiceError(Exception):
    """Base exception for all IndicVoice errors."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EmptyInputError(IndicVoiceError):
    """Raised when the input text is empty or only whitespace."""

    def __init__(self, message: str = "Enter some text to continue."):
        super().__init__(message, status_code=400)


class TextTooLongError(IndicVoiceError):
    """Raised when input text exceeds the maximum character limit."""

    def __init__(
        self,
        current_len: int,
        max_chars: int = 2000,
        message: Optional[str] = None,
    ):
        msg = (
            message
            or f"Please keep the text under {max_chars} characters. Your text is {current_len} characters."
        )
        super().__init__(msg, status_code=400)
        self.current_len = current_len
        self.max_chars = max_chars


class UnsupportedLanguageError(IndicVoiceError):
    """Raised when an unsupported language is requested."""

    def __init__(self, language: str, supported: Optional[list[str]] = None):
        msg = f"Language '{language}' is not supported."
        if supported:
            msg += f" Supported languages: {', '.join(supported)}."
        super().__init__(msg, status_code=400)
        self.language = language
        self.supported = supported or []


class UnsupportedVoiceError(IndicVoiceError):
    """Raised when a voice preset does not exist for a language."""

    def __init__(self, voice: str, language: str):
        super().__init__(
            f"Voice '{voice}' is not available for language '{language}'.",
            status_code=400,
        )
        self.voice = voice
        self.language = language


class ScriptMismatchError(IndicVoiceError):
    """Raised when text script does not match the target language (e.g. English script in skip-translation mode)."""

    def __init__(
        self,
        language: str,
        detected_script: str,
        expected_script: str,
        message: Optional[str] = None,
    ):
        msg = (
            message
            or f"This text doesn't look like {language.capitalize()} ({expected_script}). Untick 'already in this language' to translate it first."
        )
        super().__init__(msg, status_code=400)
        self.language = language
        self.detected_script = detected_script
        self.expected_script = expected_script


class AuthenticationRequiredError(IndicVoiceError):
    """Raised when a Hugging Face token is missing for a gated model."""

    def __init__(
        self,
        model_id: str,
        message: Optional[str] = None,
    ):
        msg = (
            message
            or f"A model ({model_id}) requires Hugging Face access. Please set HF_TOKEN in your environment or .env file and accept terms at https://huggingface.co/{model_id}."
        )
        super().__init__(msg, status_code=401)
        self.model_id = model_id


class ModelLoadError(IndicVoiceError):
    """Raised when failing to load a model or tokenizer."""

    def __init__(self, model_id: str, detail: str):
        super().__init__(
            f"Failed to load model '{model_id}': {detail}",
            status_code=500,
        )
        self.model_id = model_id
        self.detail = detail


class ModelInferenceError(IndicVoiceError):
    """Raised when translation or TTS inference fails."""

    def __init__(self, stage: str, detail: str):
        super().__init__(
            f"Inference failed during {stage}: {detail}",
            status_code=500,
        )
        self.stage = stage
        self.detail = detail
