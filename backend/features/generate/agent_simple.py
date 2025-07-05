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

# ─── Meme Image Generation Agent ───────────────────────────────────────────
image_generator_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
You are a meme image generator: given a list of captions, produce URLs or binary data URLs
for each image. Return JSON like:
{"images":[{"caption_id":0,"url":"..."},…]}
""",
    # You could define a ResponseImages schema here if desired
)

@image_generator_agent.tool
async def meme_image_factory(

# ─── Meme Main Generation Agent ───────────────────────────────────────────
main_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
    You are a meme generation agent: given a user request, generate a complete meme.
    This includes generating captions, selecting the best ones, and creating the final image.
    """,
    output_type=str, # Assuming the output is a URL to the meme
)
