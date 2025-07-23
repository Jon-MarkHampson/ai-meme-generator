import logging
import time
from typing import Dict
from openai import OpenAI

from .models import ModelAvailabilityResponse

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

# List of models to check (should match your frontend config - now includes Claude models)
MODELS_TO_CHECK = [
    # OpenAI Models
    "openai:gpt-4o",
    "openai:gpt-4.1-2025-04-14",
    "openai:gpt-4.1-mini",
    "openai:gpt-4.1-nano",
    "openai:o1-mini",
    # Anthropic Claude Models
    "anthropic:claude-sonnet-4-20250514",
    "anthropic:claude-3-7-sonnet-20250219",
    "anthropic:claude-3-5-sonnet-latest",
]


def get_fallback_availability() -> Dict[str, bool]:
    """Return fallback model availability (all models enabled)."""
    return {model_id: True for model_id in MODELS_TO_CHECK}


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
    availability = {}
    for model_id in MODELS_TO_CHECK:
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
