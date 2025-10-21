import API from "@/services/api";
import { ModelConfig } from '@/types/models';
import { AI_MODELS } from '@/config/ai-models';

// Cache for model definitions from backend
let modelsDefinitionCache: ModelConfig[] = [];
let modelsDefinitionCacheTimestamp = 0;

// Cache for dynamic model availability
let modelAvailabilityCache: { [key: string]: boolean } = {};
let lastCacheUpdate = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Backend response types
interface ModelDefinition {
  id: string;
  name: string;
  provider: string;
  description: string;
  capabilities: string[];
  pricing: string;
  speed: string;
  is_enabled: boolean;
  is_default: boolean;
  max_tokens?: number;
  cost_per_1k_tokens?: number;
}

interface ModelListResponse {
  models: ModelDefinition[];
  total_count: number;
  enabled_count: number;
  default_model_id?: string;
}

/**
 * Fetch model definitions from backend.
 *
 * This fetches the centralized model configuration from the backend
 * endpoint which reads from models-config.json. Falls back to local
 * AI_MODELS if backend is unavailable.
 */
export async function fetchModelsFromBackend(): Promise<ModelConfig[]> {
  const now = Date.now();
  const cacheAge = now - modelsDefinitionCacheTimestamp;
  const isCacheValid = cacheAge < CACHE_DURATION && modelsDefinitionCache.length > 0;

  console.log("🔍 [ModelDefinitions] Fetching model definitions...", {
    timestamp: new Date().toISOString(),
    cacheAge: `${Math.round(cacheAge / 1000)}s`,
    hasCachedData: modelsDefinitionCache.length > 0,
    isCacheValid,
  });

  // Return cached result if still fresh
  if (isCacheValid) {
    console.log("✅ [ModelDefinitions] Using cached definitions", {
      source: "cache",
      count: modelsDefinitionCache.length,
    });
    return modelsDefinitionCache;
  }

  console.log("🌐 [ModelDefinitions] Fetching from backend /llm_providers/models...");

  try {
    const response = await API.get<ModelListResponse>("/llm_providers/models");
    const backendModels = response.data.models;

    console.log("✅ [ModelDefinitions] Backend response received:", {
      totalModels: response.data.total_count,
      enabledModels: response.data.enabled_count,
      defaultModel: response.data.default_model_id,
    });

    // Convert backend format to frontend ModelConfig format
    const modelConfigs: ModelConfig[] = backendModels.map((model) => ({
      id: model.id,
      name: model.name,
      description: model.description,
      capabilities: model.capabilities,
      pricing: model.pricing as "low" | "medium" | "high",
      speed: model.speed as "fast" | "medium" | "slow",
      isEnabled: model.is_enabled,
      isDefault: model.is_default,
      maxTokens: model.max_tokens,
      costPer1kTokens: model.cost_per_1k_tokens,
    }));

    // Update cache
    modelsDefinitionCache = modelConfigs;
    modelsDefinitionCacheTimestamp = now;

    console.log("✅ [ModelDefinitions] Cached backend models:", {
      count: modelConfigs.length,
      models: modelConfigs.map((m) => m.name),
    });

    return modelConfigs;
  } catch (error) {
    console.warn("⚠️ [ModelDefinitions] Failed to fetch from backend, using fallback:", error);

    // Fallback to local AI_MODELS
    console.log("📋 [ModelDefinitions] Using local fallback configuration", {
      source: "fallback",
      count: AI_MODELS.length,
    });

    return AI_MODELS;
  }
}

