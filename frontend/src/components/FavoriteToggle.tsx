// components/FavoriteToggle.tsx
import { useState, useEffect } from "react";
import { HeartMinus, HeartPlus, Loader2 } from "lucide-react";
import { Toggle } from "@/components/ui/toggle";
import { toggleFavorite, getMemeByUrl } from "@/lib/gallery";

interface FavoriteToggleProps {
    imageUrl: string;
    memeId?: string;
    initialIsFavorite?: boolean;
    size?: "sm" | "lg" | "default";
    onToggle?: (memeId: string, newFavoriteStatus: boolean) => void;
}

export function FavoriteToggle({
    imageUrl,
    memeId,
    initialIsFavorite,
    size = "sm",
    onToggle
}: FavoriteToggleProps) {
    const [isFavorite, setIsFavorite] = useState(initialIsFavorite ?? false);
    const [isLoading, setIsLoading] = useState(false);
    const [isInitializing, setIsInitializing] = useState(initialIsFavorite === undefined);

    // Fetch initial favorite status if not provided
    useEffect(() => {
        if (initialIsFavorite !== undefined) {
            setIsInitializing(false);
            return;
        }

        const fetchInitialStatus = async () => {
            try {
                const meme = await getMemeByUrl(imageUrl);
                if (meme) {
                    setIsFavorite(meme.is_favorite);
                }
            } catch (error) {
                console.error("Error fetching initial favorite status:", error);
            } finally {
                setIsInitializing(false);
            }
        };

        fetchInitialStatus();
    }, [imageUrl, initialIsFavorite]);

    const handleToggle = async () => {
        if (isLoading || isInitializing) return;

        setIsLoading(true);
        try {
            let currentMemeId = memeId;

            // If no memeId provided, try to find it by URL
            if (!currentMemeId) {
                const meme = await getMemeByUrl(imageUrl);
                if (!meme) {
                    console.error("Could not find meme for URL:", imageUrl);
                    return;
                }
                currentMemeId = meme.id;
            }

            const newFavoriteStatus = !isFavorite;
            await toggleFavorite(currentMemeId, newFavoriteStatus);
            setIsFavorite(newFavoriteStatus);

            // Call the callback if provided
            if (onToggle) {
                onToggle(currentMemeId, newFavoriteStatus);
            }
        } catch (error) {
            console.error("Error toggling favorite:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Toggle
            size={size}
            pressed={isFavorite}
            onPressedChange={handleToggle}
            disabled={isLoading || isInitializing}
            aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
            className="data-[state=on]:bg-red-100 data-[state=on]:text-red-600 hover:bg-red-50"
        >
            {isLoading || isInitializing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
            ) : isFavorite ? (
                <HeartMinus className="h-4 w-4" />
            ) : (
                <HeartPlus className="h-4 w-4" />
            )}
        </Toggle>
    );
}
