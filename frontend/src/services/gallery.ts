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
  return data;
}

// Get meme by image URL (to find the meme ID)
export async function getMemeByUrl(
  imageUrl: string
): Promise<FavouriteMemeRead | null> {
  try {
    const { data } = await API.get<UserMemeList>("/user_memes/");
    return data.memes.find((meme) => meme.image_url === imageUrl) || null;
  } catch (error) {
    console.error("Error fetching meme by URL:", error);
    return null;
  }
}