// Check if models are available via backend endpoint
export async function checkModelAvailability(): Promise<{
  [key: string]: boolean;
}> {
  const now = Date.now();
  const cacheAge = now - lastCacheUpdate;
  const isCacheValid =
    cacheAge < CACHE_DURATION && Object.keys(modelAvailabilityCache).length > 0;

  console.log("🔍 [ModelAvailability] Checking model availability...", {
    timestamp: new Date().toISOString(),
    cacheAge: `${Math.round(cacheAge / 1000)}s`,
    cacheDuration: `${CACHE_DURATION / 1000}s`,
    hasCachedData: Object.keys(modelAvailabilityCache).length > 0,
    isCacheValid,
    lastUpdate: lastCacheUpdate
      ? new Date(lastCacheUpdate).toISOString()
      : "never",
  });

  // Return cached result if still fresh
  if (isCacheValid) {
    console.log("✅ [ModelAvailability] DATA SOURCE: CACHE (still valid)", {
      data: modelAvailabilityCache,
      source: "cache",
      isLiveData: false,
    });
    return modelAvailabilityCache;
  }

  console.log(
    "🌐 [ModelAvailability] Cache expired or empty, fetching fresh data from backend..."
  );

  try {
    // Call your backend endpoint that checks OpenAI model availability
    console.log("🌐 [ModelAvailability] Making request to backend...");
    const response = await API.get<{ [key: string]: boolean }>(
      "/llm_providers/availability/simple"
    );

    const availability = response.data;
    console.log("✅ [ModelAvailability] DATA SOURCE: BACKEND (live data)", {
      data: availability,
      source: "backend",
      isLiveData: true,
      timestamp: new Date().toISOString(),
    });

    modelAvailabilityCache = availability;
    lastCacheUpdate = now;

    // Log changes if any
    const enabledModels = Object.entries(availability)
      .filter(([, available]) => available)
      .map(([id]) => id);
    const disabledModels = Object.entries(availability)
      .filter(([, available]) => !available)
      .map(([id]) => id);

    console.log(
      "🟢 [ModelAvailability] Live backend data - Available models:",
      enabledModels
    );
    if (disabledModels.length > 0) {
      console.warn(
        "🔴 [ModelAvailability] Live backend data - Unavailable models:",
        disabledModels
      );
    }

    return availability;
  } catch (error) {
    // Handle specific error types
    if (error && typeof error === "object" && "response" in error) {
      const axiosError = error as {
        response?: { status?: number; statusText?: string; data?: unknown };
      };
      const status = axiosError.response?.status;
      const data = axiosError.response?.data;

      if (status === 401) {
        console.warn(
          "🔐 [ModelAvailability] Authentication required for backend endpoint",
          {
            status,
            message: "User not logged in or session expired",
            willUseFallback: true,
          }
        );
      } else if (status === 503) {
        console.warn("⚠️ [ModelAvailability] Backend service unavailable", {
          status,
          message:
            data && typeof data === "object" && "detail" in data
              ? (data as { detail: string }).detail
              : "Service unavailable",
          reason: "Likely OpenAI API key not configured",
          willUseFallback: true,
        });
      } else {
        console.error("❌ [ModelAvailability] Backend API error:", {
          status,
          statusText: axiosError.response?.statusText,
          data,
          willUseFallback: true,
        });
      }
    } else {
      console.error(
        "❌ [ModelAvailability] Network error fetching from backend:",
        {
          error: error,
          message: error instanceof Error ? error.message : String(error),
          name: error instanceof Error ? error.name : "Unknown",
          willUseFallback: true,
        }
      );
    }
  }

  // Fallback: assume all configured models are available
  console.warn(
    "⚠️ [ModelAvailability] DATA SOURCE: FALLBACK (backend unavailable)",
    {
      source: "fallback",
      isLiveData: false,
      reason: "Backend request failed or network error",
    }
  );

  // Use backend models if available, otherwise fall back to AI_MODELS
  const modelsToUse =
    modelsDefinitionCache.length > 0 ? modelsDefinitionCache : AI_MODELS;

  const fallback: { [key: string]: boolean } = {};
  modelsToUse.forEach((model) => {
    fallback[model.id] = model.isEnabled ?? true;
  });

  console.log(
    "📋 [ModelAvailability] Fallback configuration (assuming all enabled):",
    fallback
  );
  return fallback;
}

// Get available models (sync function with cached data)
export function getAvailableModels(): ModelConfig[] {
  // Use backend models if available, otherwise fall back to AI_MODELS
  const modelsToUse =
    modelsDefinitionCache.length > 0 ? modelsDefinitionCache : AI_MODELS;

  const availability = modelAvailabilityCache;
  const hasAvailabilityData = Object.keys(availability).length > 0;
  const cacheAge = Date.now() - lastCacheUpdate;
  const dataSource = hasAvailabilityData
    ? cacheAge < CACHE_DURATION
      ? "live-cache"
      : "stale-cache"
    : "no-data";

  console.log(
    "📊 [ModelSelection] Getting available models with current data:",
    {
      dataSource,
      modelSource: modelsDefinitionCache.length > 0 ? "backend" : "fallback",
      totalModels: modelsToUse.length,
      cacheAge: `${Math.round(cacheAge / 1000)}s`,
      hasData: hasAvailabilityData,
      availability,
      timestamp: new Date().toISOString(),
    }
  );

  const availableModels = modelsToUse.filter((model) => {
    const isConfigEnabled = model.isEnabled ?? true;
    const isBackendAvailable = availability[model.id] ?? true; // Default to available if unknown
    const isAvailable = isConfigEnabled && isBackendAvailable;

    console.log(`🔍 [ModelSelection] ${model.name} (${model.id}):`, {
      configEnabled: isConfigEnabled,
      backendAvailable: isBackendAvailable,
      finalAvailable: isAvailable,
      dataSource:
        availability[model.id] !== undefined ? dataSource : "fallback-default",
    });

    return isAvailable;
  });

  console.log(
    "✅ [ModelSelection] Final available models from",
    dataSource,
    ":",
    availableModels.map((m) => `${m.name} (${m.id})`)
  );
  return availableModels;
}

