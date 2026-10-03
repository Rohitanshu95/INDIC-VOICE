# Architecture — IndicVoice

**Version:** v0.2 · **Last updated:** 2026-10-03

## Changes from v0.1

- TTS model fixed to `ai4bharat/indic-parler-tts`.
- Added a complete **folder plan** (section 3) with the purpose of every folder and file.
- Added Hugging Face auth, environment variables, and `.gitignore` rules.
- Added Parler-TTS call details (description tokenizer, prompt tokenizer, sampling rate).
- Docs moved into `docs/`; `memory.md` stays at the repo root.

---

## 1. Overview

A two-stage inference pipeline wrapped by a small service layer. No training is involved.

```
            ┌──────────────┐
 English    │  Preprocess  │  sentences
 text ────► │  (split,     │ ───────────┐
            │   validate)  │            ▼
            └──────────────┘     ┌──────────────┐
                                 │ Translator   │  IndicTrans2 200M distilled
                                 │ en → indic   │
                                 └──────┬───────┘
                                        │ Indic text, per sentence
                                        ▼
                                 ┌──────────────┐
                                 │ Synthesizer  │  ai4bharat/indic-parler-tts
                                 └──────┬───────┘
                                        │ waveform chunks
                                        ▼
                                 ┌──────────────┐
                                 │ Postprocess  │  join, pause, normalize
                                 └──────┬───────┘
                                        ▼
                         audio (WAV) + translated text
```

## 2. Components

| Component | Responsibility | Tech |
|-----------|----------------|------|
| **Preprocessor** | Clean text, split into sentences, enforce length limit, check script matches language | Python, regex, `indic-nlp-library` (optional) |
| **Translator** | English to target language | `ai4bharat/indictrans2-en-indic-dist-200M`, `IndicTransToolkit` |
| **Synthesizer** | Indic text to waveform | `ai4bharat/indic-parler-tts`, `parler-tts` |
| **Postprocessor** | Join chunks with short pauses, normalize volume, write WAV | `numpy`, `soundfile` |
| **Pipeline** | Orchestrates stages, handles per-sentence errors | Python module |
| **Cache** | Skip recomputing identical requests | On-disk, hash key |
| **API** | HTTP interface | FastAPI, Uvicorn |
| **UI** | Browser interface | Gradio |
| **Config loader** | Reads YAML and environment | PyYAML, `python-dotenv` |

## 3. Folder Plan

```
indicvoice/
├── README.md                    # install, run, API examples
├── memory.md                    # living project context (read first)
├── LICENSE
├── .gitignore
├── .env.example                 # HF_TOKEN, HF_HOME, device, limits
├── requirements.txt             # pinned versions, parler-tts pinned to a commit
├── pyproject.toml               # optional: tooling config (ruff, black, pytest)
├── Dockerfile
│
├── docs/
│   ├── prd.md
│   ├── tasks.md
│   ├── architecture.md
│   └── design.md
│
├── config/
│   ├── settings.yaml            # limits, pause length, cache on/off, default device
│   ├── languages.yaml           # language names, IndicTrans2 codes, script, voice mapping
│   ├── voices.yaml              # voice presets: description text + speaker name per language
│   └── glossary.yaml            # terms to keep or replace (names, places)
│
├── indicvoice/                  # the importable package (core logic)
│   ├── __init__.py
│   ├── __main__.py              # CLI entry: python -m indicvoice "text" --lang odia
│   ├── config.py                # loads YAML + env into typed objects
│   ├── errors.py                # custom exceptions (TooLong, UnsupportedLanguage, ModelFailure)
│   ├── preprocess.py            # clean, sentence split, length check, script check
│   ├── translate.py             # Translator class
│   ├── synthesize.py            # Synthesizer class (Indic Parler-TTS)
│   ├── postprocess.py           # join, pauses, normalize, save
│   ├── pipeline.py              # translate_and_speak(...) orchestrator
│   ├── cache.py                 # hash-keyed file cache
│   └── utils/
│       ├── device.py            # cpu / cuda selection, dtype
│       └── audio.py             # WAV helpers, optional MP3 conversion
│
├── api/
│   ├── main.py                  # FastAPI app, startup model loading
│   ├── schemas.py               # request/response models
│   └── routes.py                # /synthesize, /languages, /health, /audio/{id}
│
├── ui/
│   ├── app.py                   # Gradio app
│   └── assets/
│       ├── style.css
│       ├── examples.json        # one-click sample inputs
│       └── fonts/               # Noto Sans Oriya + other Indic fonts
│
├── notebooks/
│   ├── 01_translate_poc.ipynb   # IndicTrans2 only
│   ├── 02_tts_poc.ipynb         # Indic Parler-TTS only, speaker/voice tests
│   └── 03_end_to_end.ipynb      # both chained
│
├── scripts/
│   ├── download_models.py       # pre-fetch weights into HF_HOME
│   ├── run_test_set.py          # run tests/data/test_sentences.csv, save audio for review
│   └── benchmark.py             # latency and memory per language
│
├── tests/
│   ├── unit/                    # preprocess, config, cache
│   ├── integration/             # full pipeline on small set
│   └── data/
│       └── test_sentences.csv   # id, english, language, notes
│
└── data/                        # runtime files; gitignored except .gitkeep
    ├── cache/                   # cached audio + translations
    ├── outputs/                 # generated WAV files
    └── review/                  # audio and notes for native-speaker review
```

