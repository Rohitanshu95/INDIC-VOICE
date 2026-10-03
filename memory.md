# Project Memory — IndicVoice

Living context file. Update it whenever a decision is made, something breaks, or a fact is verified. Anyone (or any AI assistant) picking up this project should read this file first.

**Version:** v0.2.1 · **Last updated:** 2026-10-03

---

## 1. Project in One Paragraph

IndicVoice takes normal English text, translates it into an Indian language (Odia first), and speaks it as audio. It chains two free open-source models: **IndicTrans2** for translation and **`ai4bharat/indic-parler-tts`** for speech. No model training is involved.

## 2. Current Status

| Item | Status |
|------|--------|
| Phase | Phase 0 PoC notebooks prepared; Phase 1 Core Pipeline scaffolded and implemented |
| Next action | Phase 2 (API and UI) and Phase 3 (Quality and evaluation) |
| Blockers | None known. Note: `ai4bharat/indic-parler-tts` is gated on Hugging Face; users must accept terms and set `HF_TOKEN`. |

## 3. Decisions Log

Never delete rows. Add a new row that supersedes an old one.

| Date | Decision | Reason |
|------|----------|--------|
| 2026-10-03 | Build a pipeline (translate, then TTS), not one end-to-end model | No single free model translates and speaks; chaining is simple and proven |
| 2026-10-03 | Translation: IndicTrans2 200M distilled | Free, covers all 22 scheduled Indian languages, fits free GPU memory |
| 2026-10-03 | **TTS: `ai4bharat/indic-parler-tts` (confirmed by user)** | Free, covers Odia, voice set by a text description, runs on Colab |
| 2026-10-03 | Odia is the priority; Hindi and Bengali alongside it for MVP | Main use case plus two well-supported languages for comparison |
| 2026-10-03 | FastAPI for the API, Gradio for the UI | Fastest route to a developer API and a demo |
| 2026-10-03 | Voices defined in `config/voices.yaml` (description plus speaker name per language) | Keeps voice consistent and editable without code changes |
| 2026-10-03 | Folder layout fixed in `docs/architecture.md` section 3; docs live in `docs/`, `memory.md` at root | Clear separation of core logic, API, UI, scripts, data |
| 2026-10-03 | Model loading is lazy / fallback-aware for local dev & testing | Allows tests, preprocessing, config, and CLI validation without requiring full 4GB weights download during unit testing |

## 4. Models and References

| Purpose | Identifier | Notes |
|---------|-----------|-------|
| Translation | `ai4bharat/indictrans2-en-indic-dist-200M` | Needs `trust_remote_code=True` and `IndicTransToolkit` (or Fairseq / Transformers tokenizer) |
| **TTS (chosen)** | `ai4bharat/indic-parler-tts` | Dual tokenizers: prompt tokenizer + description tokenizer (`model.config.text_encoder._name_or_path`) |
| TTS (fallback) | AI4Bharat Indic-TTS (FastPitch + HiFi-GAN) | Lighter, CPU-friendly, less natural |
| TTS (voice cloning, optional) | `ai4bharat/IndicF5` | Needs a reference clip and its transcript; future option |
| Hosted alternatives | Bhashini, Sarvam AI | Only if self-hosting is not possible |

## 5. Indic Parler-TTS — Verified Facts

### Verified Findings:
- Model is hosted at `https://huggingface.co/ai4bharat/indic-parler-tts`.
- Model is **gated**: requires accepting terms on Hugging Face and providing `HF_TOKEN` in `.env`.
- Built on top of the Parler-TTS architecture (`ParlerTTSForConditionalGeneration`).
- Two tokenizers are required:
  1. Prompt tokenizer: `AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts")`
  2. Description tokenizer: `AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)`
- Language is inferred automatically from prompt characters/script; no explicit language code parameter needed for TTS generation.
- Sampling rate: Read dynamically from `model.config.sampling_rate` (typically 44100 Hz or 24000 Hz).
- License: Apache-2.0.
- Weights: ~3.75 GB.

## 6. Language Codes (IndicTrans2)

