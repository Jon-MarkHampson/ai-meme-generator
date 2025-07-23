"""
Multi-provider LLM service that consolidates OpenAI and Anthropic availability.
"""

import logging
import time
from typing import Dict
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .models import LLMProvidersResponse, ModelAvailabilityResponse

logger = logging.getLogger(__name__)

# Global provider instances
_openai_provider = OpenAIProvider()
_anthropic_provider = AnthropicProvider()

# Legacy cache for backward compatibility
_legacy_cache: Dict[str, bool] = {}
_legacy_cache_timestamp = 0
CACHE_DURATION = 5 * 60  # 5 minutes in seconds


async def get_all_providers_availability(user_id: str) -> LLMProvidersResponse:
    """
    Get availability from all providers and combine the results.
    
    Args:
        user_id: ID of the requesting user (for logging)
        
    Returns:
        LLMProvidersResponse with combined availability data
    """
    logger.info(f"Checking availability for all providers (user: {user_id})")
    
    # Check availability from all providers
    openai_availability = await _openai_provider.check_availability()
    anthropic_availability = await _anthropic_provider.check_availability()
    
    providers = [openai_availability, anthropic_availability]
    
    # Combine all models from all providers
    combined_models = {}
    combined_models.update(openai_availability.models)
    combined_models.update(anthropic_availability.models)
    
    # Calculate statistics
    available_providers = sum(1 for p in providers if p.is_available)
    total_models = len(combined_models)
    available_models = sum(combined_models.values())
    
    # Collect data sources
    data_sources = list(set(p.data_source for p in providers))
    
    logger.info(
        f"Multi-provider availability check complete",
        extra={
            "user_id": user_id,
            "total_providers": len(providers),
            "available_providers": available_providers,
            "total_models": total_models,
            "available_models": available_models,
            "data_sources": data_sources,
        }
    )
    
    return LLMProvidersResponse(
        providers=providers,
        combined_models=combined_models,
        total_providers=len(providers),
        available_providers=available_providers,
        total_models=total_models,
        available_models=available_models,
        data_sources=data_sources,
    )


def get_model_availability(user_id: str) -> ModelAvailabilityResponse:
    """
    Legacy endpoint that returns combined availability in the old format.
    This maintains backward compatibility with existing frontend code.
    
    Args:
        user_id: ID of the requesting user (for logging)
        
    Returns:
        ModelAvailabilityResponse with combined availability data
    """
    global _legacy_cache, _legacy_cache_timestamp
    
    current_time = time.time()
    cache_age = current_time - _legacy_cache_timestamp
    cache_valid = cache_age < CACHE_DURATION and bool(_legacy_cache)
    
    logger.info(
        f"Legacy model availability check requested by user {user_id}",
        extra={
            "cache_age": cache_age,
            "cache_duration": CACHE_DURATION,
            "is_cache_valid": cache_valid,
            "has_cached_data": bool(_legacy_cache),
        },
    )
    
    # Return cached result if still fresh
    if cache_valid:
        logger.info(
            "Returning cached legacy model availability data",
            extra={"data_source": "cache", "availability": _legacy_cache},
        )
        
        return ModelAvailabilityResponse(
            availability=_legacy_cache,
            data_source="cache",
            cache_age_seconds=cache_age,
            enabled_count=sum(_legacy_cache.values()),
            total_count=len(_legacy_cache),
        )
    
    # Get fresh data from all providers
    logger.info("Fetching fresh model availability from all providers...")
    
    try:
        # Get availability from both providers synchronously for the legacy endpoint
        import asyncio
        
        async def fetch_all():
            openai_availability = await _openai_provider.check_availability()
            anthropic_availability = await _anthropic_provider.check_availability()
            return openai_availability, anthropic_availability
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            openai_availability, anthropic_availability = loop.run_until_complete(fetch_all())
        finally:
            loop.close()
        
        # Combine availability data
        combined_availability = {}
        combined_availability.update(openai_availability.models)
        combined_availability.update(anthropic_availability.models)
        
        # Update legacy cache
        _legacy_cache = combined_availability
        _legacy_cache_timestamp = current_time
        
        logger.info(
            f"Updated legacy model availability cache with data from all providers",
            extra={
                "openai_models": len(openai_availability.models),
                "anthropic_models": len(anthropic_availability.models),
                "total_models": len(combined_availability),
                "enabled_count": sum(combined_availability.values()),
            }
        )
        
        return ModelAvailabilityResponse(
            availability=combined_availability,
            data_source="multi_provider_api",
            cache_age_seconds=0.0,
            enabled_count=sum(combined_availability.values()),
            total_count=len(combined_availability),
        )
        
    except Exception as e:
        logger.error(
            f"Failed to check model availability from providers: {e}",
            extra={"error_type": type(e).__name__, "error_message": str(e)},
        )
        
        # Return fallback combining both providers
        fallback = get_fallback_availability()
        
        logger.warning(
            "Returning fallback model availability (all enabled)",
            extra={
                "data_source": "fallback",
                "availability": fallback,
                "reason": "Provider APIs error",
            },
        )
        
        return ModelAvailabilityResponse(
            availability=fallback,
            data_source="fallback",
            cache_age_seconds=cache_age,
            enabled_count=sum(fallback.values()),
            total_count=len(fallback),
        )


def get_fallback_availability() -> Dict[str, bool]:
    """Return fallback model availability (all models enabled from all providers)."""
    fallback = {}
    
    # Add OpenAI models
    for model in _openai_provider.supported_models:
        fallback[model.id] = True
    
    # Add Anthropic models
    for model in _anthropic_provider.supported_models:
        fallback[model.id] = True
    
    return fallback
