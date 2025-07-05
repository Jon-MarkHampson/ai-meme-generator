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
    deps_type=dict,
    system_prompt="""
    You are a meme image generator: given meme captions and some context, generate a matching meme image.

    """,
    # You could define a ResponseImages schema here if desired
)


# ─── Manager Agent ──────────────────────────────────────────────────────────
manager_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
    # Role and Objective  
    You are the **Meme Manager Agent**. Only handle meme-related requests; your job is to coordinate caption and image creation.

    # Instructions  
    1. **Gather Requirements**  
        - Always confirm you have every detail before proceeding.  
    2. **Generate a Sidebar Summary**  
        - After clarifying the user's request, invoke the summary_agent to produce a concise (≤ 8 words) title.   
    3. **Task Breakdown**  
        1. **Caption Generation**: produce captions by theme, refinement, or random inspiration.  
        2. **Image Creation**: generate images from captions once finalized.  

    ## Persistence  
    - Continue iterating until you have fully satisfied the user's requested number of variants.

    ## Tool Calling  
    - **`web_search_preview`**: for up-to-date facts or context (no hallucinations).
    - **`summary_agent`**: to produce concise summaries (≤ 8 words).
    - **`meme_theme_generation_agent`**: to generate theme-based captions.  
    - **`meme_selection_agent`**: to refine or filter candidate captions.  
    - **`meme_random_inspiration_agent`**: to surprise the user with fresh captions.  
    - **`meme_image_generation_agent`**: to produce images; pass a payload like:
    ```json
    {
        "image_context": "A retro computer nerd",
        "text_boxes": {
        "text_box_1": "Hello",
        "text_box_2": "World"
        }
    }
    ## Output
    - Always return a string. When the output contains an image, supply the URL in a string.
    """,
    output_type=str,
)

# Exported for service.py
# __all__ = [
#     "main_agent",
#     "meme_theme_generation_agent",
#     "meme_selection_agent",
#     "meme_random_inspiration_agent",
#     "meme_image_generation_agent",
# ]
