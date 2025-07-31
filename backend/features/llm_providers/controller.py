"""
LLM provider controller managing AI model availability and configuration endpoints.

This module provides HTTP endpoints for checking AI model availability across
multiple providers (OpenAI, Anthropic), enabling dynamic model selection in
the frontend based on real-time service status and API key configuration.

Key features:
- Multi-provider model availability checking with caching
- Detailed provider status information including error states
- Simple availability mapping for frontend model selection
- Debug endpoints for development and troubleshooting
- Graceful fallback handling when services are unavailable

Architecture context:
The system supports multiple AI providers to ensure reliability and provide
users with model choice. This controller exposes the availability checking
logic that powers dynamic model selection in the generation interface.

Provider support:
- OpenAI: GPT-4, GPT-3.5-turbo, and other OpenAI models
- Anthropic: Claude models including Sonnet and Haiku variants
- Extensible design for adding additional providers

Security considerations:
- All endpoints require authenticated users
- API key validation happens at the service layer
- Provider errors are sanitized before client exposure
- Debug endpoints provide safe troubleshooting information
"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
import logging

from entities.user import User
from features.auth.service import get_current_user
from .multi_provider_service import (
    get_model_availability,
    get_all_providers_availability,
)
from .models import ModelAvailabilityResponse, LLMProvidersResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm_providers", tags=["llm_providers"])


@router.get("/availability", response_model=ModelAvailabilityResponse)
async def check_model_availability(
    current_user: User = Depends(get_current_user),
) -> ModelAvailabilityResponse:
    """
    Check model availability across all configured AI providers.
    
    This endpoint aggregates availability information from all configured
    providers (OpenAI, Anthropic) and returns a unified response with
    model availability status, metadata, and caching information.
    
    Args:
        current_user: Authenticated user from JWT token validation
        
    Returns:
        ModelAvailabilityResponse: Combined availability data with metadata including:
        - availability: Dict mapping model IDs to boolean availability
        - enabled_count: Number of currently available models
        - total_count: Total number of configured models
        - data_source: Whether data is from cache or live check
        
    Raises:
        HTTPException: 503 if API keys not configured, 500 for other errors
        
    Caching behavior:
        Results are cached to reduce API calls and improve performance.
        Cache duration varies by provider response status.
        
    Legacy note:
        This endpoint provides basic availability information.
        Use /availability/detailed for comprehensive provider status.
    """
    try:
        result = get_model_availability(current_user.id)
        return result

    except Exception as e:
        logger.error(f"Unexpected error in model availability endpoint: {e}")

        # If it's an API key issue, return 503
        if "API key" in str(e) or "client not initialized" in str(e):
            raise HTTPException(
                status_code=503,
                detail="LLM service unavailable - API keys not configured",
            )

        raise HTTPException(
            status_code=500,
            detail="Internal server error while checking model availability",
        )


@router.get("/availability/detailed", response_model=LLMProvidersResponse)
async def check_detailed_model_availability(
    current_user: User = Depends(get_current_user),
) -> LLMProvidersResponse:
    """
    Retrieve comprehensive provider status and model availability details.
    
    This endpoint provides in-depth information about each AI provider's
    status, including individual provider availability, error conditions,
    cache status, and detailed model information. Used for troubleshooting
    and comprehensive frontend status displays.
    
    Args:
        current_user: Authenticated user from JWT token validation
        
    Returns:
        LLMProvidersResponse: Detailed provider information including:
        - providers: Dict with per-provider status and available models
        - combined_availability: Unified availability mapping
        - cache_info: Caching status and timing information
        - error_details: Provider-specific error information when applicable
        
    Raises:
        HTTPException: 500 for internal server errors during status checking
        
    Usage context:
        - Administrative interfaces showing provider health
        - Troubleshooting model availability issues
        - Frontend dashboards displaying detailed service status
        
    Technical details:
        Performs individual checks against each provider's API to gather
        real-time status information and model availability.
    """
    try:
        result = await get_all_providers_availability(current_user.id)
        return result

    except Exception as e:
        logger.error(f"Unexpected error in detailed model availability endpoint: {e}")

        raise HTTPException(
            status_code=500,
            detail="Internal server error while checking detailed model availability",
        )


@router.get("/availability/simple")
async def check_model_availability_simple(
    current_user: User = Depends(get_current_user),
) -> Dict[str, bool]:
    """
    Get simple model availability mapping for frontend model selection.
    
    This endpoint returns only the essential availability information in
    a simple dictionary format, making it easy for frontend components
    to determine which models are available for selection.
    
    Args:
        current_user: Authenticated user from JWT token validation
        
    Returns:
        Dict[str, bool]: Simple mapping of model IDs to availability status
        
    Error handling:
        Returns fallback availability mapping on any error to ensure
        the frontend always receives usable model selection data.
        
    Usage context:
        - Model selection dropdowns in generation interfaces
        - Quick availability checks without detailed metadata
        - Legacy frontend code requiring simple format
        
    Reliability:
        Designed for maximum reliability - always returns a valid response
        even when underlying services are experiencing issues.
    """
    try:
        result = get_model_availability(current_user.id)
        return result.availability

    except Exception as e:
        logger.error(f"Error in simple model availability endpoint: {e}")
        # Return fallback on any error
        from .multi_provider_service import get_fallback_availability

        return get_fallback_availability()


@router.get("/debug/models", response_model=None)
async def debug_models(
    current_user: User = Depends(get_current_user),
):
    """
    Debug endpoint providing comprehensive model configuration and status information.
    
    This development endpoint exposes detailed information about all configured
    models, their availability status, and provider configuration. Useful for
    troubleshooting model selection issues and verifying system configuration.
    
    Args:
        current_user: Authenticated user from JWT token validation
        
    Returns:
        Dict containing:
        - openai_models: List of configured OpenAI models with IDs and names
        - anthropic_models: List of configured Anthropic models with IDs and names
        - current_availability: Real-time availability status
        - fallback_availability: Default availability mapping
        - data_source: Whether current data is cached or live
        - total_available: Count of currently available models
        - total_models: Count of all configured models
        
    Error handling:
        Returns error information in response rather than raising exceptions
        to provide maximum debugging information even during failure states.
        
    Security note:
        This endpoint is intended for development and debugging. Consider
        restricting access in production environments.
        
    Usage context:
        - Development troubleshooting
        - System configuration verification
        - Model availability debugging
    """
    try:
        from .multi_provider_service import (
            get_fallback_availability,
            _openai_provider,
            _anthropic_provider,
        )

        # Get all supported models from providers
        openai_models = [
            {"id": m.id, "name": m.name} for m in _openai_provider.supported_models
        ]
        anthropic_models = [
            {"id": m.id, "name": m.name} for m in _anthropic_provider.supported_models
        ]

        # Get current availability
        availability_result = get_model_availability(current_user.id)

        return {
            "openai_models": openai_models,
            "anthropic_models": anthropic_models,
            "current_availability": availability_result.availability,
            "fallback_availability": get_fallback_availability(),
            "data_source": availability_result.data_source,
            "total_available": availability_result.enabled_count,
            "total_models": availability_result.total_count,
        }

    except Exception as e:
        logger.error(f"Error in debug models endpoint: {e}")
        return {"error": str(e)}
