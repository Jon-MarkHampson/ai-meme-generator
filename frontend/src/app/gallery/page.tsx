"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import * as React from "react"
import {
    FavouriteMemeRead,
    listFavourites,
} from "@/lib/gallery";
import { Card, CardContent } from "@/components/ui/card"
import {
    Carousel,
    CarouselContent,
    CarouselItem,
    CarouselNext,
    CarouselPrevious,
} from "@/components/ui/carousel"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import Image from "next/image"
import { FavoriteToggle } from "@/components/FavoriteToggle";
import { Loader2, Calendar, Download } from "lucide-react";

export default function GalleryPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [favourites, setFavourites] = useState<FavouriteMemeRead[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    console.log("Gallery page rendered. User:", user, "Loading:", loading);

    // fetch favourites on load ───────────────────────────────
    useEffect(() => {
        if (loading) return;

        if (!user) {
            router.push("/login");
            return;
        }

        const fetchFavorites = async () => {
            try {
                console.log("Fetching favorites...");
                const favoriteMemes = await listFavourites();
                console.log("Favorites loaded:", favoriteMemes);
                setFavourites(favoriteMemes);
            } catch (error) {
                console.error("Error fetching favorites:", error);
                setFavourites([]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchFavorites();
    }, [user, loading, router]);

    // Handle favorite toggle (remove from list when unfavorited)
    const handleFavoriteToggle = (memeId: string) => {
        setFavourites(prev => prev.filter(meme => meme.id !== memeId));
    };

    // Handle image download
    const handleDownload = async (imageUrl: string, memeId: string) => {
        try {
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `meme-${memeId.substring(0, 8)}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading image:', error);
            // Fallback to opening in new tab
            window.open(imageUrl, '_blank');
        }
    };

    if (loading || isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="w-8 h-8 animate-spin" />
            </div>
        );
    }

    if (!user) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div>Please log in to view your gallery.</div>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center w-full h-full overflow-hidden">
            <div className="mb-8 text-center">
                <h1 className="text-2xl mt-16 font-bold ">Gallery</h1>
                <p className="mt-4">Your favourite memes.</p>
            </div>
            <Carousel
                opts={{
                    align: "start",
                }}
                className="w-full max-w-6xl"
            >
                <CarouselContent>
                    {favourites.length > 0 ? (
                        favourites.map((meme) => (
                            <CarouselItem key={meme.id} className="md:basis-1/2 lg:basis-1/3">
                                <div className="p-0 m-0">
                                    <Card className="overflow-hidden p-0 relative">
                                        <CardContent className="p-0 leading-none">
                                            <TooltipProvider>
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <div className="relative">
                                                            <Image
                                                                src={meme.image_url}
                                                                alt={`Favorite meme ${meme.id}`}
                                                                width={400}
                                                                height={400}
                                                                className="w-full h-auto object-contain block rounded-lg"
                                                                style={{
                                                                    maxWidth: '100%',
                                                                    height: 'auto',
                                                                    display: 'block',
                                                                }}
                                                                onError={(e) => {
                                                                    // Fallback if image fails to load
                                                                    const target = e.target as HTMLImageElement;
                                                                    target.src = "/placeholder-meme.png";
                                                                }}
                                                            />
                                                        </div>
                                                    </TooltipTrigger>
                                                    <TooltipContent>
                                                        <div className="space-y-1">
                                                            <div className="flex items-center gap-2">
                                                                <Calendar className="w-4 h-4" />
                                                                <span className="text-sm">
                                                                    Created: {new Date(meme.created_at).toLocaleDateString()}
                                                                </span>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <Download className="w-4 h-4" />
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleDownload(meme.image_url, meme.id);
                                                                    }}
                                                                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline cursor-pointer bg-transparent border-none p-0"
                                                                >
                                                                    Download Image
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                            <div className="absolute top-2 right-2">
                                                <FavoriteToggle
                                                    imageUrl={meme.image_url}
                                                    memeId={meme.id}
                                                    initialIsFavorite={true}
                                                    size="sm"
                                                    onToggle={(memeId, newFavoriteStatus) => {
                                                        if (!newFavoriteStatus) {
                                                            handleFavoriteToggle(memeId);
                                                        }
                                                    }}
                                                />
                                            </div>
                                        </CardContent>
                                    </Card>
                                </div>
                            </CarouselItem>
                        ))
                    ) : (
                        // Show placeholder when no favorites or loading
                        <CarouselItem className="md:basis-1/2 lg:basis-1/3">
                            <div className="p-1">
                                <Card>
                                    <CardContent className="flex aspect-square items-center justify-center p-6">
                                        <div className="text-center text-muted-foreground">
                                            <p className="text-lg">No favorite memes yet!</p>
                                            <p className="text-sm mt-2">Start creating and favoriting memes to see them here.</p>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        </CarouselItem>
                    )}
                </CarouselContent>
                <CarouselPrevious />
                <CarouselNext />
            </Carousel>
        </div>
    );
}
