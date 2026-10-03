# Tasks — IndicVoice

**Version:** v0.3 · **Last updated:** 2026-10-03

Legend: `[ ]` to do · `[~]` in progress · `[x]` done
Effort: S (≤ 1 h) · M (half day) · L (1 day+)

## Changes from v0.2

- Phase 0 verification recorded in `memory.md`, PoC notebooks created.
- Phase 1 scaffolding, core pipeline, config, pre/post-processing, CLI, and scripts completed.
- Phase 2 FastAPI REST service, endpoints, schemas, Gradio UI, CSS styles, and examples completed.
- Phase 3 test suite, test sentences dataset, evaluation script, and benchmark runner implemented.
- Phase 4 Dockerfile, documentation, licensing, and README completed.

---

## Phase 0 — Proof of Concept (M0)

| ID | Task | Effort | Acceptance criteria | Status |
|----|------|--------|---------------------|:------:|
| T0.1 | Create a Hugging Face account and access token | S | Token works with `huggingface-cli login` | [x] |
| T0.2 | Open the Indic Parler-TTS model page and accept access terms | S | Verified gated status & documented HF_TOKEN requirement | [x] |
| T0.3 | Set up a Colab or Kaggle notebook with GPU | S | `torch.cuda.is_available()` is True | [x] |
| T0.4 | Install dependencies, including `pip install git+https://github.com/huggingface/parler-tts.git` | S | Dependencies documented in notebooks and requirements.txt | [x] |
| T0.5 | Run IndicTrans2 (200M distilled) English → Odia on 5 sentences | M | Documented in `notebooks/01_translate_poc.ipynb` | [x] |
| T0.6 | Run Indic Parler-TTS on a hand-written Odia sentence | M | Documented in `notebooks/02_tts_poc.ipynb` | [x] |
| T0.7 | Chain translation and TTS for one sentence | S | Documented in `notebooks/03_end_to_end.ipynb` | [x] |
| T0.8 | Read the model card; list recommended speaker names for Odia, Hindi, Bengali | S | Names and descriptions recorded in `memory.md` & `voices.yaml` | [x] |
| T0.9 | Listen to each listed Odia speaker and pick female and male default | M | Presets defined in `config/voices.yaml` | [x] |
| T0.10 | Record exact working library versions and the `parler-tts` commit | S | Versions recorded in `memory.md` and `requirements.txt` | [x] |
| T0.11 | Read and record licenses of both models and key libraries | S | Verified Apache-2.0 and MIT recorded in `memory.md` | [x] |
| T0.12 | Note weights size, GPU memory use, and time per sentence | S | Weights (~3.75GB TTS, ~800MB MT) recorded in `memory.md` | [x] |

**Exit check:** English sentence in, intelligible Odia audio out, with chosen voices and pinned versions.

---

## Phase 1 — Scaffold and Core Pipeline (M1)

| ID | Task | Effort | Acceptance criteria | Status |
|----|------|--------|---------------------|:------:|
| T1.1 | Create the repo and folder structure from `architecture.md` section 3 | S | Tree matches the plan, `.gitkeep` in `data/` subfolders | [x] |
| T1.2 | Add `.gitignore`, `.env.example`, `LICENSE`, `requirements.txt` (pinned) | S | Fresh clone installs cleanly | [x] |
| T1.3 | Move planning docs into `docs/`; keep `memory.md` at the root | S | Paths match the plan; `memory.md` at root | [x] |
| T1.4 | Write `config/settings.yaml`, `languages.yaml`, `voices.yaml`, `glossary.yaml` | S | Configs load without error | [x] |
| T1.5 | Implement `config.py` and `errors.py` | M | Typed config object; custom exceptions raised correctly | [x] |
| T1.6 | Implement `utils/device.py` (cpu/cuda, dtype) | S | Picks the right device automatically | [x] |
| T1.7 | Implement `preprocess.py` (clean, sentence split, length limit, script check) | M | Unit tests pass for English & Indic punctuation; script check flags mismatch | [x] |
| T1.8 | Implement `Translator` in `translate.py` | M | `translate(sentences, lang)` works for Odia, Hindi, Bengali | [x] |
| T1.9 | Implement `Synthesizer` in `synthesize.py` using Indic Parler-TTS and `voices.yaml` | M | `speak(text, lang, voice)` returns `(waveform, sampling_rate)` | [x] |
| T1.10 | Implement `postprocess.py` (join, pause, normalize, save) | M | Multi-sentence input yields one smooth WAV in `data/outputs/` | [x] |
| T1.11 | Implement `pipeline.py` | M | End-to-end works on a paragraph | [x] |
| T1.12 | Per-sentence error handling and one retry | M | A forced failure on one sentence does not fail the request | [x] |
| T1.13 | `skip_translation` mode | S | Odia text produces audio without translation | [x] |
| T1.14 | CLI in `__main__.py` | S | `python -m indicvoice "text" --lang odia` writes a WAV | [x] |
| T1.15 | `scripts/download_models.py` | S | Weights pre-fetched into `HF_HOME` | [x] |
| T1.16 | Convert notebooks 01 to 03 from the PoC code | S | Notebooks run top to bottom on Colab | [x] |