### Folder purposes

| Folder | Purpose | Created in |
|--------|---------|-----------|
| `docs/` | Planning documents | Phase 0 |
| `config/` | Everything tunable, so languages and voices change without code edits | Phase 1 |
| `indicvoice/` | Core logic; no web code here | Phase 1 |
| `api/` | HTTP layer only; imports from `indicvoice` | Phase 2 |
| `ui/` | Gradio layer only; imports from `indicvoice` | Phase 2 |
| `notebooks/` | Experiments and Colab entry points | Phase 0 |
| `scripts/` | One-off tools for setup, testing, benchmarking | Phase 1 to 3 |
| `tests/` | Automated tests and the review sentence set | Phase 1 onward |
| `data/` | Generated files, never committed | Phase 1 |

### Dependency rule

```
ui/  ──►  indicvoice/  ◄──  api/
              ▲
          scripts/, tests/, notebooks/
```
`indicvoice/` never imports from `api/` or `ui/`.

## 4. Configuration

### `config/languages.yaml`
```yaml
languages:
  odia:
    label: "Odia (ଓଡ଼ିଆ)"
    mt_code: "ory_Orya"
    script: "Oriya"
    default_voice: "female"
  hindi:
    label: "Hindi (हिन्दी)"
    mt_code: "hin_Deva"
    script: "Devanagari"
    default_voice: "female"
  bengali:
    label: "Bengali (বাংলা)"
    mt_code: "ben_Beng"
    script: "Bengali"
    default_voice: "female"
  # Phase 3: tamil=tam_Taml, telugu=tel_Telu, kannada=kan_Knda, malayalam=mal_Mlym,
  # marathi=mar_Deva, gujarati=guj_Gujr, punjabi=pan_Guru, assamese=asm_Beng
```

### `config/voices.yaml`
```yaml
# Speaker names must be taken from the Indic Parler-TTS model card (verify per language).
voices:
  female:
    odia:    "<speaker name from model card> speaks in a clear, moderately paced voice with a close recording and no background noise."
    hindi:   "<speaker name from model card> speaks in a clear, moderately paced voice with a close recording and no background noise."
    bengali: "<speaker name from model card> speaks in a clear, moderately paced voice with a close recording and no background noise."
  male:
    odia:    "<speaker name from model card> speaks in a clear, moderately paced voice with a close recording and no background noise."
    # ...
```
Using the same speaker name and description for every sentence keeps the voice consistent.

### `config/settings.yaml`
```yaml
max_chars: 2000
sentence_pause_ms: 250
cache_enabled: true
mt_batch_size: 8
mt_num_beams: 5
device: auto            # auto | cpu | cuda
```

### `.env.example`
```
HF_TOKEN=
HF_HOME=./.hf_cache
INDICVOICE_DEVICE=auto
```

## 5. Model Details

### Translator
- Checkpoint: `ai4bharat/indictrans2-en-indic-dist-200M`
- Needs `trust_remote_code=True` and `IndicTransToolkit` for pre/post-processing
- Source code `eng_Latn`; target codes from `languages.yaml`