// Get default model (sync function)
export function getDefaultModel(): ModelConfig {
  const availableModels = getAvailableModels();
  const modelsToUse =
    modelsDefinitionCache.length > 0 ? modelsDefinitionCache : AI_MODELS;

  return (
    availableModels.find((model) => model.isDefault) ||
    availableModels[0] ||
    modelsToUse[0]
  );
}

// Get model by ID (sync function)
export function getModelById(id: string): ModelConfig | undefined {
  const modelsToUse =
    modelsDefinitionCache.length > 0 ? modelsDefinitionCache : AI_MODELS;
  return modelsToUse.find((model) => model.id === id);
}

// Initialize model availability check (call this on app startup)
export function initializeModelAvailability(): Promise<void> {
  console.log(
    "🚀 [ModelAvailability] Initializing model availability check on app startup..."
  );
  const startTime = Date.now();

  // Fetch both model definitions and availability in parallel
  return Promise.all([
    fetchModelsFromBackend().catch((error) => {
      console.warn("⚠️ [ModelDefinitions] Failed to fetch, using fallback:", error);
      return AI_MODELS;
    }),
    checkModelAvailability(),
  ])
    .then(([models, availability]) => {
      const endTime = Date.now();
      const duration = endTime - startTime;
      const hasLiveData = lastCacheUpdate === endTime; // If cache was just updated, we got live data

      console.log("✅ [ModelAvailability] Initialization complete:", {
        timestamp: new Date().toISOString(),
        duration: `${duration}ms`,
        dataSource: hasLiveData ? "backend-live" : "fallback",
        modelSource: modelsDefinitionCache.length > 0 ? "backend" : "fallback",
        isLiveData: hasLiveData,
        availability: availability,
        cacheUpdated: new Date(lastCacheUpdate).toISOString(),
        totalModels: Object.keys(availability).length,
        availableCount: Object.values(availability).filter(Boolean).length,
      });

      // Log summary of what models are available
      const enabledModels = Object.entries(availability)
        .filter(([, available]) => available)
        .map(([id]) => models.find((m) => m.id === id)?.name || id);

      console.log(
        `🎯 [ModelAvailability] Startup complete: ${enabledModels.length} models available:`,
        enabledModels
      );
    })
    .catch((error) => {
      console.error("❌ [ModelAvailability] Initialization failed:", error);
      console.warn(
        "⚠️ [ModelAvailability] App will use fallback model configuration"
      );
    });
}

// Get enhanced model info with availability status
export function getModelWithStatus(
  id: string
): (ModelConfig & { isAvailable: boolean }) | undefined {
  const model = getModelById(id);
  if (!model) return undefined;

  const isAvailable = modelAvailabilityCache[id] ?? true;
  return { ...model, isAvailable };
}

// Get information about the current data source for debugging
export function getDataSourceInfo(): {
  source: "live-cache" | "stale-cache" | "no-data";
  cacheAge: number;
  lastUpdate: string;
  isLiveData: boolean;
  hasData: boolean;
} {
  const now = Date.now();
  const cacheAge = now - lastCacheUpdate;
  const hasData = Object.keys(modelAvailabilityCache).length > 0;
  const isLiveData = hasData && cacheAge < CACHE_DURATION;

  let source: "live-cache" | "stale-cache" | "no-data";
  if (!hasData) {
    source = "no-data";
  } else if (cacheAge < CACHE_DURATION) {
    source = "live-cache";
  } else {
    source = "stale-cache";
  }

  return {
    source,
    cacheAge,
    lastUpdate: lastCacheUpdate
      ? new Date(lastCacheUpdate).toISOString()
      : "never",
    isLiveData,
    hasData,
  };
}

// Debug utility function - only available in development
if (process.env.NODE_ENV === 'development') {
  (globalThis as Record<string, unknown>).__debugModelAvailability = function () {
    const dataSource = getDataSourceInfo();
    const availableModels = getAvailableModels();

    console.log("🔍 Model Availability Debug Report", {
      timestamp: new Date().toISOString(),
      dataSource: dataSource,
      cache: modelAvailabilityCache,
      configuredModels: AI_MODELS.length,
      availableModels: availableModels.length,
      modelsList: availableModels.map((m) => ({
        id: m.id,
        name: m.name,
        enabled: m.isEnabled,
      })),
    });

    return {
      dataSource,
      cache: modelAvailabilityCache,
      availableModels: availableModels.map((m) => m.name),
    };
  };
}