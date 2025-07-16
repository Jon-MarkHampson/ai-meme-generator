from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from openai.types.responses import WebSearchToolParam
from pydantic import BaseModel


# Load environment variables (e.g. OPENAI_API_KEY)
load_dotenv()

# Configure Logfire for observability
logfire.configure()
logfire.instrument_pydantic_ai()

# Configure the OpenAI Responses model to include built-in web search
model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[WebSearchToolParam(type="web_search_preview")]
)

# Use GPT-4.1 with built-in web_search_preview tool
model = OpenAIResponsesModel("gpt-4.1-2025-04-14")


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


# ----- Meme Generation Agent -----
# This agent produces raw meme captions based on theme keywords.
meme_generation_agent = Agent(
    model=model,
    model_settings=model_settings,
    instructions="""
# Role and Objective
You are a meme-caption factory: generate meme captions from themes.

# Instructions
## Persistence
- Continue iterating until you have fully satisfied the user's requested number of variants before ending your turn.

## Tool Calling
- If you need up-to-date context, use the built-in `web_search_preview` tool. Do NOT guess or hallucinate facts.

## Planning
- Plan step-by-step how you will retrieve context and generate concise top/bottom text pairs. Reflect briefly before each generation step.

## Task Instructions
- Given a list of theme keywords, optionally fetch web context, then produce the requested number of short, clever, meme-style captions in top text / bottom text format.
- Do not use emojis, hashtags, or extra commentary.

## Examples
- **Themes:** ["Mondays", "coffee"]
- **Output:**
```json
{"captions": [
  {"text_box_1": "When you wake up on Monday,", "text_box_2": "screaming for coffee."},
  {"text_box_1": "Mondays spelled backward is", "text_box_2": "'syadnoM'—still no coffee."},
  {"text_box_1": "May your coffee be strong:", "text_box_2": "and your Monday be short!"}
]}
```

## Output Format
- Return strictly valid JSON matching the `ResponseMemeCaptions` schema.
""",
    output_type=ResponseMemeCaptions,
)

# ----- Meme Selection Agent -----
# This agent curates and filters generated memes.
meme_selection_agent = Agent(
    model=model,
    model_settings=model_settings,
    instructions="""
# Role and Objective
You are a meme curator: select and refine the best captions.

# Instructions
## Persistence
- Keep refining until the final set meets the desired count and is funny and relevant.

## Tool Calling
- Use the `meme_factory` tool exactly once, passing the full list of keywords and the count, to fetch candidate memes.
- If you need updated context, call `web_search_preview` as above. Do NOT guess or hallucinate.

## Planning
- Plan your selection criteria (humor, relevance, on-theme) before filtering. If not enough candidates remain, you may recall `meme_factory` again with the same arguments.

## Task Instructions
- Review the batch of memes returned by `meme_factory`.
- Discard any that aren't funny, relevant, or on-theme.
- Ensure the final output count matches the user's request.

## Example Flow
```text
1. Call meme_factory(keywords=['Mondays','coffee'], count=3) → 3 captions
2. Filter out 1 that is bland
3. Only 2 remain but 3 requested → recall meme_factory(...) again
4. Aggregate or choose new ones to total 3
``` 

## Output Format
- Return strictly valid JSON matching the `ResponseMemeCaptions` schema.
""",
    output_type=str,
)


# Register a tool on the selector that delegates to the generation agent
@meme_selection_agent.tool
async def meme_factory(
    ctx: RunContext[None], keywords: list[str], count: int
) -> list[MemeCaptionAndContext]:
    """
    Delegate caption generation to the meme_generation_agent, sharing usage budget.
    """
    result = await meme_generation_agent.run(
        f"Themes: {', '.join(keywords)}. Create {count} captions.",
        usage=ctx.usage,
    )
    return result.output.captions


def generate_curated_memes(
    keywords: list[str],
    num_variants: int = 5,
    usage_limits: UsageLimits = UsageLimits(request_limit=5, total_tokens_limit=5000),
) -> list[MemeCaptionAndContext]:
    """
    Generate and curate meme captions using a two-agent pipeline.
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
