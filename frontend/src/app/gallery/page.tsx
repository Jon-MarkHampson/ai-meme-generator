"use client";
import { useEffect, useState, useRef } from "react";
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
import Image from "next/image"


export default function GalleryPage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    const [favourites, setFavourites] = useState<FavouriteMemeRead[]>([]);

    // redirect if not logged in ─────────────────────────────
    useEffect(() => {
        if (!loading && !user) {
            router.replace("/");
        }
    }, [loading, user, router]);

    // fetch favourites on load ───────────────────────────────
    useEffect(() => {
        listFavourites()
            .then(setFavourites)
            .catch(() => setFavourites([]));
    }, []);

    return (
        <div className="flex flex-col items-center justify-center w-full h-screen">
            <div className="mb-8 text-center">
                <h1 className="text-2xl font-bold ">Gallery</h1>
                <p className="mt-4">This is the gallery page for your favourite memes.</p>
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
                                    <Card className="overflow-hidden p-0">
                                        <CardContent className="p-0 leading-none">
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


