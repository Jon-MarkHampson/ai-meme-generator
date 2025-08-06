// hooks/useModelSelection.ts
import { useState, useEffect } from "react";
import {
  getDefaultModel,
  getModelById,
  initializeModelAvailability,
  getDataSourceInfo,
  type ModelConfig,
} from "@/services/models";

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

  // Initialize model availability on first use
  useEffect(() => {
    console.log(
      "🎯 [useModelSelection] Initializing model availability check..."
    );
    initializeModelAvailability()
      .then(() => {
        const dataSource = getDataSourceInfo();
        console.log("✅ [useModelSelection] Model availability initialized:", {
          source: dataSource.source,
          isLiveData: dataSource.isLiveData,
          lastUpdate: dataSource.lastUpdate,
        });
      })
      .catch((error) => {
        console.warn(
          "⚠️ [useModelSelection] Model availability initialization failed:",
          error
        );
      });
  }, []);

  // Initialize with default model or from localStorage
  const [selectedModelId, setSelectedModelId] = useState<string>(() => {
    if (persistToLocalStorage && typeof window !== "undefined") {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const model = getModelById(saved);
        if (model?.isEnabled) {
          console.log(
            "🔄 [useModelSelection] Restored model from localStorage:",
            {
              modelId: saved,
              modelName: model.name,
            }
          );
          return saved;
        } else {
          console.log(
            "⚠️ [useModelSelection] Saved model is disabled, using default:",
            {
              savedModelId: saved,
              savedModelExists: !!model,
              savedModelEnabled: model?.isEnabled,
            }
          );
        }
      }
    }
    const defaultModel = getDefaultModel();
    console.log("🏁 [useModelSelection] Using default model:", {
      modelId: defaultModel.id,
      modelName: defaultModel.name,
    });
    return defaultModel.id;
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
      console.log("🔄 [useModelSelection] Changing model:", {
        from: selectedModelId,
        to: modelId,
        modelName: model.name,
        dataSource: getDataSourceInfo().source,
      });
      setSelectedModelId(modelId);
    } else {
      console.warn("❌ [useModelSelection] Cannot change to disabled model:", {
        modelId,
        modelExists: !!model,
        modelEnabled: model?.isEnabled,
      });
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
