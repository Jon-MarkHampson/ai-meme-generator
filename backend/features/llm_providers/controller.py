"""
Model availability controller.
Handles API endpoints for checking AI model availability.
"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
import logging

from entities.user import User
from features.auth.service import get_current_user
from .service import get_model_availability
from .models import ModelAvailabilityResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm_providers", tags=["llm_providers"])


@router.get("/availability", response_model=ModelAvailabilityResponse)
async def check_model_availability(
    current_user: User = Depends(get_current_user),
) -> ModelAvailabilityResponse:
    """
    Check which OpenAI models are currently available.

    Returns:
        ModelAvailabilityResponse with availability data and metadata

    Raises:
        HTTPException: If service is unavailable
    """
    try:
        result = get_model_availability(current_user.id)
        return result

    except Exception as e:
        logger.error(f"Unexpected error in model availability endpoint: {e}")

        # If it's an OpenAI client issue, return 503
        if "API key" in str(e) or "OpenAI client not initialized" in str(e):
            raise HTTPException(
                status_code=503,
                detail="OpenAI service unavailable - API key not configured",
            )

        raise HTTPException(
            status_code=500,
            detail="Internal server error while checking model availability",
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
        from .service import get_fallback_availability

        return get_fallback_availability()
