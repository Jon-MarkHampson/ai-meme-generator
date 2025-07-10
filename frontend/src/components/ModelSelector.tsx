// components/ModelSelector.tsx
import React from 'react';
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { getAvailableModels, getModelById, type ModelConfig } from "@/config/models";

interface ModelSelectorProps {
    selectedModel: string;
    onModelChange: (modelId: string) => void;
    className?: string;
    showMetadata?: boolean;
}

export function ModelSelector({ selectedModel, onModelChange, className = "", showMetadata = true }: ModelSelectorProps) {
    const availableModels = getAvailableModels();
    const selectedModelConfig = getModelById(selectedModel);

    return (
        <TooltipProvider>
            <div className={`flex gap-2 items-center ${className}`}>
                <span className="text-sm font-medium text-muted-foreground">Model:</span>
                <Select value={selectedModel} onValueChange={onModelChange}>
                    <SelectTrigger className="w-[200px]">
                        <SelectValue>
                            <div className="flex items-center gap-2">
                                <span>{selectedModelConfig?.name || selectedModel}</span>
                                {showMetadata && selectedModelConfig && (
                                    <div className="flex gap-1 text-xs text-muted-foreground">
                                        <span>({selectedModelConfig.pricing}, {selectedModelConfig.speed})</span>
                                    </div>
                                )}
                            </div>
                        </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                        <SelectGroup>
                            <SelectLabel>Choose AI Model</SelectLabel>
                            {availableModels.map((model) => (
                                <Tooltip key={model.id}>
                                    <TooltipTrigger asChild>
                                        <SelectItem value={model.id} className="cursor-pointer">
                                            <div className="flex flex-col gap-1 py-1">
                                                <div className="flex items-center justify-between gap-3">
                                                    <span className="font-medium">{model.name}</span>
                                                    {showMetadata && (
                                                        <span className="text-xs text-muted-foreground">
                                                            {model.pricing} • {model.speed}
                                                        </span>
                                                    )}
                                                </div>
                                                <span className="text-xs text-muted-foreground">{model.description}</span>
                                                {model.capabilities && (
                                                    <div className="text-xs text-muted-foreground">
                                                        {model.capabilities.join(', ')}
                                                    </div>
                                                )}
                                            </div>
                                        </SelectItem>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <div className="max-w-xs">
                                            <p className="font-medium">{model.name}</p>
                                            <p className="text-sm text-muted-foreground">{model.description}</p>
                                            {model.capabilities && (
                                                <p className="text-xs mt-1">
                                                    Capabilities: {model.capabilities.join(', ')}
                                                </p>
                                            )}
                                        </div>
                                    </TooltipContent>
                                </Tooltip>
                            ))}
                        </SelectGroup>
                    </SelectContent>
                </Select>
            </div>
        </TooltipProvider>
    );
}
