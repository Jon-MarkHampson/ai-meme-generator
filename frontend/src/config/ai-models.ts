import { ModelConfig } from '@/types/models';

/**
 * AI Models Configuration - FALLBACK ONLY
 *
 * This configuration serves as a fallback when the backend is unavailable.
 * The primary source of truth is models-config.json at the project root,
 * which is served by the backend endpoint: GET /llm_providers/models
 *
 * This file should be kept in sync with models-config.json for consistency.
 * Consider this a static backup of the centralized configuration.
 */

export const AI_MODELS: ModelConfig[] = [
  // OpenAI Models
  {
    id: "openai:gpt-4o",
    name: "GPT-4o",
    description: "Latest OpenAI model with vision capabilities",
    capabilities: ["text", "vision", "reasoning"],
    pricing: "high",
    speed: "medium",
    isEnabled: true,
    maxTokens: 128000,
    costPer1kTokens: 0.015,
  },
  {
    id: "openai:gpt-4.1-2025-04-14",
    name: "GPT-4.1",
    description: "Advanced reasoning model (April 2025)",
    capabilities: ["text", "reasoning", "analysis"],
    pricing: "high",
    speed: "medium",
    isDefault: true,
    isEnabled: true,
    maxTokens: 200000,
    costPer1kTokens: 0.02,
  },
  {
    id: "openai:gpt-4.1-mini",
    name: "GPT-4.1 Mini",
    description: "Faster, cost-effective version",
    capabilities: ["text", "reasoning"],
    pricing: "medium",
    speed: "fast",
    isEnabled: true,
    maxTokens: 128000,
    costPer1kTokens: 0.008,
  },
  {
    id: "openai:gpt-4.1-nano",
    name: "GPT-4.1 Nano",
    description: "Ultra-fast for simple tasks",
    capabilities: ["text"],
    pricing: "low",
    speed: "fast",
    isEnabled: true,
    maxTokens: 64000,
    costPer1kTokens: 0.004,
  },
  {
    id: "openai:o1-mini",
    name: "O1 Mini",
    description: "Reasoning-focused model",
    capabilities: ["reasoning", "analysis"],
    pricing: "medium",
    speed: "slow",
    isEnabled: true,
    maxTokens: 128000,
    costPer1kTokens: 0.012,
  },

  // Anthropic Claude Models
  {
    id: "anthropic:claude-sonnet-4-20250514",
    name: "Claude Sonnet 4",
    description: "Latest Claude model with enhanced reasoning",
    capabilities: ["text", "reasoning", "analysis", "vision"],
    pricing: "high",
    speed: "medium",
    isEnabled: true,
    maxTokens: 200000,
    costPer1kTokens: 0.015,
  },
  {
    id: "anthropic:claude-3-7-sonnet-20250219",
    name: "Claude Sonnet 3.7",
    description: "Enhanced version of Claude 3.5 Sonnet",
    capabilities: ["text", "reasoning", "analysis", "vision"],
    pricing: "high",
    speed: "medium",
    isEnabled: true,
    maxTokens: 200000,
    costPer1kTokens: 0.012,
  },
  {
    id: "anthropic:claude-3-5-sonnet-latest",
    name: "Claude Sonnet 3.5",
    description: "Latest Claude 3.5 Sonnet with improvements",
    capabilities: ["text", "reasoning", "analysis", "vision"],
    pricing: "medium",
    speed: "medium",
    isEnabled: true,
    maxTokens: 200000,
    costPer1kTokens: 0.008,
  },

  // Image Generation Models
  {
    id: "gemini:gemini-2.5-flash-image",
    name: "Nano Banana (Gemini)",
    description: "Gemini's fast image generation model (Nano Banana)",
    capabilities: ["image-generation"],
    pricing: "low",
    speed: "fast",
    isEnabled: true,
    isDefault: true,
    maxTokens: undefined,
    costPer1kTokens: 0.001,
  },
  {
    id: "openai:gpt-4.1-image",
    name: "OpenAI Image Generation",
    description: "OpenAI's image generation via Responses API",
    capabilities: ["image-generation"],
    pricing: "high",
    speed: "medium",
    isEnabled: true,
    maxTokens: undefined,
    costPer1kTokens: 0.02,
  },
];