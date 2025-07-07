# backend/features/generate/agent.py
import os
import base64
import uuid
import mimetypes
import logfire
from dotenv import load_dotenv
from typing import List

from openai.types.responses import WebSearchToolParam
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.usage import UsageLimits
from pydantic_ai.models.openai import (
    OpenAIResponsesModel,
    OpenAIResponsesModelSettings,
)
from .models import MemeCaptionAndContext, ImageResult, Deps
from features.image_storage.service import upload_image_to_supabase

load_dotenv()
logfire.configure()
logfire.instrument_pydantic_ai()

AI_IMAGE_BUCKET = os.getenv("AI_IMAGE_BUCKET", "memes")  # Default bucket name

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
You are a meme-caption factory.
Your job is to generate meme captions and, if needed, image context, and emit only valid JSON matching this exact schema:

{
"text_boxes": {
    "text_box_1": "<string>",
    "text_box_2": "<string>"
},
"context": "<string>"
}

- Include at least two text boxes; if the user requests more boxes, add additional keys (e.g., "text_box_3").
- If `image_context` is blank, invent a fitting scene and place it in `context`.
- Do NOT include any extra fields, markdown syntax, code fences, or explanatory text—output ONLY the JSON object.
""",
    output_type=MemeCaptionAndContext,
)


# ─── Image‐Generation Agent ─────────────────────────────────────────────────
meme_image_generation_agent = Agent(
    model=model,
    model_settings=model_settings,
    deps_type=Deps,
    system_prompt="""
You are the Meme Image Generation Agent in a multi-agent workflow.
Your manager will hand you a single string containing JSON with these keys:
{
  "text_boxes": { 
    "text_box_1": "<string>",
    "text_box_2": "<string>",
    … 
  },
  "context": "<string>",           
  "previous_response_id": "<string>"  # or null
}
Your job is:
1. Parse that input string into:
   - a dict[str, str] for `text_boxes`
   - a str for `context`
   - a str or None for `previous_response_id`
2. Invoke the `image_generation` tool exactly once:
   image_generation(
     text_boxes=text_boxes,
     context=context,
     previous_response_id=previous_response_id
   )
3. Receive an `ImageResult` from the tool, and return that object directly. Do not emit any additional text, comments, or formatting.
""",
    output_type=ImageResult,
)


# ─── Image Generation Tool ─────────────────────────────────────────────────
@meme_image_generation_agent.tool
def image_generation(
    ctx: RunContext[Deps],
    text_boxes: dict[str, str],
    context: str = "",
    previous_response_id: str | None = None,
) -> ImageResult:
    """
    1) Ask OpenAI's image_generation tool for a base64-encoded PNG,
       including all text_boxes in the prompt.
    2) Decode and upload it to Supabase.
    3) Return ImageResult.
    """
    # Build a little “Top: …; Bottom: …; Caption3: …” string from whatever keys you got
    boxes_desc = "; ".join(f"{key}: “{val}”" for key, val in text_boxes.items())

    if previous_response_id:
        prompt = (
            f"Rerun the image generation with the previous response ID: {previous_response_id}. "
            f"Create a meme image with the following text boxes: {boxes_desc}."
            + (f" Image context: {context}" if context else "")
        )
    else:
        prompt = (
            f"Create a meme image with the following text boxes using Impact font: {boxes_desc}."
            + (f" Image context: {context}" if context else "")
        )
    # Debug logging
    # print(f"Image generation prompt: {prompt}")

    # Synchronous call into the OpenAI client
    response = ctx.deps.client.responses.create(
        model="gpt-4.1-2025-04-14",
        previous_response_id=previous_response_id,
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

            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                # Default to PNG if we can't guess the type
                mime_type = "image/png"

            # upload directly to Supabase
            public_url = upload_image_to_supabase(
                AI_IMAGE_BUCKET, contents, filename, content_type=mime_type
            )

            return ImageResult(url=public_url, response_id=response.id)

    # If no image came back, ask agent to retry
    raise ModelRetry("No image returned from OpenAI image_generation tool")


# ─── Caption Refinement Agent ──────────────────────────────────────────────
meme_caption_refinement_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
You are a Meme Caption Refinement Agent.
Your job is to take a user-supplied meme caption (and optional image context), and rewrite or improve it, splitting it into text boxes as needed for a meme image.
Output only valid JSON matching this schema:
{
  "text_boxes": {
    "text_box_1": "<string>",
    "text_box_2": "<string>"
  },
  "context": "<string>"
}
- If there is only one line, split it into two if possible (top/bottom).
- If context is missing, invent a fitting scene and place it in "context".
- Do NOT include any extra fields, markdown, or explanatory text—output ONLY the JSON object.
""",
    output_type=MemeCaptionAndContext,
)

