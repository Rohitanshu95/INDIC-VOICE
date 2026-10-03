"""Gradio Web Application for IndicVoice."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Tuple
import gradio as gr

from indicvoice.config import load_config
from indicvoice.errors import IndicVoiceError
from indicvoice.pipeline import IndicVoicePipeline
from indicvoice.preprocess import detect_script

logger = logging.getLogger("indicvoice.ui")

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG = load_config(base_dir=ROOT_DIR)
PIPELINE = IndicVoicePipeline(config=CONFIG)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CSS_PATH = ASSETS_DIR / "style.css"
EXAMPLES_PATH = ASSETS_DIR / "examples.json"

# Load CSS content if exists
CSS_CONTENT = ""
if CSS_PATH.exists():
    CSS_CONTENT = CSS_PATH.read_text(encoding="utf-8")

# Map language dropdown labels to internal keys
LABEL_TO_KEY: dict[str, str] = {
    info.label: name for name, info in CONFIG.languages.items()
}
KEY_TO_LABEL: dict[str, str] = {
    name: info.label for name, info in CONFIG.languages.items()
}

LANGUAGE_CHOICES = [info.label for info in CONFIG.languages.values()]
DEFAULT_LANGUAGE = CONFIG.languages["odia"].label


def update_char_counter(text: str) -> str:
    """Update live character count."""
    length = len(text or "")
    max_c = CONFIG.settings.max_chars
    if length > max_c:
        return f"⚠️ {length} / {max_c} characters (Exceeds {max_c} limit)"
    return f"{length} / {max_c} characters"


def check_input_script(text: str, language_label: str, skip_trans: bool) -> str:
    """Show immediate warning if script mismatch is detected in skip-translation mode."""
    if not text or not skip_trans:
        return ""

    lang_key = LABEL_TO_KEY.get(language_label, "odia")
    expected_script = CONFIG.languages[lang_key].script
    detected = detect_script(text)

    if detected == "Latin" and expected_script != "Latin":
        return f"⚠️ Script Mismatch: Input text looks like English/Latin, but {language_label} expects {expected_script} script. Untick 'already in this language' to translate it first."
    return ""


def process_text(
    text: str,
    language_label: str,
    voice_preset: str,
    skip_translation: bool,
    custom_voice: str,
) -> Tuple[str, str | None, str]:
    """Execute pipeline and return translated text, audio file path, and status."""
    if not text or not text.strip():
        return "", None, "⚠️ Enter some text to continue."

    if len(text) > CONFIG.settings.max_chars:
        return (
            "",
            None,
            f"⚠️ Please keep the text under {CONFIG.settings.max_chars} characters. Your text is {len(text)} characters.",
        )

    lang_key = LABEL_TO_KEY.get(language_label, "odia")
    voice_key = voice_preset.lower().strip()

    try:
        result = PIPELINE.translate_and_speak(
            text=text,
            target_lang=lang_key,
            voice=voice_key,
            skip_translation=skip_translation,
            custom_description=custom_voice if custom_voice.strip() else None,
        )

        status_msg = f"✓ Success in {result.duration_sec} s"
        if result.cached:
            status_msg += " (Served from cache)"
        if result.failed_sentences:
            status_msg += f" • {len(result.failed_sentences)} sentence(s) could not be synthesized."

        return result.translated_text, result.audio_path, status_msg

    except IndicVoiceError as e:
        return "", None, f"⚠️ {e.message}"
    except Exception as e:
        logger.error(f"UI execution error: {e}", exc_info=True)
        return (
            "",
            None,
            "⚠️ Something went wrong while generating audio. Please check model access and try again.",
        )


def build_app() -> gr.Blocks:
    """Construct Gradio UI."""
    with gr.Blocks(
        title="IndicVoice — English to Indian Speech",
        css=CSS_CONTENT,
        theme=gr.themes.Soft(),
    ) as app:

        with gr.Row(elem_classes=["app-header"]):
            with gr.Column():
                gr.Markdown(
                    """
                    # IndicVoice 🎙️
                    ### Translate English into Indian languages and listen as natural spoken audio.
                    *Powered by IndicTrans2 and Indic Parler-TTS.*
                    """
                )

        with gr.Row():
            # Left Column: Input Controls
            with gr.Column(scale=1):
                input_text = gr.Textbox(
                    label="Input Text (English)",
                    placeholder="Type or paste English text to translate and speak...",
                    lines=6,
                )
                char_counter = gr.Markdown(
                    value=f"0 / {CONFIG.settings.max_chars} characters",
                    elem_classes=["char-counter"],
                )

                warning_banner = gr.Markdown(value="", visible=True)

                with gr.Row():
                    lang_dropdown = gr.Dropdown(
                        label="Target Language",
                        choices=LANGUAGE_CHOICES,
                        value=DEFAULT_LANGUAGE,
                    )
                    voice_dropdown = gr.Dropdown(
                        label="Voice Preset",
                        choices=["Female", "Male"],
                        value="Female",
                    )

                skip_translation_cb = gr.Checkbox(
                    label="My text is already in the target language (Skip translation)",
                    value=False,
                )

                with gr.Accordion("Advanced Voice Options", open=False):
                    custom_voice_box = gr.Textbox(
                        label="Custom Voice Description",
                        placeholder="e.g. A female speaker speaks in a calm, expressive, and gentle tone...",
                        lines=2,
                    )

                submit_btn = gr.Button("Translate & Speak", variant="primary", elem_classes=["btn-primary"])

            # Right Column: Output Display
            with gr.Column(scale=1):
                output_text = gr.Textbox(
                    label="Translated Text (Verified Script)",
                    interactive=False,
                    lines=6,
                    elem_classes=["indic-text-output"],
                )
                output_audio = gr.Audio(
                    label="Synthesized Audio",
                    type="filepath",
                )
                status_box = gr.Markdown(value="")

        # Examples Row
        if EXAMPLES_PATH.exists():
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Try an Example:")
                    try:
                        with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
                            examples_data = json.load(f)

                        with gr.Row():
                            for ex in examples_data:
                                btn = gr.Button(ex.get("title", "Example"), size="sm")

                                def _make_handler(item):
                                    def _fill():
                                        return (
                                            item["text"],
                                            item.get("language", DEFAULT_LANGUAGE),
                                            item.get("voice", "Female"),
                                            False,
                                            update_char_counter(item["text"]),
                                        )
                                    return _fill

                                btn.click(
                                    fn=_make_handler(ex),
                                    outputs=[
                                        input_text,
                                        lang_dropdown,
                                        voice_dropdown,
                                        skip_translation_cb,
                                        char_counter,
                                    ],
                                )
                    except Exception as e:
                        logger.warning(f"Failed to render examples: {e}")

        # Interactive Event Handlers
        input_text.change(
            fn=update_char_counter,
            inputs=[input_text],
            outputs=[char_counter],
        )

        input_text.change(
            fn=check_input_script,
            inputs=[input_text, lang_dropdown, skip_translation_cb],
            outputs=[warning_banner],
        )

        skip_translation_cb.change(
            fn=check_input_script,
            inputs=[input_text, lang_dropdown, skip_translation_cb],
            outputs=[warning_banner],
        )

        submit_btn.click(
            fn=process_text,
            inputs=[
                input_text,
                lang_dropdown,
                voice_dropdown,
                skip_translation_cb,
                custom_voice_box,
            ],
            outputs=[output_text, output_audio, status_box],
        )

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
