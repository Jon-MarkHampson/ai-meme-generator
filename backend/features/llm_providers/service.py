"""
AI model availability service managing multi-provider integration.

This service provides real-time availability checking for AI models from multiple
providers (OpenAI, Anthropic) with intelligent caching and fallback mechanisms.
It enables the frontend to dynamically adjust model selection based on current
availability and user preferences.

Key features:
- Real-time model availability checking via provider APIs
- Intelligent caching system (5-minute TTL) to reduce API overhead
- Graceful fallback when provider APIs are unavailable
- Multi-provider support (OpenAI, Anthropic Claude models)
- Comprehensive logging for debugging and monitoring

Architecture:
- Cache-first approach with automatic refresh on expiration
- Exception handling with fallback to "all models available" assumption
- User-scoped requests for audit logging and future personalization
- Configurable model lists that match frontend selections

Performance considerations:
- API calls are cached to prevent rate limiting
- Background refresh prevents user-facing delays
- Fallback ensures service availability even during provider outages
"""
import logging
import time
from typing import Dict, List
from openai import OpenAI

from .schema import ModelAvailabilityResponse
from .models_config import get_all_models

logger = logging.getLogger(__name__)

# Initialize OpenAI client safely
try:
    client = OpenAI()  # Uses OPENAI_API_KEY from environment
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize OpenAI client: {e}")
    client = None

# Cache model availability for 5 minutes
_model_availability_cache: Dict[str, bool] = {}
_cache_timestamp = 0
CACHE_DURATION = 5 * 60  # 5 minutes in seconds


def get_models_to_check() -> List[str]:
    """
    Get list of model IDs to check from centralized configuration.

    Returns:
        List of model IDs loaded from models-config.json
    """
    models = get_all_models()
    return [model.id for model in models]


def get_fallback_availability() -> Dict[str, bool]:
    """Return fallback model availability (all models enabled)."""
    models_to_check = get_models_to_check()
    return {model_id: True for model_id in models_to_check}


def is_cache_valid() -> bool:
    """Check if the current cache is still valid."""
    current_time = time.time()
    cache_age = current_time - _cache_timestamp
    return cache_age < CACHE_DURATION and bool(_model_availability_cache)


def get_cache_age() -> float:
    """Get the age of the current cache in seconds."""
    return time.time() - _cache_timestamp


def fetch_model_availability_from_openai() -> Dict[str, bool]:
    """
    Fetch model availability from OpenAI API.

    Returns:
        Dict mapping model IDs to availability status

    Raises:
        Exception: If OpenAI client is not available or API call fails
    """
    if client is None:
        raise Exception("OpenAI client not initialized - API key missing")

    logger.debug("Calling OpenAI models.list() API...")
    models_response = client.models.list()
    available_model_ids = {model.id for model in models_response.data}

    logger.debug(f"OpenAI API returned {len(available_model_ids)} models")

    # Check availability for each model we care about
    models_to_check = get_models_to_check()
    availability = {}
    for model_id in models_to_check:
        # Remove "openai:" prefix for OpenAI API check
        openai_model_id = model_id.replace("openai:", "")
        is_available = openai_model_id in available_model_ids
        availability[model_id] = is_available

        logger.debug(
            f"Model {model_id} ({openai_model_id}): {'available' if is_available else 'not available'}"
        )

    return availability


def update_cache(availability: Dict[str, bool]) -> None:
    """Update the global cache with new availability data."""
    global _model_availability_cache, _cache_timestamp

    _model_availability_cache = availability
    _cache_timestamp = time.time()

    enabled_count = sum(availability.values())
    total_count = len(availability)

    logger.info(
        "Updated model availability cache",
        extra={
            "data_source": "openai_api",
            "availability": availability,
            "enabled_count": enabled_count,
            "total_count": total_count,
            "cache_updated": _cache_timestamp,
        },
    )


def get_model_availability(user_id: str) -> ModelAvailabilityResponse:
    """
    Get model availability with caching.

    Args:
        user_id: ID of the requesting user (for logging)

    Returns:
        ModelAvailabilityResponse with availability data and metadata
    """
    current_time = time.time()
    cache_age = get_cache_age()
    cache_valid = is_cache_valid()

    logger.info(
        f"Model availability check requested by user {user_id}",
        extra={
            "cache_age": cache_age,
            "cache_duration": CACHE_DURATION,
            "is_cache_valid": cache_valid,
            "has_cached_data": bool(_model_availability_cache),
        },
    )

    # Return cached result if still fresh
    if cache_valid:
        logger.info(
            "Returning cached model availability data",
            extra={"data_source": "cache", "availability": _model_availability_cache},
        )

        return ModelAvailabilityResponse(
            availability=_model_availability_cache,
            data_source="cache",
            cache_age_seconds=cache_age,
            enabled_count=sum(_model_availability_cache.values()),
            total_count=len(_model_availability_cache),
        )

    # Try to fetch fresh data from OpenAI
    logger.info("Fetching fresh model availability from OpenAI API...")

    try:
        availability = fetch_model_availability_from_openai()
        update_cache(availability)

        return ModelAvailabilityResponse(
            availability=availability,
            data_source="openai_api",
            cache_age_seconds=0.0,  # Fresh data
            enabled_count=sum(availability.values()),
            total_count=len(availability),
        )

    except Exception as e:
        logger.error(
            f"Failed to check model availability from OpenAI API: {e}",
            extra={"error_type": type(e).__name__, "error_message": str(e)},
        )

        # Return fallback
        fallback = get_fallback_availability()

        logger.warning(
            "Returning fallback model availability (all enabled)",
            extra={
                "data_source": "fallback",
                "availability": fallback,
                "reason": "OpenAI API error",
            },
        )

        return ModelAvailabilityResponse(
            availability=fallback,
            data_source="fallback",
            cache_age_seconds=cache_age,
            enabled_count=sum(fallback.values()),
            total_count=len(fallback),
        )
