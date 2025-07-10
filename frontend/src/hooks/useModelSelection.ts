// hooks/useModelSelection.ts
import { useState, useEffect } from "react";
import {
  getDefaultModel,
  getModelById,
  type ModelConfig,
} from "@/config/models";

interface UseModelSelectionOptions {
  persistToLocalStorage?: boolean;
  storageKey?: string;
  onModelChange?: (model: ModelConfig) => void;
}

export function useModelSelection(options: UseModelSelectionOptions = {}) {
  const {
    persistToLocalStorage = true,
    storageKey = "ai-meme-generator-selected-model",
    onModelChange,
  } = options;

  // Initialize with default model or from localStorage
  const [selectedModelId, setSelectedModelId] = useState<string>(() => {
    if (persistToLocalStorage && typeof window !== "undefined") {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const model = getModelById(saved);
        if (model?.isEnabled) {
          return saved;
        }
      }
    }
    return getDefaultModel().id;
  });

  const selectedModel = getModelById(selectedModelId);

  // Persist to localStorage when model changes
  useEffect(() => {
    if (persistToLocalStorage && typeof window !== "undefined") {
      localStorage.setItem(storageKey, selectedModelId);
    }

    if (onModelChange && selectedModel) {
      onModelChange(selectedModel);
    }
  }, [
    selectedModelId,
    persistToLocalStorage,
    storageKey,
    onModelChange,
    selectedModel,
  ]);

  const changeModel = (modelId: string) => {
    const model = getModelById(modelId);
    if (model?.isEnabled) {
      setSelectedModelId(modelId);
    }
  };

  return {
    selectedModelId,
    selectedModel,
    changeModel,
    isModelAvailable: (modelId: string) => {
      const model = getModelById(modelId);
      return model?.isEnabled ?? false;
    },
  };
}
