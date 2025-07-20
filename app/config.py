"""
Configuration management module
"""
import os
from typing import Optional

class Settings:
    """Application configuration class"""

    # Basic application configuration
    APP_NAME: str = "SentimentSense"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "HuggingFace-based sentiment analysis service"

    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Model configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "cardiffnlp/twitter-roberta-base-sentiment-latest")
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "512"))
    BATCH_SIZE_LIMIT: int = int(os.getenv("BATCH_SIZE_LIMIT", "10"))

    # Cache configuration
    ENABLE_MODEL_CACHE: bool = os.getenv("ENABLE_MODEL_CACHE", "true").lower() == "true"

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json or text
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")  # Optional log file path

    # Monitoring configuration
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))

    # Health check configuration
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))

    # Alert configuration
    ALERT_EMAIL: Optional[str] = os.getenv("ALERT_EMAIL")
    ALERT_SLACK_WEBHOOK: Optional[str] = os.getenv("ALERT_SLACK_WEBHOOK")

# Global configuration instance
settings = Settings()
