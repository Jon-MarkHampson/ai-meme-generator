import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.imgflip.com"


def get_memes():
    """
    Retrieve all meme templates available on Imgflip.

    Returns:
        dict: API response data with the list of memes.
    """
    url = f"{BASE_URL}/get_memes"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def handle_top_templates(limit: int = 100):

    response = get_memes()

    if response:
        if response.get("success"):
            logger.info("Meme templates retrieved successfully")
            memes = response["data"]["memes"]
            for meme in memes[:limit]:
                meme_id = meme["id"]
                meme_name = meme["name"]
                meme_url = meme["url"]
                box_count = meme["box_count"]
                print(
                    f"Meme ID: {meme_id}, Name: {meme_name}, URL: {meme_url}, Box Count: {box_count}",
                )
        else:
            error_message = response.get(
                "error_message", "Unknown error occurred when fetching memes."
            )
            logger.info(f"Error: {error_message}")
    else:
        logger.info("Error: No response received while fetching memes.")


if __name__ == "__main__":
    handle_top_templates()
