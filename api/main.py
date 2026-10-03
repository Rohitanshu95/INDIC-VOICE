"""FastAPI main entrypoint with startup lifecycle and standard error formatting."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router
from indicvoice import __version__
from indicvoice.config import load_config
from indicvoice.pipeline import IndicVoicePipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("indicvoice.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle."""
    logger.info("Initializing IndicVoice API service...")
    config = load_config()
    pipeline = IndicVoicePipeline(config=config)

    # Attach to app state
    app.state.pipeline = pipeline
    logger.info(f"IndicVoice API ready on device '{pipeline.translator.device}'.")

    yield

    logger.info("Shutting down IndicVoice API service.")


app = FastAPI(
    title="IndicVoice API",
    description="English to Indian-language speech translation and synthesis pipeline (IndicTrans2 + Indic Parler-TTS).",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Ensure all HTTP exceptions adhere to consistent error JSON schema."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "Request error",
            "code": exc.status_code,
            "detail": str(exc.detail),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic schema validation errors into consistent error JSON."""
    errors = exc.errors()
    first_err = errors[0]["msg"] if errors else "Invalid request body."
    return JSONResponse(
        status_code=422,
        content={
            "error": f"Validation Error: {first_err}",
            "code": 422,
            "detail": str(errors),
        },
    )


# Register routes
app.include_router(router)


def run() -> None:
    """Entrypoint to run uvicorn server directly."""
    import os
    import uvicorn

    port = int(os.getenv("INDICVOICE_PORT", "8090"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    run()
