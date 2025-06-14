"""
Configuration and settings for the Text-to-CAD API
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Settings
    api_title: str = "Text-to-CAD API"
    api_description: str = "Generate 3D CAD models from text descriptions"
    api_version: str = "1.0.0"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS Settings
    cors_origins: list[str] = Field(default=["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])
    
    # Gemini AI Settings
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.5-flash-preview-04-17"
    
    # User Limits
    max_models_per_user: int = 10
    
    # File Storage
    temp_dir: str = Field(default_factory=lambda: os.path.join(os.path.expanduser("~"), ".text-to-cad", "temp"))
    # Analytics service handles all user data now - no more JSON file needed
    analytics_url: str = Field(default="http://analytics:8001", env="ANALYTICS_URL")
    
    # Security Settings (for future implementation)
    enable_auth: bool = False
    admin_api_key: Optional[str] = None
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create temp directory if it doesn't exist
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


# BadCAD availability check
try:
    import badcad
    from badcad import *
    BADCAD_AVAILABLE = True
    print("✅ BadCAD successfully imported")
except ImportError as e:
    print(f"❌ BadCAD import failed: {e}")
    BADCAD_AVAILABLE = False


# Gemini client initialization
try:
    from google import genai
    if settings.gemini_api_key:
        gemini_client = genai.Client(api_key=settings.gemini_api_key)
        GEMINI_AVAILABLE = True
        print("✅ Gemini client initialized")
    else:
        print("⚠️ GEMINI_API_KEY not set")
        gemini_client = None
        GEMINI_AVAILABLE = False
except ImportError as e:
    print(f"❌ Gemini import failed: {e}")
    GEMINI_AVAILABLE = False
    gemini_client = None