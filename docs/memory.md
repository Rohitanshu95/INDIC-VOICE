# Project Memory — IndicVoice

Living context file. Update it whenever a decision is made, something breaks, or a fact is verified. Anyone (or any AI assistant) picking up this project should read this file first.

**Version:** v0.2 · **Last updated:** 2026-10-03

---

## 1. Project in One Paragraph

IndicVoice takes normal English text, translates it into an Indian language (Odia first), and speaks it as audio. It chains two free open-source models: **IndicTrans2** for translation and **`ai4bharat/indic-parler-tts`** for speech. No model training is involved.

## 2. Current Status

| Item | Status |
|------|--------|
| Phase | Planning complete (v0.2), Phase 0 not started |
| Next action | T0.1 to T0.12 in `docs/tasks.md` (account, access, notebook proof of concept, speaker selection) |
| Blockers | None known |

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

## 4. Models and References

| Purpose | Identifier | Notes |
|---------|-----------|-------|
| Translation | `ai4bharat/indictrans2-en-indic-dist-200M` | Needs `trust_remote_code=True` and `IndicTransToolkit` |
| **TTS (chosen)** | `ai4bharat/indic-parler-tts` | See section 5 |
| TTS (fallback) | AI4Bharat Indic-TTS (FastPitch + HiFi-GAN) | Lighter, CPU-friendly, less natural |
| TTS (voice cloning, optional) | `ai4bharat/IndicF5` | Needs a reference clip and its transcript; future option |
| Hosted alternatives | Bhashini, Sarvam AI | Only if self-hosting is not possible |

## 5. Indic Parler-TTS — What Is Known

### Seen in public sources (Hugging Face pages and discussions, June 2026 and earlier)
- The model is a fine-tuned version of Indic Parler-TTS Pretrained, trained on about 1,806 hours of Indic and English data, officially speaking 20 Indic languages plus English.
- The language is detected from the text you give it; switch languages by changing the text.
- Install with `pip install git+https://github.com/huggingface/parler-tts.git`; the model card inference code runs on Google Colab.
- The `indic-parler-tts-pretrained` sibling is listed as **gated** and shows an Apache-2.0 license on its page.
- Weights are about 3.75 GB.

### Still to verify (do not assume)
| Item | Status |
|------|--------|
| License of the **main** `indic-parler-tts` model | Not verified |
| Whether the main model is also gated | Not verified |
| Recommended Odia speaker names | Not verified; read the model card |
| Recommended Hindi and Bengali speaker names | Not verified |
| Exact sampling rate | Read from `model.config.sampling_rate` |
| Memory use on a free GPU | Not measured |

## 6. Language Codes (IndicTrans2)

| Language | Code |
|----------|------|
| English (source) | `eng_Latn` |
| Odia | `ory_Orya` |
| Hindi | `hin_Deva` |
| Bengali | `ben_Beng` |
| Tamil | `tam_Taml` |
| Telugu | `tel_Telu` |
| Kannada | `kan_Knda` |
| Malayalam | `mal_Mlym` |
| Marathi | `mar_Deva` |
| Gujarati | `guj_Gujr` |
| Punjabi | `pan_Guru` |
| Assamese | `asm_Beng` |

## 7. Environment Notes

Fill in during Phase 0.

| Item | Value |
|------|-------|
| Python version | _to record_ |
| torch version | _to record_ |
| transformers version | _to record_ |
| `parler-tts` commit hash | _to record_ |
| IndicTransToolkit version | _to record_ |
| GPU used | _to record_ |
| Peak GPU memory | _to record_ |
| Time per sentence (GPU) | _to record_ |
| `HF_HOME` location | _to record_ |

## 8. Voice Choices

| Language | Female speaker | Male speaker | Chosen on | Notes |
|----------|----------------|--------------|-----------|-------|
| Odia | _to choose_ | _to choose_ | — | Listen to every listed speaker on the same sentence |
| Hindi | _to choose_ | _to choose_ | — | |
| Bengali | _to choose_ | _to choose_ | — | |

## 9. Licenses (Verify Before Public or Commercial Use)

| Component | License | Verified? |
|-----------|---------|-----------|
| IndicTrans2 | _check model card_ | No |
| `indic-parler-tts` (main model) | _check model card_ | No |
| `indic-parler-tts-pretrained` | Apache-2.0 shown on its page | Seen, re-check |
| `parler-tts` library | _check repo_ | No |
| IndicTransToolkit | _check repo_ | No |
| IndicF5 (if used) | _check model card_ | No |

## 10. Conventions

- Python 3.10+; format with `black`, lint with `ruff`.
- All tunable values (languages, voices, limits) live in `config/`, never hard-coded.
- `indicvoice/` never imports from `api/` or `ui/`.
- Models are loaded once and wrapped in `Translator` and `Synthesizer` so they can be swapped.
- Generated audio files are named by hash, never by user text.
- Public-facing language names are human-readable (`odia`); internal codes stay in the code.
- Secrets (`HF_TOKEN`) live in `.env`, which is gitignored.

## 11. Known Gotchas and Risks

Seed list from planning. Replace with real findings as they appear.

- Translation can mangle names, numbers and dates; always show the translated text.
- TTS quality can drop on very long inputs; split by sentence.
- The voice can drift between sentences unless the same description and speaker name are used every time.
- Free GPU sessions disconnect; keep `HF_HOME` on persistent storage.
- `parler-tts` is installed from GitHub, so pin a commit; library versions can conflict with `transformers`.
- Odia script needs a proper font in the UI or it may render as boxes.
- Passing English text to the TTS model with "skip translation" on gives bad audio; the script check should catch this.

## 12. Test Log

| Date | Language | Test | Result | Notes |
|------|----------|------|--------|-------|
| — | — | — | — | No tests run yet |

## 13. Native-Speaker Review Notes

| Date | Reviewer | Language | Verdict | Issues found |
|------|----------|----------|---------|--------------|
| — | — | — | — | Not reviewed yet |

## 14. Open Questions

1. Personal/learning use only, or public or commercial deployment?
2. Stand-alone tool, or a voice layer for another project such as a chatbot?
3. Hosting target: Colab only, Hugging Face Space, or own server?
4. Output formats beyond WAV?
5. Which Odia speaker sounds best? (decide in T0.9)

## 15. Change Log

| Date | Change |
|------|--------|
| 2026-10-03 | v0.1: initial planning documents created |
| 2026-10-03 | v0.2: Indic Parler-TTS confirmed as TTS model; full folder plan added; Hugging Face access, speaker selection, script check, and model pre-download tasks added; docs moved to `docs/` |

## 16. How to Use This File

1. Read sections 1 to 3 first for context.
2. Check section 11 before debugging.
3. After any session, update sections 2, 3, 7, 8, 12 and 15.
4. Replace every "to verify" item in section 5 with a checked fact and its source.
