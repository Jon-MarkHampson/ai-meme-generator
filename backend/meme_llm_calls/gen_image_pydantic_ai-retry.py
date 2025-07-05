# backend/features/generate/image_agent.py
import os
import base64
import uuid
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

AI_IMAGE_BUCKET = os.getenv("AI_IMAGE_BUCKET", "memes")  # Default bucket name

# ─── OpenAI‐Responses Model ─────────────────────────────────────────────────
model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[WebSearchToolParam(type="web_search_preview")],
    allow_tools=True,
)
model = OpenAIResponsesModel("gpt-4.1-2025-04-14")


# ─── Dependency Container ───────────────────────────────────────────────────
@dataclass
class Deps:
    client: OpenAI


# ─── Image Generation Context ───────────────────────────────────────────────
class ImageGenerationContext(BaseModel):
    text_boxes: dict[str, str]  # e.g. {"text_box_1": "Hello", "text_box_2": "World"}
    context: str = ""  # optional scene or style notes


# ─── Pydantic AI Result Model ────────────────────────────────────────────────
class ImageResult(BaseModel):
    url: str  # the Supabase URL
    response_id: str  # the OpenAI `response.id` you got back


# ─── Image‐Generation Agent ─────────────────────────────────────────────────
meme_image_generation_agent = Agent(
    model=model,
    model_settings=model_settings,
    deps_type=Deps,
    system_prompt="""
    You are a Meme Image Generation Agent.  
    When invoked, you must call the `image_generation` tool with:
    ImageGenerationContext(text_boxes=<dict of text boxes>, context=<optional context>) & optionally the previous image generation attempts attempts response_id.
    The `image_generation` tool will return an `ImageResult` which will contain the public URL to the generated image and the response ID.
    Store the the response_id for incase the user make a follow-up request to regenerate the image.
    """,
)


@meme_image_generation_agent.tool
def image_generation(
    ctx: RunContext[None],
    image_context: ImageGenerationContext,
    response_id: str | None = None,
) -> ImageResult:
    """
    1) Ask OpenAI's image_generation tool for a base64-encoded PNG,
       including all text_boxes in the prompt.
    2) Decode and upload it to Supabase.
    3) Return ImageResult.
    """
    # Build a little “Top: …; Bottom: …; Caption3: …” string from whatever keys you got
    boxes_desc = "; ".join(
        f"{key}: “{val}”" for key, val in image_context.text_boxes.items()
    )

    prompt = f"Create a meme image with the following text boxes: {boxes_desc}." + (
        f" Context: {image_context.context}" if image_context.context else ""
    )

    # Synchronous call into the OpenAI client
    response = ctx.deps.client.responses.create(
        model="gpt-4.1-2025-04-14",
        input=prompt,
        tools=[{"type": "image_generation"}],
    )

    # Find the first image payload
    for output in response.output:
        if output.type == "image_generation_call":
            image_b64 = output.result
            # strip any data-url header
            if image_b64.startswith("data:"):
                image_b64 = image_b64.split(",", 1)[1]

            contents = base64.b64decode(image_b64)
            filename = f"{uuid.uuid4().hex}.png"

            # upload directly to Supabase
            public_url = upload_image_to_supabase(AI_IMAGE_BUCKET, contents, filename)

            return ImageResult(url=public_url, response_id=response.id)

    # If no image came back, ask agent to retry
    raise ModelRetry("No image returned from OpenAI image_generation tool")


# ─── Quick CLI Test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    client = OpenAI()
    deps = Deps(client=client)
    first_run = meme_image_generation_agent.run_sync(
        "Generate a meme of a nerd at a computer with Hello/World captions in cartoon style",
        deps=deps,
    )
    print("Saved image:", first_run.output)

    second_run = meme_image_generation_agent.run_sync(
        "Make the image more realistic",
        deps=deps,
    )
    print("Saved image:", second_run.output)
