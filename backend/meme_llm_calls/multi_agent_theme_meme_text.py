from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic import BaseModel
import logfire


# Load environment variables (e.g. OPENAI_API_KEY)
load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()

model = OpenAIModel("gpt-4.1-2025-04-14")


class MemeCaptionAndContext(BaseModel):
    """
    Represents a single meme caption with top and bottom text.
    """

    text_box_1: str  # Top text
    text_box_2: str  # Bottom text


class ResponseMemeCaptions(BaseModel):
    """
    Wrapper schema for a list of MemeCaptionAndContext objects.
    """

    captions: list[MemeCaptionAndContext]


# Agent that only generates raw meme captions
meme_generation_agent = Agent(
    model=model,
    # tools=[duckduckgo_search_tool()],
    system_prompt=(
        "You are a meme-caption factory. Given theme keywords, decide if you need fresh context from the web; "
        "if so, call the {'type': 'web_search_preview'} tool. Then generate the requested number of short, clever, meme-style captions "
        "as top text/bottom text pairs. Do not use emojis or hashtags. Return JSON matching ResponseMemeCaptions."
    ),
    output_type=ResponseMemeCaptions,
)

# Agent that selects the best memes from candidates
meme_selection_agent = Agent(
    model=model,
    system_prompt=(
        "You are a meme curator. Use the meme_factory tool to get a batch of memes, review them, discard any that aren't funny or relevant, "
        "and return a final list of the top captions. If the batch is insufficient, you may call meme_factory again. "
        "Return only JSON matching ResponseMemeCaptions."
    ),
    output_type=ResponseMemeCaptions,
)


# Register a tool on the selector that delegates to the generator
@meme_selection_agent.tool
async def meme_factory(
    ctx: RunContext[None], keywords: list[str], count: int
) -> list[MemeCaptionAndContext]:
    # Delegate generation to meme_generation_agent, sharing usage budget
    result = await meme_generation_agent.run(
        f"Themes: {', '.join(keywords)}. Create {count} captions.",
        usage=ctx.usage,
    )
    # result.output is ResponseMemeCaptions
    return result.output.captions


def generate_curated_memes(
    keywords: list[str],
    num_variants: int = 5,
    usage_limits: UsageLimits = UsageLimits(request_limit=5, total_tokens_limit=5000),
) -> list[MemeCaptionAndContext]:
    """
    Generate and curate meme captions using a two-agent pipeline.

    Args:
        keywords: Theme keywords.
        num_variants: Desired final count of meme captions.
        usage_limits: Caps on requests and tokens.

    Returns:
        A list of curated MemeCaptionAndContext objects.
    """
    prompt = f"Fetch {num_variants} top captions for themes: {', '.join(keywords)}."
    result = meme_selection_agent.run_sync(prompt, usage_limits=usage_limits)
    return result.output.captions


def prompt_for_themes() -> list[str]:
    raw = input("Enter theme keywords separated by commas: ")
    return [kw.strip() for kw in raw.split(",") if kw.strip()]


if __name__ == "__main__":
    themes = prompt_for_themes()
    if not themes:
        print("No themes entered. Exiting.")
    else:
        captions = generate_curated_memes(themes)
        print("\nCurated Meme Captions:")
        for i, cap in enumerate(captions, 1):
            print(f"{i}. TOP: {cap.text_box_1} | BOTTOM: {cap.text_box_2}")
