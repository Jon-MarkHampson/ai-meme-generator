"""
OpenAI provider implementation.
"""

import logging
import time
from typing import List
from openai import OpenAI

from .base import BaseLLMProvider, ModelInfo, ProviderAvailability

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""

    def __init__(self):
        self._client = None
        self._cache: ProviderAvailability | None = None
        self._cache_timestamp = 0
        self._cache_duration = 5 * 60  # 5 minutes

        # Initialize OpenAI client safely
        try:
            self._client = OpenAI()  # Uses OPENAI_API_KEY from environment
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            self._client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def supported_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="openai:gpt-4o",
                name="GPT-4o",
                description="Latest OpenAI model with vision capabilities",
                capabilities=["text", "vision", "reasoning"],
                pricing="high",
                speed="medium",
                max_tokens=128000,
                cost_per_1k_tokens=0.015,
            ),
            ModelInfo(
                id="openai:gpt-4.1-2025-04-14",
                name="GPT-4.1",
                description="Advanced reasoning model (April 2025)",
                capabilities=["text", "reasoning", "analysis"],
                pricing="high",
                speed="medium",
                max_tokens=200000,
                cost_per_1k_tokens=0.02,
            ),
            ModelInfo(
                id="openai:gpt-4.1-mini",
                name="GPT-4.1 Mini",
                description="Faster, cost-effective version",
                capabilities=["text", "reasoning"],
                pricing="medium",
                speed="fast",
                max_tokens=128000,
                cost_per_1k_tokens=0.008,
            ),
            ModelInfo(
                id="openai:gpt-4.1-nano",
                name="GPT-4.1 Nano",
                description="Ultra-fast for simple tasks",
                capabilities=["text"],
                pricing="low",
                speed="fast",
                max_tokens=64000,
                cost_per_1k_tokens=0.004,
            ),
            ModelInfo(
                id="openai:o1-mini",
                name="O1 Mini",
                description="Reasoning-focused model",
                capabilities=["reasoning", "analysis"],
                pricing="medium",
                speed="slow",
                max_tokens=128000,
                cost_per_1k_tokens=0.012,
            ),
        ]

    def _is_cache_valid(self) -> bool:
        """Check if the current cache is still valid."""
        current_time = time.time()
        cache_age = current_time - self._cache_timestamp
        return cache_age < self._cache_duration and self._cache is not None

    def _get_cache_age(self) -> float:
        """Get the age of the current cache in seconds."""
        return time.time() - self._cache_timestamp

    async def check_availability(self) -> ProviderAvailability:
        """Check which OpenAI models are currently available."""

        # Return cached result if still fresh
        if self._is_cache_valid():
            logger.info("Returning cached OpenAI availability data")
            self._cache.cache_age_seconds = self._get_cache_age()
            self._cache.data_source = "cache"
            return self._cache

        # Check if client is available
        if self._client is None:
            logger.error("OpenAI client not initialized")
            return ProviderAvailability(
                provider_name=self.provider_name,
                is_available=False,
                models={},
                error_message="OpenAI client not initialized - API key missing",
                data_source="error",
            )

        try:
            logger.debug("Calling OpenAI models.list() API...")
            models_response = self._client.models.list()
            available_model_ids = {model.id for model in models_response.data}

            logger.debug(f"OpenAI API returned {len(available_model_ids)} models")

            # Check availability for each supported model
            model_availability = {}
            for model_info in self.supported_models:
                # Remove "openai:" prefix for OpenAI API check
                openai_model_id = model_info.id.replace("openai:", "")
                is_available = openai_model_id in available_model_ids
                model_availability[model_info.id] = is_available

                logger.debug(
                    f"Model {model_info.id} ({openai_model_id}): {'available' if is_available else 'not available'}"
                )

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
                f"Updated OpenAI model availability from API",
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
                f"Failed to check OpenAI model availability: {e}",
                extra={"error_type": type(e).__name__, "error_message": str(e)},
            )

            return self.get_fallback_availability()

    def get_fallback_availability(self) -> ProviderAvailability:
        """Return fallback availability (all models enabled)."""
        fallback_models = {model.id: True for model in self.supported_models}

        logger.warning(
            "Returning fallback OpenAI availability (all enabled)",
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
