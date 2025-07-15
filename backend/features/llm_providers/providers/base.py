"""
Base classes for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Information about a specific model."""

    id: str
    name: str
    description: str
    capabilities: List[str] = []
    pricing: str = "unknown"
    speed: str = "unknown"
    max_tokens: int | None = None
    cost_per_1k_tokens: float | None = None


class ProviderAvailability(BaseModel):
    """Availability information for a provider."""

    provider_name: str
    is_available: bool
    models: Dict[str, bool]  # model_id -> availability
    error_message: str | None = None
    data_source: str = "unknown"  # api, cache, fallback
    cache_age_seconds: float = 0.0


class BaseLLMProvider(ABC):
    """Base class for all LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[ModelInfo]:
        """Return list of models this provider supports."""
        pass

    @abstractmethod
    async def check_availability(self) -> ProviderAvailability:
        """Check which models are currently available from this provider."""
        pass

    @abstractmethod
    def get_fallback_availability(self) -> ProviderAvailability:
        """Return fallback availability when API is unavailable."""
        pass
