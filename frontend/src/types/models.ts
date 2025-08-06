export interface ModelConfig {
  id: string;
  name: string;
  description: string;
  capabilities?: string[];
  pricing?: "low" | "medium" | "high";
  speed?: "fast" | "medium" | "slow";
  isDefault?: boolean;
  isEnabled?: boolean;
  maxTokens?: number;
  costPer1kTokens?: number;
}