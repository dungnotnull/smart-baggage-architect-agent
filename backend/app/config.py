"""Application configuration via pydantic-settings."""

import os
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # App
    app_name: str = "Smart Baggage Architect"
    app_version: str = "0.1.0"
    auth_api_key: str = os.getenv("AUTH_API_KEY", "")
    auth_disabled: bool = os.getenv("AUTH_DISABLED", "true").lower() == "true"

    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # LLM Provider: "claude" | "openai" | "local"
    llm_provider: str = os.getenv("LLM_PROVIDER", "claude")

    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Phi-3-mini local model
    phi3_model_path: str = os.getenv("PHI3_MODEL_PATH", str(BASE_DIR / "models" / "phi3-mini-q4.gguf"))

    # Database
    db_path: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "smart_baggage.db"))
    db_encryption_key: str = os.getenv("DB_ENCRYPTION_KEY", "")

    # Weather API
    open_meteo_base_url: str = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1")

    # Geocoding
    geocoding_base_url: str = os.getenv("GEOCODING_BASE_URL", "https://geocoding-api.open-meteo.com/v1")

    # Airline policies directory
    airline_policies_dir: str = os.getenv("AIRLINE_POLICIES_DIR", str(BASE_DIR / "airline_policies"))

    # YOLO model paths
    yolov8_onnx_path: str = os.getenv("YOLOV8_ONNX_PATH", str(BASE_DIR / "models" / "yolov8n-travel.onnx"))
    yolov8_pt_path: str = os.getenv("YOLOV8_PT_PATH", str(BASE_DIR / "models" / "yolov8n-travel.pt"))

    # CLIP model
    clip_model_id: str = os.getenv("CLIP_MODEL_ID", "openai/clip-vit-base-patch32")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # CORS origins for React Native dev
    cors_origins: list[str] = ["*"]

    # LLM Provider config
    providers: dict[str, Any] = {
        "claude": {
            "model": "claude-sonnet-4-6",
            "api_key_env": "ANTHROPIC_API_KEY",
            "max_tokens": 2048,
            "temperature": 0.7,
        },
        "openai": {
            "model": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
            "max_tokens": 2048,
            "temperature": 0.7,
        },
        "local": {
            "model_path": str(BASE_DIR / "models" / "phi3-mini-q4.gguf"),
            "n_ctx": 4096,
            "n_gpu_layers": 0,
            "temperature": 0.7,
            "max_tokens": 512,
        },
    }

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
