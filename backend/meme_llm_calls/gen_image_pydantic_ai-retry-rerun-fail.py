# backend/features/generate/image_agent.py

import os
import uuid
import base64
from dataclasses import dataclass

from dotenv import load_dotenv
import logfire
from openai import OpenAI
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from openai.types.responses import WebSearchToolParam

from features.image_storage.service import upload_image_to_supabase

# ─── Bootstrap ─────────────────────────────────────────────────────────────
load_dotenv()
logfire.configure()
logfire.instrument_pydantic_ai()

AI_IMAGE_BUCKET = os.getenv("AI_IMAGE_BUCKET", "memes")


# ─── Dependency container ───────────────────────────────────────────────────
@dataclass
class Deps:
    client: OpenAI


# ─── Input Context for Image Generation Tool ────────────────────────────────
class ImageGenerationContext(BaseModel):
    text_boxes: dict[str, str]  # e.g. {"text_box_1": "Hello", "text_box_2": "World"}
    context: str = ""  # optional scene or style notes


# ─── Tool output schema ─────────────────────────────────────────────────────
class ImageResult(BaseModel):
    url: str  # public Supabase URL
    response_id: str  # OpenAI response.id (for internal use)


# ─── Agent configuration ────────────────────────────────────────────────────
model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[WebSearchToolParam(type="web_search_preview")],
    allow_tools=True,
)
model = OpenAIResponsesModel("gpt-4.1-2025-04-14")

meme_image_generation_agent = Agent(
    model=model,
    model_settings=model_settings,
    deps_type=Deps,
    output_type=ImageResult,
    instructions="""
You are the Meme Image Generation Agent.

On the first user request, call the `image_generation` tool with an ImageGenerationContext payload containing:
  • text_boxes: a map of caption positions to text  
  • context: optional style or scene notes

Store the returned ImageResult.response_id internally.  
If the user asks to modify the last image (e.g. “make it more realistic”), call `image_generation` again, passing the previous response_id as `previous_response_id`.  

Never expose response_id to the user; reply only with the final image.  

After the tool runs, your reply must be exactly:

```markdown
![Your meme]({{url}})
""",
)
# ─── Unified tool for generate & edit ───────────────────────────────────────


@meme_image_generation_agent.tool
def image_generation(
    ctx: RunContext[Deps],
    payload: ImageGenerationContext,
    previous_response_id: str | None = None,
) -> ImageResult:
    """
    Build a prompt from payload, call OpenAI's image_generation tool,
    upload the result to Supabase, and return an ImageResult.
    Retries if no image is returned.
    """
    # Build the prompt
    desc = "; ".join(f"{k}: {v}" for k, v in payload.text_boxes.items())
    prompt = f"Create a meme image with {desc}"
    if payload.context:
        prompt += f"; style/context: {payload.context}"

    # Prepare request
    req = {
        "model": "gpt-4.1-2025-04-14",
        "input": prompt,
        "tools": [{"type": "image_generation"}],
    }
    if previous_response_id:
        req["previous_response_id"] = previous_response_id

    # Call OpenAI (sync)
    resp = ctx.deps.client.responses.create(**req)

    # Extract the first image
    for out in resp.output:
        if out.type == "image_generation_call":
            b64 = out.result
            if b64.startswith("data:"):
                b64 = b64.split(",", 1)[1]
            data = base64.b64decode(b64)
            filename = f"{uuid.uuid4().hex}.png"
            public_url = upload_image_to_supabase(AI_IMAGE_BUCKET, data, filename)
            return ImageResult(url=public_url, response_id=resp.id)

    # Let the agent retry if no image
    raise ModelRetry("OpenAI returned no image")


# ─── Quick CLI test (dev only) ─────────────────────────────────────────────

if __name__ == "__main__":
    client = OpenAI()
    deps = Deps(client=client)
    first = meme_image_generation_agent.run_sync(
        "Generate a meme of a cat sat at a computer: top 'Hello', bottom 'World', cartoon style",
        deps=deps,
    )
    print("First run:", first.output)

    edit = meme_image_generation_agent.run_sync(
        "Make that image look more realistic",
        deps=deps,
    )
    print("Second run:", edit.output)
