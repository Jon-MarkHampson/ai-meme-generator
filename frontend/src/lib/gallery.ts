// lib/gallery.ts
import API from "./api";

export interface FavouriteMemeRead {
  id: string;
  user_id: string;
  conversation_id: string;
  meme_template_id?: string;
  caption_variant_id?: string;
  image_url: string;
  openai_response_id?: string;
  is_favorite: boolean;
  created_at: Date;
}

export interface UserMemeList {
  memes: FavouriteMemeRead[];
}

export async function listFavourites(): Promise<FavouriteMemeRead[]> {
  const { data } = await API.get<UserMemeList>("/user_memes/favorites");
  return data.memes;
}
