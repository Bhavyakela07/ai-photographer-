"""
Configuration settings for AI Virtual Photographer.

This module loads environment variables and provides
centralized configuration for all agents and services.

Supports both:
- Local development: .env file
- Streamlit Cloud: st.secrets
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (local development)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Try to import Streamlit secrets for cloud deployment
try:
    import streamlit as st
    _streamlit_secrets = dict(st.secrets) if hasattr(st, 'secrets') else {}
except:
    _streamlit_secrets = {}


def get_config(key: str, default: str = "") -> str:
    """Get config from environment or Streamlit secrets."""
    # Priority: Environment variable > Streamlit secrets > default
    return os.getenv(key, _streamlit_secrets.get(key, default))


class Settings:
    """
    Application settings loaded from environment variables or Streamlit secrets.
    
    All API keys and model configurations are centralized here
    to make it easy to swap models or update keys.
    """
    
    # ============================================
    # API Keys
    # ============================================
    GEMINI_API_KEY: str = get_config("GEMINI_API_KEY", "")
    
    # ============================================
    # Model IDs
    # ============================================
    # Text+Vision model for garment understanding
    # Options: gemini-2.0-flash-exp, gemini-3-pro-preview, gemini-1.5-pro
    TEXT_VISION_MODEL_ID: str = get_config(
        "GEMINI_TEXT_VISION_MODEL_ID", 
        "gemini-2.0-flash-exp"
    )
    
    # Image generation model
    # Options: 
    #   - imagen-3.0-generate-002 (highest quality, 1024px)
    #   - imagen-3.0-fast-generate-001 (faster, good quality)
    #   - gemini-2.0-flash-exp-image-generation (native, good for editing)
    IMAGE_MODEL_ID: str = get_config(
        "GEMINI_IMAGE_MODEL_ID", 
        "imagen-3.0-generate-002"
    )
    
    # Fallback native image generation model (used when Imagen fails)
    # Options: gemini-2.0-flash-preview-image-generation, gemini-2.0-flash-exp-image-generation
    NATIVE_IMAGE_MODEL_ID: str = get_config(
        "GEMINI_NATIVE_IMAGE_MODEL_ID",
        "gemini-2.0-flash-preview-image-generation"
    )
    
    # ============================================
    # Image Generation Quality Settings
    # ============================================
    
    # Aspect ratio for generated images
    # Options: "1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2"
    # "3:4" is ideal for full-body fashion photography (portrait)
    IMAGE_ASPECT_RATIO: str = get_config("IMAGE_ASPECT_RATIO", "3:4")
    
    # Number of images to generate (1-4), more options = better chance of good result
    IMAGE_COUNT: int = int(get_config("IMAGE_COUNT", "1"))
    
    # Enable prompt enhancement (LLM rewrites prompt for better results)
    # Set to "true" or "false"
    ENABLE_PROMPT_ENHANCEMENT: bool = get_config("ENABLE_PROMPT_ENHANCEMENT", "true").lower() == "true"
    
    # Safety filter level: "block_none", "block_only_high", "block_medium_and_above", "block_low_and_above"
    SAFETY_FILTER_LEVEL: str = get_config("SAFETY_FILTER_LEVEL", "block_only_high")
    
    # Add quality keywords to prompts automatically
    AUTO_QUALITY_KEYWORDS: bool = get_config("AUTO_QUALITY_KEYWORDS", "true").lower() == "true"
    
    # Quality keywords to add to prompts
    QUALITY_KEYWORDS: str = get_config(
        "QUALITY_KEYWORDS",
        "high-quality, 4K, ultra-detailed, professional photography, sharp focus, high resolution"
    )
    
    # ============================================
    # Generation Temperature Settings
    # ============================================
    # Lower = more consistent, higher = more creative
    ANALYSIS_TEMPERATURE: float = float(get_config("ANALYSIS_TEMPERATURE", "0.2"))
    GENERATION_TEMPERATURE: float = float(get_config("GENERATION_TEMPERATURE", "0.9"))
    
    # ============================================
    # Retry Settings
    # ============================================
    MAX_RETRIES: int = int(get_config("MAX_RETRIES", "3"))
    RETRY_DELAY_SECONDS: float = float(get_config("RETRY_DELAY_SECONDS", "1.0"))
    
    # ============================================
    # Legacy compatibility
    # ============================================
    IMAGE_WIDTH: int = int(get_config("IMAGE_WIDTH", "1024"))
    IMAGE_HEIGHT: int = int(get_config("IMAGE_HEIGHT", "1024"))
    
    @classmethod
    def validate(cls) -> bool:
        """
        Check if required settings are configured.
        
        Returns:
            True if all required settings are present, False otherwise.
        """
        if not cls.GEMINI_API_KEY:
            return False
        return True
    
    @classmethod
    def get_missing_config_message(cls) -> str:
        """
        Get a user-friendly message about missing configuration.
        
        Returns:
            String describing what's missing and how to fix it.
        """
        if not cls.GEMINI_API_KEY:
            return (
                "❌ GEMINI_API_KEY is not set!\n\n"
                "Please:\n"
                "1. Copy `.env.example` to `.env`\n"
                "2. Add your Gemini API key from https://aistudio.google.com/apikey\n"
                "3. Restart the application"
            )
        return "✅ Configuration is valid"
    
    @classmethod
    def get_quality_info(cls) -> str:
        """Get current quality settings as formatted string."""
        return f"""
📊 Current Quality Settings:
• Image Model: {cls.IMAGE_MODEL_ID}
• Aspect Ratio: {cls.IMAGE_ASPECT_RATIO}
• Prompt Enhancement: {'✅ Enabled' if cls.ENABLE_PROMPT_ENHANCEMENT else '❌ Disabled'}
• Auto Quality Keywords: {'✅ Enabled' if cls.AUTO_QUALITY_KEYWORDS else '❌ Disabled'}
• Safety Filter: {cls.SAFETY_FILTER_LEVEL}
• Generation Temperature: {cls.GENERATION_TEMPERATURE}
"""


# Create a singleton instance for easy import
settings = Settings()
