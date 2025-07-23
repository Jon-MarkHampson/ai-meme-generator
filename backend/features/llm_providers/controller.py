"""
Model availability controller.
Handles API endpoints for checking AI model availability.
"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
import logging

from entities.user import User
from features.auth.service import get_current_user
from .multi_provider_service import get_model_availability, get_all_providers_availability
from .models import ModelAvailabilityResponse, LLMProvidersResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm_providers", tags=["llm_providers"])


@router.get("/availability", response_model=ModelAvailabilityResponse)
async def check_model_availability(
    current_user: User = Depends(get_current_user),
) -> ModelAvailabilityResponse:
    """
    Check which models are currently available from all providers.
    
    LEGACY ENDPOINT: Use /availability/detailed for full provider information.

    Returns:
        ModelAvailabilityResponse with combined availability data and metadata

    Raises:
        HTTPException: If service is unavailable
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
    Check detailed availability information from all providers.
    
    Returns provider-specific information including error states, cache status,
    and individual provider availability.

    Returns:
        LLMProvidersResponse with detailed provider information

    Raises:
        HTTPException: If service is unavailable
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
    Simplified endpoint that returns just the availability mapping.
    Compatible with existing frontend code.

    Returns:
        Dict mapping model IDs to availability status
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
    Debug endpoint to see all configured models and their availability.
    """
    try:
        from .multi_provider_service import get_fallback_availability, _openai_provider, _anthropic_provider
        
        # Get all supported models from providers
        openai_models = [{"id": m.id, "name": m.name} for m in _openai_provider.supported_models]
        anthropic_models = [{"id": m.id, "name": m.name} for m in _anthropic_provider.supported_models]
        
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
