// config/models.ts
export interface ModelConfig {
  id: string;
  name: string;
  description: string;
  capabilities?: string[];
  pricing?: "low" | "medium" | "high";
  speed?: "fast" | "medium" | "slow";
  isDefault?: boolean;
  isEnabled?: boolean;
}

export const AI_MODELS: ModelConfig[] = [
  {
    id: "openai:gpt-4o",
    name: "GPT-4o",
    description: "Latest OpenAI model with vision capabilities",
    capabilities: ["text", "vision", "reasoning"],
    pricing: "high",
    speed: "medium",
    isEnabled: true,
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
  },
  {
    id: "openai:gpt-4.1-mini",
    name: "GPT-4.1 Mini",
    description: "Faster, cost-effective version",
    capabilities: ["text", "reasoning"],
    pricing: "medium",
    speed: "fast",
    isEnabled: true,
  },
  {
    id: "openai:gpt-4.1-nano",
    name: "GPT-4.1 Nano",
    description: "Ultra-fast for simple tasks",
    capabilities: ["text"],
    pricing: "low",
    speed: "fast",
    isEnabled: true,
  },
  {
    id: "openai:o1-mini",
    name: "O1 Mini",
    description: "Reasoning-focused model",
    capabilities: ["reasoning", "analysis"],
    pricing: "medium",
    speed: "slow",
    isEnabled: true,
  },
];

export const getAvailableModels = () =>
  AI_MODELS.filter((model) => model.isEnabled);
export const getDefaultModel = () =>
  AI_MODELS.find((model) => model.isDefault) || AI_MODELS[0];
export const getModelById = (id: string) =>
  AI_MODELS.find((model) => model.id === id);
