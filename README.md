# IndicVoice 🎙️

**IndicVoice** translates English text into Indian languages (with **Odia** as the priority language, alongside Hindi, Bengali, and others) and speaks it as natural, high-quality audio.

It chains two open-source models without any fine-tuning or per-request API costs:
1. **Translation**: [IndicTrans2 (200M distilled)](https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M) (`ai4bharat/indictrans2-en-indic-dist-200M`)
2. **Speech Synthesis**: [Indic Parler-TTS](https://huggingface.co/ai4bharat/indic-parler-tts) (`ai4bharat/indic-parler-tts`)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Preprocess  │ ──► │  Translator  │ ──► │ Synthesizer  │ ──► │ Postprocess  │
│  Validation  │     │ IndicTrans2  │     │  Parler-TTS  │     │ Norm & Save  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 🚀 Key Features

- **End-to-End Pipeline**: Convert English text into natural Odia, Hindi, Bengali, or other Indic speech with a single call.
- **Priority Odia Support**: Specially tested with Odia script and voice presets.
- **Skip-Translation Mode**: Feed native script text directly to speech synthesis.
- **Script Mismatch Detection**: Automatic warning if Latin text is mistakenly supplied in skip-translation mode.
- **Sentence Chunking & Consistency**: Handles long paragraphs by splitting sentences and normalizing volume to avoid clipping or voice drift.
- **Voice Control**: Female and Male presets per language, plus custom natural language voice descriptions.
- **Hash-Keyed Caching**: Sub-millisecond response on identical repeated requests.
- **Three Interfaces**: CLI (`python -m indicvoice`), REST API (FastAPI), and Web UI (Gradio).

---

## 📋 System Requirements

- **OS**: Linux, macOS, or Windows
- **Python**: Python 3.10 or 3.11 (recommended)
- **Compute**:
  - **GPU**: NVIDIA GPU with 8GB+ VRAM recommended for fast inference.
  - **CPU**: Fully supported for local development and testing.

---

## 🛠️ Installation & Setup

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/your-username/indicvoice.git
cd indicvoice

# Create virtual environment with Python 3.11
py -3.11 -m venv .venv
source .venv/bin/activate       # Linux/macOS
# or: .venv\Scripts\activate    # Windows
```

### 2. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Hugging Face Access & Token Setup

`ai4bharat/indic-parler-tts` is a gated model.
1. Visit [ai4bharat/indic-parler-tts](https://huggingface.co/ai4bharat/indic-parler-tts) and accept the access terms.
2. Obtain your access token from [Hugging Face Settings](https://huggingface.co/settings/tokens).
3. Copy `.env.example` to `.env` and set your token:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
HF_TOKEN=hf_your_actual_token_here
HF_HOME=./.hf_cache
INDICVOICE_DEVICE=auto
```

### 4. (Optional) Pre-Download Models

Pre-fetch model weights into your cache before running:

```bash
python scripts/download_models.py
```

---

## 💻 CLI Usage

Translate and synthesize speech directly from the terminal:

```bash
# 1. Translate English into Odia and generate WAV
python -m indicvoice "Welcome to Odisha. Bhubaneswar is known as the temple city." --lang odia

# 2. Select Male voice preset and custom output file
python -m indicvoice "The sun rises in the east." --lang hindi --voice male --out sunrise.wav

# 3. Skip translation (direct Odia text to speech)
python -m indicvoice "ଓଡ଼ିଶା କୁ ସ୍ୱାଗତ ।" --lang odia --skip-translation

# 4. View supported languages
python -m indicvoice --list-languages
```

---

## 🌐 Web UI (Gradio)

Launch the interactive web interface:

```bash
python -m ui.app
```

Open your browser at `http://localhost:7860`.
Features:
- Live character counter (0 / 2,000 characters).
- Instant script mismatch warning if English text is entered in skip-translation mode.
- One-click sample sentences (Welcome message, Temple visit, Travel directions).
- Audio player with scrubber and WAV download.

---

## ⚡ REST API (FastAPI)

Start the REST API service:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check service health, active device, and model load status |
| `GET` | `/languages` | List supported languages, scripts, and voices |
| `POST` | `/synthesize` | Translate and synthesize speech |
| `GET` | `/audio/{filename}` | Download generated WAV audio file |

### Example Request (`POST /synthesize`)

```bash
curl -X POST "http://localhost:8000/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to Odisha.",
    "target_lang": "odia",
    "voice": "female",
    "skip_translation": false
  }'
```

Response:
```json
{
  "source_text": "Welcome to Odisha.",
  "translated_text": "ଓଡ଼ିଶା କୁ ସ୍ୱାଗତ ।",
  "target_lang": "odia",
  "audio_url": "/audio/odia_1727953200_a1b2c3d4.wav",
  "duration_sec": 2.45,
  "cached": false,
  "failed_sentences": []
}
```

---

## 🧪 Testing & Evaluation

Run unit and integration tests:

```bash
pytest tests/
```

Run test sentences and generate review audio:

```bash
python scripts/run_test_set.py --lang odia
```

Run latency and throughput benchmark:

```bash
python scripts/benchmark.py
```

---

## 🐳 Docker Deployment

Build and run with Docker:

```bash
docker build -t indicvoice:latest .
docker run -p 8000:8000 -p 7860:7860 -e HF_TOKEN="your_token" indicvoice:latest
```

---

## 📄 Licensing & Attribution

- **IndicVoice Codebase**: [Apache License 2.0](LICENSE)
- **IndicTrans2**: [ai4bharat/indictrans2-en-indic-dist-200M](https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M) — MIT License / CC-BY-4.0
- **Indic Parler-TTS**: [ai4bharat/indic-parler-tts](https://huggingface.co/ai4bharat/indic-parler-tts) — Apache License 2.0
- **Parler-TTS**: [huggingface/parler-tts](https://github.com/huggingface/parler-tts) — Apache License 2.0