| Language | Code | Script |
|----------|------|--------|
| English (source) | `eng_Latn` | Latin |
| Odia | `ory_Orya` | Oriya (Odia) |
| Hindi | `hin_Deva` | Devanagari |
| Bengali | `ben_Beng` | Bengali |
| Tamil | `tam_Taml` | Tamil |
| Telugu | `tel_Telu` | Telugu |
| Kannada | `kan_Knda` | Kannada |
| Malayalam | `mal_Mlym` | Malayalam |
| Marathi | `mar_Deva` | Devanagari |
| Gujarati | `guj_Gujr` | Gujarati |
| Punjabi | `pan_Guru` | Gurmukhi |
| Assamese | `asm_Beng` | Bengali |

## 7. Environment & Versions

| Item | Recommended Value | Notes |
|------|-------------------|-------|
| Python version | 3.10 or 3.11 | Python 3.12+ may lack wheels for some audio dependencies |
| torch version | >= 2.1.0, < 2.5.0 | With CUDA 11.8/12.1 on GPU hosts |
| transformers version | >= 4.43.0 | Compatible with parler-tts |
| `parler-tts` | `git+https://github.com/huggingface/parler-tts.git` | Commit pinned in `requirements.txt` |
| `IndicTransToolkit` | `git+https://github.com/AI4Bharat/IndicTransToolkit.git` | Used for IndicTrans2 tokenization |
| `soundfile` | >= 0.12.1 | Audio I/O |
| `scipy` | >= 1.11.0 | Audio processing and resampling |

## 8. Voice Choices

| Language | Female description / speaker | Male description / speaker | Notes |
|----------|------------------------------|----------------------------|-------|
| Odia | Female speaker with a clear, moderate pace, natural tone, close recording with no background noise | Male speaker with a clear, resonant tone, moderate pace, close recording with no background noise | Odia script prompt controls pronunciation |
| Hindi | Divya speaks in a clear, moderately paced voice with a close recording and no background noise | Rohit speaks in a clear, moderately paced voice with a close recording and no background noise | Well-tested Hindi speakers in Indic Parler-TTS |
| Bengali | Aditi / Rashmi speaks in a clear, expressive voice at a moderate pace with clean audio | Arjun / Tapan speaks in a calm, clear voice at a moderate pace with clean audio | Tested Bengali voices |

## 9. Licenses (Verified)

| Component | License | Verified? |
|-----------|---------|-----------|
| IndicTrans2 | MIT / CC-BY-4.0 | Yes |
| `indic-parler-tts` (main model) | Apache-2.0 | Yes |
| `indic-parler-tts-pretrained` | Apache-2.0 | Yes |
| `parler-tts` library | Apache-2.0 | Yes |
| `IndicTransToolkit` | MIT | Yes |

## 10. Conventions

- Python 3.10+; clean modular architecture.
- All tunable values (languages, voices, limits) live in `config/`, never hard-coded.
- `indicvoice/` never imports from `api/` or `ui/`.
- Models are loaded once and wrapped in `Translator` and `Synthesizer` interfaces.
- Generated audio files are named by content hash or UUID, never by raw text.
- Public-facing language names are human-readable (`odia`); internal codes stay in config.
- Secrets (`HF_TOKEN`) live in `.env`, which is gitignored.

## 11. Known Gotchas and Risks

- `ai4bharat/indic-parler-tts` is gated on Hugging Face; users must accept terms on HF model page and set `HF_TOKEN`.
- Pre-download script handles setting cache directory and credentials cleanly.
- Script mismatch checking prevents feeding Latin/English text directly to Indic TTS in skip-translation mode.
- Sentence chunking and volume normalization prevent audio clipping or loudness jumps across multi-sentence outputs.

## 12. Change Log

| Date | Change |
|------|--------|
| 2026-10-03 | v0.1: Initial planning documents created |
| 2026-10-03 | v0.2: Indic Parler-TTS confirmed; full folder plan added; Hugging Face access, speaker selection, script check added |
| 2026-10-03 | v0.2.1: Phase 0 verified facts recorded (Apache-2.0 license, gating status, dual tokenizers, speaker presets). Root `memory.md` established. Phase 1 scaffolding and pipeline implemented. |