### Synthesizer (Indic Parler-TTS)
- Checkpoint: `ai4bharat/indic-parler-tts`
- Two tokenizers: one for the **prompt** (the Indic text to speak) and one for the **description** (text encoder's tokenizer, from `model.config.text_encoder._name_or_path`)
- The language is inferred from the prompt text, so no language flag is passed
- Output rate comes from `model.config.sampling_rate`
- Weights are about 3.75 GB; set `HF_HOME` to a persistent folder so they are not re-downloaded
- If Hugging Face asks for access, accept the terms on the model page and set `HF_TOKEN`

### Wrapper interfaces
```python
class Translator:
    def translate(self, sentences: list[str], target_lang: str) -> list[str]: ...

class Synthesizer:
    def speak(self, text: str, language: str, voice: str = "female") -> tuple[np.ndarray, int]: ...
    # returns (waveform, sampling_rate)
```

## 6. Data Flow

1. Request arrives with `text`, `target_lang`, optional `voice`, optional `skip_translation`.
2. Preprocessor validates length, checks the script, splits into sentences.
3. Translator converts sentences in batches (skipped when `skip_translation` is true).
4. Synthesizer speaks each translated sentence using the voice description for that language.
5. Postprocessor joins chunks with a short pause, normalizes volume, saves WAV into `data/outputs/`.
6. Response returns translated text, audio path or URL, and timing.

## 7. API Design

### `POST /synthesize`
```json
{
  "text": "Welcome to Odisha.",
  "target_lang": "odia",
  "voice": "female",
  "skip_translation": false
}
```
Response:
```json
{
  "source_text": "Welcome to Odisha.",
  "translated_text": "...",
  "target_lang": "odia",
  "audio_url": "/audio/3f9a1c.wav",
  "duration_sec": 2.4,
  "cached": false,
  "failed_sentences": []
}
```

### `GET /languages` returns languages and voices from config.
### `GET /health` returns model load state and device.

| Code | Meaning |
|------|---------|
| 400 | Empty text, unsupported language, text over limit, script mismatch |
| 422 | Malformed body |
| 500 | Model failure |
| 503 | Models still loading |

## 8. Performance Strategy

| Concern | Approach |
|---------|----------|
| Startup time | Load models once at startup; show "loading" status |
| Memory | Distilled translator; `float16` on GPU if audio quality holds; free cache between requests if needed |
| Latency | Batch translation; synthesize per sentence |
| Repeat requests | Cache by `hash(text + lang + voice)` |
| Long text | Character limit and sentence chunking |
| Concurrency | One worker by default; queue if the GPU is shared |

## 9. Error Handling

- Per-sentence try/except with one retry; failures are listed in `failed_sentences`.
- Empty translation or empty audio counts as a failure.
- Request timeout to prevent hung GPU jobs.
- Clear, user-safe messages; details go to logs only.

## 10. `.gitignore` Essentials

```
.env
.hf_cache/
data/cache/*
data/outputs/*
data/review/*
!data/**/.gitkeep
__pycache__/
*.pyc
.ipynb_checkpoints/
.venv/
```

## 11. Setup Sequence

1. Create a virtual environment (Python 3.10+).
2. `pip install -r requirements.txt` (includes `parler-tts` pinned to a commit from GitHub).
3. Copy `.env.example` to `.env`; add `HF_TOKEN` if needed.
4. `python scripts/download_models.py` to pre-fetch weights.
5. Run `python -m indicvoice "Welcome to Odisha." --lang odia`.

## 12. Deployment Options

| Option | Pros | Cons |
|--------|------|------|
| Colab / Kaggle notebook | Free GPU, quickest start | Not a permanent service |
| Hugging Face Space | Free public demo, Gradio native | Free tier is CPU-only, slow |
| Local GPU machine | Full control | Needs hardware |
| Docker on own server | Reproducible | Needs a GPU host for good speed |

## 13. Testing Strategy

| Level | What |
|-------|------|
| Unit | Sentence splitting, config loading, cache keys, script check |
| Integration | Full pipeline on a 20-sentence set per language |
| Manual | Native-speaker review of translation and audio |
| Regression | Re-run the set after any model or library version change |

## 14. Licensing Checklist

Read and record in `memory.md` the license of: IndicTrans2, Indic Parler-TTS, `parler-tts`, `IndicTransToolkit`, and every Python dependency you redistribute. Do this before any public or commercial release.
