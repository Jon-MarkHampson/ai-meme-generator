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
import { getAvailableModels, getModelById, getModelWithStatus, getDataSourceInfo } from "@/config/models";

interface ModelSelectorProps {
    selectedModel: string;
    onModelChange: (modelId: string) => void;
    className?: string;
    showMetadata?: boolean;
    showDebugInfo?: boolean;
}

export function ModelSelector({
    selectedModel,
    onModelChange,
    className = "",
    showMetadata = true,
    showDebugInfo = process.env.NODE_ENV === 'development'
}: ModelSelectorProps) {
    const availableModels = getAvailableModels();
    const selectedModelConfig = getModelById(selectedModel);
    const dataSourceInfo = getDataSourceInfo();

    return (
        <TooltipProvider>
            <div className={`flex flex-col gap-2 ${className}`}>
                <div className="flex gap-2 items-center">
                    <span className="text-sm font-medium text-muted-foreground">Model:</span>
                    <Select value={selectedModel} onValueChange={onModelChange}>
                        <SelectTrigger className="w-[240px]">
                            <SelectValue>
                                <div className="flex items-center gap-2">
                                    <span>{selectedModelConfig?.name || selectedModel}</span>
                                    {showMetadata && selectedModelConfig && (
                                        <div className="flex gap-1 text-xs text-muted-foreground">
                                            {/* <span className="px-1 py-0.5 bg-gray-100 rounded text-xs">
                                                {selectedModelConfig.pricing}
                                            </span> */}
                                            {/* <span className="px-1 py-0.5 bg-blue-100 rounded text-xs">
                                                {selectedModelConfig.speed}
                                            </span> */}
                                        </div>
                                    )}
                                </div>
                            </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                                <SelectLabel>Choose AI Model</SelectLabel>
                                {availableModels.map((model) => {
                                    const modelWithStatus = getModelWithStatus(model.id);
                                    const isAvailable = modelWithStatus?.isAvailable ?? true;

                                    return (
                                        <Tooltip key={model.id}>
                                            <TooltipTrigger asChild>
                                                <SelectItem
                                                    value={model.id}
                                                    className="cursor-pointer"
                                                    disabled={!isAvailable}
                                                >
                                                    <div className="flex flex-col gap-1 py-1">
                                                        <div className="flex items-center justify-between gap-3">
                                                            <div className="flex items-center gap-2">
                                                                <span className="font-medium">{model.name}</span>
                                                                {!isAvailable && (
                                                                    <span className="text-xs text-red-500 bg-red-50 px-1 py-0.5 rounded">
                                                                        Unavailable
                                                                    </span>
                                                                )}
                                                            </div>
                                                            {/* {showMetadata && (
                                                                <div className="flex gap-1">
                                                                    <span className="text-xs text-muted-foreground px-1 py-0.5 bg-gray-50 rounded">
                                                                        {model.pricing}
                                                                    </span>
                                                                    <span className="text-xs text-muted-foreground px-1 py-0.5 bg-blue-50 rounded">
                                                                        {model.speed}
                                                                    </span>
                                                                </div>
                                                            )} */}
                                                        </div>
                                                        <span className="text-xs text-muted-foreground">{model.description}</span>
                                                        {/*
                                                        {model.capabilities && (
                                                            <div className="text-xs text-muted-foreground">
                                                                Capabilities: {model.capabilities.join(', ')}
                                                            </div>
                                                        )}
                                                        */}
                                                        {showMetadata && (
                                                            <div className="flex gap-1">
                                                                <span className="text-xs text-muted-foreground ">
                                                                    Pricing: {model.pricing} |
                                                                </span>
                                                                <span className="text-xs text-muted-foreground ">
                                                                    Speed: {model.speed}
                                                                </span>
                                                            </div>
                                                        )}

                                                    </div>
                                                </SelectItem>
                                            </TooltipTrigger>
                                            <TooltipContent>
                                                <div className="max-w-xs">
                                                    {/* <p className="font-medium">{model.name}</p>
                                                    <p className="text-sm text-muted-foreground">{model.description}</p> */}
                                                    {/* {model.capabilities && (
                                                        <p className="text-xs mt-1">
                                                            Capabilities: {model.capabilities.join(', ')}
                                                        </p>
                                                    )} */}
                                                    {model.costPer1kTokens && (
                                                        <p className="text-xs mt-1">
                                                            Cost: ${model.costPer1kTokens}/1k tokens
                                                        </p>
                                                    )}
                                                    {model.maxTokens && (
                                                        <div className="text-xs text-muted-foreground">
                                                            Max tokens: {model.maxTokens.toLocaleString()}
                                                        </div>
                                                    )}
                                                    <p className="text-xs mt-1 text-muted-foreground">
                                                        Status: {isAvailable ? '✅ Available' : '❌ Unavailable'}
                                                    </p>
                                                </div>
                                            </TooltipContent>
                                        </Tooltip>
                                    );
                                })}
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </div>

                {/* Debug info in development mode */}
                {showDebugInfo && (
                    <div className="text-xs text-muted-foreground bg-gray-50 p-2 rounded border">
                        <div className="font-medium text-gray-700 mb-1">🔍 Model Data Source Debug:</div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <span className="font-medium">Source:</span>
                                <span className={`ml-1 px-1 py-0.5 rounded text-xs ${dataSourceInfo.source === 'live-cache' ? 'bg-green-100 text-green-800' :
                                    dataSourceInfo.source === 'stale-cache' ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-red-100 text-red-800'
                                    }`}>
                                    {dataSourceInfo.source}
                                </span>
                            </div>
                            <div>
                                <span className="font-medium">Live Data:</span>
                                <span className={`ml-1 ${dataSourceInfo.isLiveData ? 'text-green-600' : 'text-red-600'}`}>
                                    {dataSourceInfo.isLiveData ? '✅ Yes' : '❌ No'}
                                </span>
                            </div>
                            <div>
                                <span className="font-medium">Cache Age:</span>
                                <span className="ml-1">{Math.round(dataSourceInfo.cacheAge / 1000)}s</span>
                            </div>
                            <div>
                                <span className="font-medium">Last Update:</span>
                                <span className="ml-1">
                                    {dataSourceInfo.lastUpdate === 'never' ? 'Never' :
                                        new Date(dataSourceInfo.lastUpdate).toLocaleTimeString()}
                                </span>
                            </div>
                        </div>
                        <div className="mt-1 text-xs text-gray-600">
                            Available models: {availableModels.length}
                        </div>
                        {dataSourceInfo.source === 'no-data' && (
                            <div className="mt-1 text-xs text-amber-600 bg-amber-50 p-1 rounded">
                                💡 Tip: Log in to get live model availability from backend
                            </div>
                        )}
                    </div>
                )}
            </div>
        </TooltipProvider>
    );
}
