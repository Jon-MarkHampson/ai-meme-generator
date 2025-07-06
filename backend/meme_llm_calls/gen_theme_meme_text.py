from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic import BaseModel, ValidationError

# Load environment variables (e.g. OPENAI_API_KEY)
load_dotenv()

model = OpenAIModel("gpt-4.1-2025-04-14")


class MemeCaptionAndContext(BaseModel):
    """
    Represents a single meme caption with top and bottom text.
    Each caption has two text boxes.
    """

    text_box_1: str  # Top text
    text_box_2: str  # Bottom text


# Define the output schema for meme captions
class ResponseMemeCaptions(BaseModel):
    """
    Schema for validated meme captions.
    Each caption object has 'text_box_1' and 'text_box_2'.
    """

    captions: list[MemeCaptionAndContext]


# Initialize a PydanticAI Agent with DuckDuckGo search and output_type schema
agent = Agent(
    model=model,
    tools=[duckduckgo_search_tool()],
    system_prompt=(
        "You are a meme-caption generator. Your job: produce meaningful, astute, satirical, short, punchy, meme-style captions that are informed, witty, relatable, and funny. "
        "Given theme keywords, decide whether to use duckduckgo_search_tool to fetch fresh context. "
        "Do not use emojis, hashtags, or extra commentary. "
    ),
    output_type=ResponseMemeCaptions,  # Pydantic schema enforcement
)


def generate_meme_text(
    keywords: list[str], num_variants: int = 5
) -> ResponseMemeCaptions:
    """
    Generate meme captions from theme keywords, optionally using search tool.

    Args:
        keywords: List of theme keywords.
        num_variants: Number of captions to return.

    Returns:
        List of caption dicts, each with 'text_box_1' and 'text_box_2'.
    """
    prompt = (
        f"Themes: {', '.join(keywords)}. "
        f"Create {num_variants} meme-format captions in top text/bottom text structure: "
    )

    try:
        # Directly get validated output via output_type
        result = agent.run_sync(prompt)
        return result.output.captions
    except ValidationError as ve:
        # If schema validation fails, you could log ve or retry
        raise RuntimeError(f"Invalid response format: {ve}")


def prompt_for_themes() -> list[str]:
    """
    Ask the user to enter comma-separated theme keywords.
    """
    raw = input("Enter theme keywords separated by commas: ")
    return [kw.strip() for kw in raw.split(",") if kw.strip()]


if __name__ == "__main__":
    themes = prompt_for_themes()
    if not themes:
        print("No themes entered. Exiting.")
    else:
        try:
            captions = generate_meme_text(themes)
            print("\nGenerated Captions:")
            for i, cap in enumerate(captions, 1):
                print(f"{i}. TOP: {cap.text_box_1} | BOTTOM: {cap.text_box_2}")
        except RuntimeError as err:
            print(f"Error generating captions: {err}")
