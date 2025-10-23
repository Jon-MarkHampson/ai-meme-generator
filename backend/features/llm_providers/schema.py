from typing import Dict, List

from pydantic import BaseModel

from .providers.base import ModelInfo, ProviderAvailability


class LLMProvidersResponse(BaseModel):
    """Response model for LLM providers availability endpoint."""

    providers: List[ProviderAvailability]
    combined_models: Dict[str, bool]  # All models from all providers
    total_providers: int
    available_providers: int
    total_models: int
    available_models: int
    data_sources: List[str]  # List of data sources used


class ModelAvailabilityResponse(BaseModel):
    """Legacy response model for backward compatibility."""

    availability: Dict[str, bool]
    data_source: str
    cache_age_seconds: float
    enabled_count: int
    total_count: int


class ModelConfigInfo(BaseModel):
    """Information about a model configuration."""

    id: str
    name: str
    description: str
    is_available: bool
    is_enabled: bool
    pricing: str
    speed: str
    capabilities: List[str]
    max_tokens: int | None = None
    cost_per_1k_tokens: float | None = None
    provider: str


class ModelDefinition(BaseModel):
    """Complete model definition from configuration."""

    id: str
    name: str
    provider: str
    description: str
    capabilities: List[str]
    pricing: str
    speed: str
    is_enabled: bool
    is_default: bool
    max_tokens: int | None = None
    cost_per_1k_tokens: float | None = None


class ModelListResponse(BaseModel):
    """Response model for the models list endpoint."""

    models: List[ModelDefinition]
    total_count: int
    enabled_count: int
    default_model_id: str | None = None
