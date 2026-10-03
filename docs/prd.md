# PRD — Indic Translate-and-Speak (working title: IndicVoice)

**Status:** Draft v0.2
**Owner:** Rohitanshu
**Last updated:** 2026-10-03

## Changes from v0.1

| Area | v0.1 | v0.2 |
|------|------|------|
| TTS model | Recommended, not final | **Decided: `ai4bharat/indic-parler-tts`** |
| Voice control | Generic presets | Presets built from a text description plus a recommended speaker name per language |
| Access | Not mentioned | Hugging Face account and token may be needed (related models are gated) |
| Setup | Generic | Install `parler-tts` from GitHub; pin versions |
| Folders | Basic tree | Full folder plan in `architecture.md` (docs, config, scripts, data) |
| Language handling | Dropdown only | Warn if the text script does not match the chosen language |

---

## 1. Problem

Most content is written in English, but many people in India are more comfortable listening in their own language, including Odia. Today, getting spoken audio in an Indian language means translating text by hand and then finding a TTS tool that actually supports the language. This is slow, and Odia in particular is poorly supported by mainstream tools.

## 2. Product Summary

A tool that takes **normal (English) text**, **translates** it into a chosen Indian language, and **speaks** it as natural-sounding audio. Odia is the priority language.

```
English text → IndicTrans2 → Indic text → Indic Parler-TTS → audio (.wav)
```

## 3. Goals

| # | Goal |
|---|------|
| G1 | Convert English text to spoken audio in Odia end-to-end with one action |
| G2 | Support several other Indian languages through the same pipeline |
| G3 | Use only free, open-source models (no per-call API cost) |
| G4 | Offer both a simple web UI and a programmatic API |
| G5 | Show the translated text next to the audio so users can verify it |
| G6 | Keep the code modular so either model can be swapped later |

## 4. Non-Goals (v1)

- Training or fine-tuning any model
- Voice cloning of specific people (IndicF5 stays a future option)
- Real-time streaming or live conversation
- Speech-to-text or speech-to-speech translation
- Source languages other than English
- Mobile app

## 5. Target Users

| Persona | Need |
|---------|------|
| **Developer / student (primary)** | A reusable building block, for example giving a chatbot a voice in Odia |
| **Content creator** | Turn English notices, scripts or announcements into local-language audio |
| **Accessibility user** | Listen instead of read, in a familiar language |

## 6. User Stories

1. As a user, I paste English text, pick Odia, and get an audio file I can play and download.
2. As a user, I see the Odia text that was spoken so I can check the translation.
3. As a user, I can pick a different language from a dropdown.
4. As a user, I can supply text already in the target language and skip translation.
5. As a user, I can choose between a female and a male voice.
6. As a developer, I can call an HTTP endpoint with text and a language and receive audio.
7. As a developer, I can add a language by editing config files, without changing code.

## 7. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Accept English text up to a configurable limit (default 2,000 characters) | Must |
| FR-2 | Translate English to the target language with IndicTrans2 (200M distilled) | Must |
| FR-3 | Synthesize speech from the translated text with **Indic Parler-TTS** | Must |
| FR-4 | Support Odia, Hindi and Bengali at launch | Must |
| FR-5 | Split long input into sentences, process each, join the audio | Must |
| FR-6 | Return translated text and audio together | Must |
| FR-7 | Download audio as WAV | Must |
| FR-8 | "Skip translation" mode for text already in the target language | Should |
| FR-9 | Voice presets (female, male) defined in `config/voices.yaml`, using a text description and a recommended speaker name per language | Must |
| FR-10 | Advanced option: custom voice description | Could |
| FR-11 | Detect when input text is in the wrong script for the chosen language and warn | Should |
| FR-12 | Support Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Punjabi, Assamese | Should |
| FR-13 | REST API with `/synthesize`, `/languages`, `/health` | Must |
| FR-14 | Cache results for repeated identical requests | Should |
| FR-15 | Glossary for names, places and fixed translations | Could |
| FR-16 | MP3 export | Could |
| FR-17 | Read the Hugging Face token from the environment when a model needs it | Must |

## 8. Non-Functional Requirements

| Area | Requirement |
|------|-------------|
| **Cost** | Zero per-request cost; runs on a free GPU tier or local hardware |
| **Performance** | 2 to 3 sentences return audio in under 15 s on a GPU. CPU-only works but slower |
| **Quality** | At least 8 of 10 Odia test sentences judged understandable by a native speaker |
| **Reliability** | A failed sentence must not crash the whole request |
| **Portability** | Runs on Colab/Kaggle, a local machine, or a Hugging Face Space |
| **Storage** | Plan for several GB of model downloads (TTS weights are about 3.75 GB) |
| **Licensing** | Every model and library license is read and recorded before public or commercial use |
| **Privacy** | No user text is sent to third-party APIs; nothing stored beyond the cache |

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Native-speaker acceptability (translation + audio) | ≥ 80% of test set |
| End-to-end latency, short input, GPU | < 15 s |
| Languages working end-to-end | 3 at MVP, 8+ at v1 |
| Failed requests on a 50-sentence test set | < 2% |
| Voice consistency across sentences in one request | No audible voice change in review |

## 10. Milestones

| Milestone | Outcome |
|-----------|---------|
| **M0 — Proof of concept** | Notebook: English → Odia audio for one sentence using both models |
| **M1 — Core pipeline** | Scaffolded repo, pipeline module, CLI, 3 languages |
| **M2 — API + UI** | FastAPI service and Gradio interface |
| **M3 — Quality pass** | Test set, native-speaker review, glossary, more languages |
| **M4 — Deploy** | Public demo, Docker image, README |

## 11. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Translation errors on names, numbers, dates | Wrong audio content | Show translated text; glossary; number normalization |
| Voice varies between sentences | Poor listening experience | Fixed voice description and speaker name per language; sentence chunking |
| Model access is gated or needs login | Setup fails | Document HF account, accepting terms, and `HF_TOKEN` in the README |
| `parler-tts` is installed from GitHub, not PyPI | Breaks when upstream changes | Pin the commit hash in `requirements.txt` |
| Large weights on free tiers | Out-of-memory or slow start | Distilled translation model; lazy loading; cache weights in a persistent folder |
| License limits commercial use | Blocks monetization | Verify and record all licenses in `memory.md` |
| Long input degrades quality | Bad output | Character limit and sentence chunking |

## 12. Open Questions

1. Personal/learning use only, or public or commercial deployment? (decides license strictness)
2. Stand-alone tool, or a voice layer for another project such as a chatbot?
3. Hosting target: Colab only, Hugging Face Space, or own server?
4. Which Odia speaker name from the model card sounds best? (decide after listening tests)
5. Output formats needed beyond WAV?