# ─── Random Inspiration Agent ──────────────────────────────────────────────
meme_random_inspiration_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt="""
You are a Meme Random Inspiration Agent.
Your job is to invent a random, humorous meme caption and scene, and output it as valid JSON:
{
  "text_boxes": {
    "text_box_1": "<string>",
    "text_box_2": "<string>"
  },
  "context": "<string>"
}
Do not include any extra text, markdown, or explanations—output ONLY the JSON object.
""",
    output_type=MemeCaptionAndContext,
)


# ─── Manager Agent ──────────────────────────────────────────────────────────
manager_agent = Agent(
    model=model,
    model_settings=model_settings,
    deps_type=Deps,
    system_prompt="""
You are a friendly and efficient Meme Manager Agent. You coordinate meme creation in two phases: caption generation and image creation.

1. **Classify User Input**
   Determine which mode the user wants:
   - **themes**: user provides a list of keywords.
   - **caption**: user provides full caption text (and optional image context).
   - **random**: user requests random inspiration.

2. **Gather Missing Information**
   - If keywords or captions are missing, ask the user for exactly what's missing.
   - If image context is needed or user supplied, capture it.

3. **Generate Captions**
    For each of the below modes generate three variants:
    Format the output like Option #1, Option #2, Option #3.
   - For **themes** mode, call `meme_theme_factory(keywords, image_context)`
   - For **caption** mode, call `meme_caption_refinement_agent`
   - For **random** mode, call `meme_random_inspiration_agent`
   Stream back the three caption+context variants.

4. **Caption Selection**
   - Wait for the user to pick one variant (e.g., “I choose #2”).

5. **Generate Image**
   - Call `meme_image_generation` once on the selected variant.
   - Stream back the image URL.

6. **Image Tweaks**
   - If the user says “tweak” or “make it X,” call `meme_image_generation` again with the same `text_boxes`, `context`, and the `previous_response_id`.

**Tools Available**
- `web_search_preview` for up-to-date context (optional).
- `meme_theme_factory` for theme-based captions.
- `meme_image_generation` for image rendering.
- `meme_caption_refinement` for user-supplied captions.
- `meme_random_inspiration` for random mode.

**Output Content & Format**
Always maintain a friendly tone.
Avoid double newlines in your output.
When the image is ready, return the public URL as a string.
""",
    output_type=str,
)


@manager_agent.tool
async def meme_theme_factory(
    ctx: RunContext[Deps], keywords: List[str], image_context: str = ""
) -> MemeCaptionAndContext:
    # simply forward to the theme agent, preserving usage tracking
    r = await meme_theme_generation_agent.run(
        f"Themes: {', '.join(keywords)}; Context: {image_context}",
        usage=ctx.usage,
    )
    return r.output


@manager_agent.tool
def meme_image_generation(
    ctx: RunContext[Deps],
    text_boxes: dict[str, str],
    context: str = "",
    previous_response_id: str | None = None,
) -> ImageResult:
    """
    Call the image generation agent to create a meme image.
    """
    # Debug print
    print(
        f"Generating image with text_boxes: {text_boxes}, context: {context}, previous_response_id: {previous_response_id}"
    )
    prompt = (
        f"Create a meme image with the following text boxes: {', '.join(text_boxes.values())}."
        + (f" Image context: {context}" if context else "")
        + (
            f" (previous response ID: {previous_response_id})"
            if previous_response_id
            else ""
        )
    )
    # Call the image generation agent synchronously
    result = meme_image_generation_agent.run_sync(
        prompt,
        deps=ctx.deps,
        usage=ctx.usage,
    )
    return result.output


# ─── Meme Caption Refinement Tool ──────────────────────────────────────────
@manager_agent.tool
def meme_caption_refinement(
    ctx: RunContext[Deps], caption: str, image_context: str = ""
) -> MemeCaptionAndContext:
    """
    Refine or rewrite a user-supplied meme caption (and optional context) into perfect meme caption(s) and context.
    """
    prompt = f"Caption: {caption}; Context: {image_context}"
    r = meme_caption_refinement_agent.run_sync(prompt, usage=ctx.usage)
    return r.output


# ─── Meme Random Inspiration Tool ──────────────────────────────────────────
@manager_agent.tool
def meme_random_inspiration(ctx: RunContext[Deps]) -> MemeCaptionAndContext:
    """
    Generate a random meme caption and context.
    """
    prompt = "Invent a random meme caption and fitting context."
    r = meme_random_inspiration_agent.run_sync(prompt, usage=ctx.usage)
    return r.output


# Exported for service.py
# __all__ = [
#     "main_agent",
#     "meme_theme_generation_agent",
#     "meme_selection_agent",
#     "meme_random_inspiration_agent",
#     "meme_image_generation_agent",
# ]
