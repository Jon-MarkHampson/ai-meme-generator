import API from "./api";
import { FavouriteMemeRead, UserMemeList } from "@/types/gallery";

export async function listFavourites(): Promise<FavouriteMemeRead[]> {
  const { data } = await API.get<UserMemeList>("/user_memes/favorites");
  return data.memes;
}

// Toggle favorite status by meme ID
export async function toggleFavorite(
  memeId: string,
  isFavorite: boolean
): Promise<FavouriteMemeRead> {
  const { data } = await API.patch<FavouriteMemeRead>(`/user_memes/${memeId}`, {
    is_favorite: isFavorite,
  });
  // Invalidate cache when favorite status changes
  memesCache = null;
  lastCacheTime = 0;
  return data;
}

// Cache for user memes to prevent excessive API calls
let memesCache: FavouriteMemeRead[] | null = null;
let lastCacheTime = 0;
const CACHE_DURATION = 30000; // 30 seconds

// Get meme by image URL (to find the meme ID)
export async function getMemeByUrl(
  imageUrl: string
): Promise<FavouriteMemeRead | null> {
  try {
    const now = Date.now();

    // Use cached data if available and not expired
    if (memesCache && (now - lastCacheTime < CACHE_DURATION)) {
      return memesCache.find((meme) => meme.image_url === imageUrl) || null;
    }

    // Fetch fresh data
    const { data } = await API.get<UserMemeList>("/user_memes/");
    memesCache = data.memes;
    lastCacheTime = now;

    return data.memes.find((meme) => meme.image_url === imageUrl) || null;
  } catch (error) {
    console.error("Error fetching meme by URL:", error);
    return null;
  }
}
