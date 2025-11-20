"""
Configuration settings for MediaCleaner application
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "MediaCleaner"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Paths
    DATA_DIR: Path = Path("/data")  # Will be mounted from Unraid
    THUMBNAIL_DIR: Path = Path("/app/public/thumbnails")
    DATABASE_PATH: Path = Path("/app/data/mediacleaner.db")

    # Media Processing
    MIN_FILE_SIZE_MB: int = 300  # Ignore files smaller than this
    VIDEO_EXTENSIONS: list = [".mkv", ".mp4", ".avi", ".m4v", ".mov"]
    THUMBNAIL_TIMESTAMP_RATIO: float = 0.25  # Take screenshot at 25% of duration
    THUMBNAIL_WIDTH: int = 640  # Width of generated thumbnails

    # Performance
    MAX_CONCURRENT_SCANS: int = 4  # Number of concurrent ffprobe operations
    MAX_CONCURRENT_THUMBNAILS: int = 2  # Number of concurrent thumbnail generations

    # FFmpeg
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
