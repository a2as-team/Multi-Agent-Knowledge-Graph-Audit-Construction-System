"""
Configuration utilities for the application.
Handles LLM model configuration and API keys.
"""
import os
from dotenv import load_dotenv, find_dotenv

from src.utils.logger import logger


def load_env():
    """Load environment variables from .env file."""
    try:
        env_path = find_dotenv()
        if env_path:
            load_dotenv(env_path, override=True)
        else:
            # Try to load from project root
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file, override=True)
    except Exception as e:
        logger.warning(f"Could not load .env file: {e}")


# Load environment variables
load_env()


# Gemini Model Constants
# Available models (verified via API):
MODEL_GEMINI_FLASH = "gemini/gemini-2.5-flash"  # Latest stable flash model
MODEL_GEMINI_PRO = "gemini/gemini-2.5-pro"      # Latest stable pro model

# Alternative models:
MODEL_GEMINI_FLASH_20 = "gemini/gemini-2.0-flash"  # Gemini 2.0 Flash
MODEL_GEMINI_FLASH_EXP = "gemini/gemini-2.0-flash-exp"  # Experimental
MODEL_GEMINI_FLASH_LITE = "gemini/gemini-2.0-flash-lite"  # Lite version

# Default model to use
DEFAULT_MODEL = MODEL_GEMINI_FLASH  # Using gemini-2.5-flash (latest stable)


def get_gemini_api_key() -> str:
    """
    Get the Gemini API key from environment variables.
    
    Returns:
        API key string
        
    Raises:
        ValueError: If API key is not found
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )
    return api_key


def get_neo4j_import_dir():
    """
    Gets the neo4j import directory from an environment variable.
    
    Returns:
        Path string or None if not set
    """
    return os.getenv("NEO4J_IMPORT_DIR")

