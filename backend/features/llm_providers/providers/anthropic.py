"""
Anthropic (Claude) provider implementation.
"""

import logging
import time
from typing import List
import anthropic

from .base import BaseLLMProvider, ModelInfo, ProviderAvailability
from ..models_config import get_models_by_provider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self):
        self._client = None
        self._cache: ProviderAvailability | None = None
        self._cache_timestamp = 0
        self._cache_duration = 5 * 60  # 5 minutes

        # Initialize Anthropic client safely
        try:
            self._client = (
                anthropic.Anthropic()
            )  # Uses ANTHROPIC_API_KEY from environment
            logger.info("Anthropic client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {e}")
            self._client = None

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def supported_models(self) -> List[ModelInfo]:
        """
        Get Anthropic models from centralized configuration.

        Models are loaded from the shared models-config.json file.
        """
        return get_models_by_provider("anthropic")

    def _is_cache_valid(self) -> bool:
        """Check if the current cache is still valid."""
        current_time = time.time()
        cache_age = current_time - self._cache_timestamp
        return cache_age < self._cache_duration and self._cache is not None

    def _get_cache_age(self) -> float:
        """Get the age of the current cache in seconds."""
        return time.time() - self._cache_timestamp

    async def check_availability(self) -> ProviderAvailability:
        """Check which Anthropic models are currently available."""

        # Return cached result if still fresh
        if self._is_cache_valid():
            logger.info("Returning cached Anthropic availability data")
            self._cache.cache_age_seconds = self._get_cache_age()
            self._cache.data_source = "cache"
            return self._cache

        # Check if client is available
        if self._client is None:
            logger.error("Anthropic client not initialized")
            return ProviderAvailability(
                provider_name=self.provider_name,
                is_available=False,
                models={},
                error_message="Anthropic client not initialized - API key missing",
                data_source="error",
            )

        try:
            # For Anthropic, we'll assume all our supported models are available
            # since they don't have a public models endpoint like OpenAI
            # We can test connectivity by making a simple request
            logger.debug("Testing Anthropic API connectivity...")

            # Test with a minimal request to verify API key and connectivity
            test_response = self._client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}],
            )

            logger.debug("Anthropic API connectivity test successful")

            # All supported models are considered available if API is accessible
            model_availability = {model.id: True for model in self.supported_models}

            # Create and cache result
            result = ProviderAvailability(
                provider_name=self.provider_name,
                is_available=True,
                models=model_availability,
                data_source="api",
                cache_age_seconds=0.0,
            )

            self._cache = result
            self._cache_timestamp = time.time()

            enabled_count = sum(model_availability.values())
            total_count = len(model_availability)

            logger.info(
                f"Updated Anthropic model availability from API",
                extra={
                    "provider": self.provider_name,
                    "enabled_count": enabled_count,
                    "total_count": total_count,
                    "models": model_availability,
                },
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to check Anthropic model availability: {e}",
                extra={"error_type": type(e).__name__, "error_message": str(e)},
            )

            return self.get_fallback_availability()

    def get_fallback_availability(self) -> ProviderAvailability:
        """Return fallback availability (all models enabled)."""
        fallback_models = {model.id: True for model in self.supported_models}

        logger.warning(
            "Returning fallback Anthropic availability (all enabled)",
            extra={
                "provider": self.provider_name,
                "models": fallback_models,
                "reason": "API error or client unavailable",
            },
        )

        return ProviderAvailability(
            provider_name=self.provider_name,
            is_available=True,  # Assume available for fallback
            models=fallback_models,
            error_message="Using fallback - API unavailable",
            data_source="fallback",
            cache_age_seconds=self._get_cache_age(),
        )
