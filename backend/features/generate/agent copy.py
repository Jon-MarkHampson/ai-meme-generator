# backend/features/generate/agent.py

import logfire
from dotenv import load_dotenv

from openai.types.responses import WebSearchToolParam
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits
from pydantic_ai.models.openai import (
    OpenAIResponsesModel,
    OpenAIResponsesModelSettings,
)
from .models import MemeCaption, ResponseMemeCaptions

# ─── Bootstrap ─────────────────────────────────────────────────────────────
load_dotenv()
logfire.configure()
logfire.instrument_pydantic_ai()

model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[WebSearchToolParam(type="web_search_preview")],
    allow_tools=True,
)
model = OpenAIResponsesModel("gpt-4.1-2025-04-14")


# ─── Meme Theme Generation Agent ────────────────────────────────────────────
meme_theme_generation_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
You are a meme-caption factory: generate meme captions from themes.

- Use web_search_preview if you need fresh context.
- Produce exactly N captions in JSON:
  {"captions":[{"text_box_1":"...","text_box_2":"...},…]}.
""",
    output_type=ResponseMemeCaptions,
)


# ─── Meme Selection Agent ───────────────────────────────────────────────────
meme_selection_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
You are a meme curator: select and refine the best captions.

- Call the `meme_factory` tool once with (keywords, count) to get candidates.
- Filter for humor, relevance, on-theme. Output the final JSON.
""",
    output_type=ResponseMemeCaptions,
)


@meme_selection_agent.tool
async def meme_factory(
    ctx: RunContext[None], keywords: list[str], count: int
) -> list[MemeCaption]:
    # Delegate actual caption generation
    result = await meme_theme_generation_agent.run(
        f"Themes: {', '.join(keywords)}. Create {count} captions.",
        usage=ctx.usage,
    )
    return result.output.captions


# ─── Random/Inspiration Agent ───────────────────────────────────────────────
meme_random_inspiration_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
You are a meme inspiration engine: given no theme, surprise the user with 3 fresh caption pairs.
Return JSON matching ResponseMemeCaptions.
""",
    output_type=ResponseMemeCaptions,
)


# ─── Meme Image Generation Agent ───────────────────────────────────────────
meme_image_generation_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
You are a meme image generator: given a list of captions, produce URLs or binary data URLs
for each image. Return JSON like:
{"images":[{"caption_id":0,"url":"..."},…]}
""",
    # You could define a ResponseImages schema here if desired
)


# ─── Orchestrator ─────────────────────────────────────────────────────────
main_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
You are the Meme Orchestrator. Only handle meme-related requests.

- To generate theme-based captions, call meme_theme_generation_agent.
- To refine/select captions, call meme_selection_agent.
- To surprise the user, call meme_random_inspiration_agent.
- To create images, call meme_image_generation_agent.
- Use web_search_preview if you need up-to-date facts.
- Return a final JSON matching ResponseMemeCaptions.
""",
    output_type=ResponseMemeCaptions,
)

# Exported for service.py
__all__ = [
    "main_agent",
    "meme_theme_generation_agent",
    "meme_selection_agent",
    "meme_random_inspiration_agent",
    "meme_image_generation_agent",
]
