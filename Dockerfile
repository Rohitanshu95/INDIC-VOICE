# Use official Python 3.11 slim image
FROM python:3.11-slim

# Prevent interactive prompts and configure python environment
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/.hf_cache

# Install required system packages (git for parler-tts, libsndfile for audio I/O)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for efficient layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application codebase
COPY config/ ./config/
COPY indicvoice/ ./indicvoice/
COPY api/ ./api/
COPY ui/ ./ui/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY pyproject.toml README.md LICENSE ./

# Pre-create data directories
RUN mkdir -p data/cache data/outputs data/review .hf_cache

# Expose ports for FastAPI (8000) and Gradio UI (7860)
EXPOSE 8000
EXPOSE 7860

# Default command starts the FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
