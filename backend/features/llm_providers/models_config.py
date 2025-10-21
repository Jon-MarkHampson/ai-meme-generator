"""
Centralized model configuration loader.

This module loads the shared models-config.json file and provides
it to the rest of the application. This ensures a single source of
truth for all AI model definitions.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict
from functools import lru_cache

from .providers.base import ModelInfo

logger = logging.getLogger(__name__)

# Path to the shared configuration file (project root)
CONFIG_FILE_PATH = Path(__file__).parent.parent.parent.parent / "models-config.json"


@lru_cache(maxsize=1)
def load_models_config() -> Dict:
    """
    Load and parse the models configuration file.

    This function is cached to avoid repeated file I/O operations.

    Returns:
        Dict containing the parsed JSON configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    logger.info(f"Loading models configuration from: {CONFIG_FILE_PATH}")

    if not CONFIG_FILE_PATH.exists():
        raise FileNotFoundError(
            f"Models configuration file not found at: {CONFIG_FILE_PATH}"
        )

    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)

    logger.info(
        f"Successfully loaded {len(config.get('models', []))} models from configuration"
    )

    return config


def get_all_models() -> List[ModelInfo]:
    """
    Get all model definitions from the configuration.

    Returns:
        List of ModelInfo objects for all configured models
    """
    config = load_models_config()
    models = []

    for model_data in config.get("models", []):
        model_info = ModelInfo(
            id=model_data["id"],
            name=model_data["name"],
            description=model_data["description"],
            capabilities=model_data.get("capabilities", []),
            pricing=model_data.get("pricing", "unknown"),
            speed=model_data.get("speed", "unknown"),
            max_tokens=model_data.get("maxTokens"),
            cost_per_1k_tokens=model_data.get("costPer1kTokens"),
        )
        models.append(model_info)

    return models


def get_models_by_provider(provider: str) -> List[ModelInfo]:
    """
    Get model definitions for a specific provider.

    Args:
        provider: Provider name (e.g., "openai", "anthropic")

    Returns:
        List of ModelInfo objects for the specified provider
    """
    config = load_models_config()
    models = []

    for model_data in config.get("models", []):
        if model_data.get("provider") == provider:
            model_info = ModelInfo(
                id=model_data["id"],
                name=model_data["name"],
                description=model_data["description"],
                capabilities=model_data.get("capabilities", []),
                pricing=model_data.get("pricing", "unknown"),
                speed=model_data.get("speed", "unknown"),
                max_tokens=model_data.get("maxTokens"),
                cost_per_1k_tokens=model_data.get("costPer1kTokens"),
            )
            models.append(model_info)

    logger.debug(
        f"Found {len(models)} models for provider '{provider}': "
        f"{[m.id for m in models]}"
    )

    return models


def get_model_by_id(model_id: str) -> ModelInfo | None:
    """
    Get a specific model by its ID.

    Args:
        model_id: Model ID (e.g., "openai:gpt-4o")

    Returns:
        ModelInfo object if found, None otherwise
    """
    config = load_models_config()

    for model_data in config.get("models", []):
        if model_data["id"] == model_id:
            return ModelInfo(
                id=model_data["id"],
                name=model_data["name"],
                description=model_data["description"],
                capabilities=model_data.get("capabilities", []),
                pricing=model_data.get("pricing", "unknown"),
                speed=model_data.get("speed", "unknown"),
                max_tokens=model_data.get("maxTokens"),
                cost_per_1k_tokens=model_data.get("costPer1kTokens"),
            )

    return None


def get_enabled_models() -> List[ModelInfo]:
    """
    Get all enabled model definitions.

    Returns:
        List of ModelInfo objects for enabled models
    """
    config = load_models_config()
    models = []

    for model_data in config.get("models", []):
        if model_data.get("isEnabled", True):
            model_info = ModelInfo(
                id=model_data["id"],
                name=model_data["name"],
                description=model_data["description"],
                capabilities=model_data.get("capabilities", []),
                pricing=model_data.get("pricing", "unknown"),
                speed=model_data.get("speed", "unknown"),
                max_tokens=model_data.get("maxTokens"),
                cost_per_1k_tokens=model_data.get("costPer1kTokens"),
            )
            models.append(model_info)

    return models


def get_default_model() -> ModelInfo | None:
    """
    Get the default model from configuration.

    Returns:
        ModelInfo object for the default model, or None if not found
    """
    config = load_models_config()

    for model_data in config.get("models", []):
        if model_data.get("isDefault", False):
            return ModelInfo(
                id=model_data["id"],
                name=model_data["name"],
                description=model_data["description"],
                capabilities=model_data.get("capabilities", []),
                pricing=model_data.get("pricing", "unknown"),
                speed=model_data.get("speed", "unknown"),
                max_tokens=model_data.get("maxTokens"),
                cost_per_1k_tokens=model_data.get("costPer1kTokens"),
            )

    return None


def get_raw_config() -> Dict:
    """
    Get the raw configuration dictionary.

    This is useful for endpoints that need to return the complete
    configuration including metadata like isDefault and isEnabled.

    Returns:
        Dict containing the raw configuration
    """
    return load_models_config()