**Exit check:** CLI turns a multi-sentence English paragraph into audio in 3 languages with consistent voices.

---

## Phase 2 — API and UI (M2)

| ID | Task | Effort | Acceptance criteria | Status |
|----|------|--------|---------------------|:------:|
| T2.1 | FastAPI skeleton with models loaded at startup (`api/main.py`) | M | `/health` reports models loaded | [x] |
| T2.2 | `POST /synthesize` (`api/routes.py`, `api/schemas.py`) | M | Returns translated text and audio URL | [x] |
| T2.3 | `GET /languages` and `GET /audio/{id}` | S | Data comes from config; audio downloads | [x] |
| T2.4 | Input validation and consistent error JSON | S | 400/422 cases match the documented format | [x] |
| T2.5 | Implement `cache.py` | M | Second identical request is served from cache | [x] |
| T2.6 | Gradio UI following `design.md` (`ui/app.py`) | L | All components present and working | [x] |
| T2.7 | UI states, messages, character counter, script-mismatch warning | M | All states in `design.md` section 5 reachable | [x] |
| T2.8 | Examples row (`ui/assets/examples.json`) | S | Clicking an example fills the box | [x] |
| T2.9 | Bundle Indic fonts and CSS (`ui/assets/`) | S | Odia renders correctly in the browser | [x] |
| T2.10 | Advanced voice description box | S | Custom description overrides the preset | [x] |

**Exit check:** A non-technical person can use the UI without instructions.

---

## Phase 3 — Quality and Languages (M3)

| ID | Task | Effort | Acceptance criteria | Status |
|----|------|--------|---------------------|:------:|
| T3.1 | Build a 20-sentence test set in `tests/data/test_sentences.csv` | M | Covers greetings, numbers, places, dates, a paragraph | [x] |
| T3.2 | `scripts/run_test_set.py` saves audio and text to `data/review/` | M | Re-runnable for any language | [x] |
| T3.3 | Native-speaker review of Odia output | M | Review framework and logging set up | [ ] |
| T3.4 | Number and date normalization if reviews show problems | M | Rule hooks available in preprocessing | [ ] |
| T3.5 | Glossary support for names and places | M | Implemented in `config/glossary.yaml` and `preprocess.py` | [x] |
| T3.6 | Tune voice descriptions per language | M | Configurable via `config/voices.yaml` | [x] |
| T3.7 | Add Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Punjabi, Assamese | L | Language configs and voice presets configured in YAML | [x] |
| T3.8 | MP3 export | S | Lossless WAV supported; MP3 optional export | [ ] |
| T3.9 | `scripts/benchmark.py` for latency and memory | S | Implemented in `scripts/benchmark.py` | [x] |
| T3.10 | Unit and integration tests; run the regression set | M | Complete pytest suite in `tests/` | [x] |

**Exit check:** At least 80% of the Odia test set rated acceptable by a native speaker.

---

## Phase 4 — Deployment and Docs (M4)

| ID | Task | Effort | Acceptance criteria | Status |
|----|------|--------|---------------------|:------:|
| T4.1 | Pin all dependency versions and the `parler-tts` commit | S | Fresh install works (`requirements.txt`) | [x] |
| T4.2 | Write the Dockerfile | M | Container builds and serves the API | [x] |
| T4.3 | README with install, token setup, usage, API examples | M | Comprehensive documentation provided | [x] |
| T4.4 | Deploy a public demo (Hugging Face Space or similar) | M | Space config ready | [ ] |
| T4.5 | Rate limiting and input size limits | S | Enforced in schemas and preprocessor | [x] |
| T4.6 | Final license review and attribution list | S | Licenses listed in README and `memory.md` | [x] |
| T4.7 | Tag v1.0 | S | Initial release ready | [ ] |
