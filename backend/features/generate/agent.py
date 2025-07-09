# backend/features/generate/agent.py
import os
import base64
import uuid
import mimetypes
import logfire
from dotenv import load_dotenv
from typing import List
from fastapi import HTTPException

from openai.types.responses import WebSearchToolParam
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.usage import UsageLimits
from pydantic_ai.models.openai import (
    OpenAIResponsesModel,
    OpenAIResponsesModelSettings,
)
from .models import MemeCaptionAndContext, ImageResult, Deps
from features.image_storage.service import upload_image_to_supabase
from features.user_memes.service import (
    create_user_meme,
    update_user_meme,
    read_latest_conversation_meme,
)
from features.user_memes.models import UserMemeCreate, UserMemeUpdate
from .helpers import convert_response_to_png


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
    # previous_response_id: str | None = None,
) -> ImageResult:
    """
    1) Ask OpenAI's image_generation tool for a base64-encoded PNG,
       including all text_boxes in the prompt.
    2) Decode and upload it to Supabase.
    3) Return ImageResult.
    """
    # Build a little “Top: …; Bottom: …; Caption3: …” string from whatever keys you got
    boxes_desc = "; ".join(f"{key}: “{val}”" for key, val in text_boxes.items())

    prompt = (
        f"Create a meme image with the following text boxes using Impact font (white, with black outline): {boxes_desc}."
        f" Take care creating the text layout and spacing to ensure it looks like a real meme."
        + (f" Image context: {context}" if context else "")
    )
    # Debug logging
    # print(f"Image generation prompt: {prompt}")

    # Synchronous call into the OpenAI client
    response = ctx.deps.client.responses.create(
        model="gpt-4.1-2025-04-14",
        input=prompt,
        tools=[{"type": "image_generation"}],
    )

    if not response.output:
        raise ModelRetry("No image generated. Please try again.")

    # Convert the response to PNG bytes, mime type, and filename
    # This function will extract the base64-encoded image from the response
    converted_image = convert_response_to_png(response)

    # upload directly to Supabase storage bucket
    public_url = upload_image_to_supabase(
        storage_bucket=AI_IMAGE_BUCKET,
        contents=converted_image.contents,
        original_filename=converted_image.filename,
        content_type=converted_image.mime_type,
    )

    # add the url to the user_meme database table
    data = UserMemeCreate(
        conversation_id=ctx.deps.conversation_id,
        image_url=public_url,
        openai_response_id=response.id,
    )

    def create_user_meme_operation():
        return create_user_meme(
            data=data, session=ctx.deps.session, current_user=ctx.deps.current_user
        )

    user_meme = safe_db_operation(create_user_meme_operation, ctx.deps.session)
    print(f"Created user meme with ID: {user_meme.id}")
    print(f"Response ID: {response.id}")
    return ImageResult(image_id=user_meme.id, url=public_url, response_id=response.id)


# ─── Image Modification Agent ──────────────────────────────────────────────────────
# This agent modifies existing meme images based on user requests
meme_image_modification_agent = Agent(
    model=model,
    model_settings=model_settings,
    deps_type=Deps,
    system_prompt="""
You are a Meme Image Modification Agent, part of a multi-agent workflow.
You will receive a prompt that contains a modification request and response ID in this format:
"Modify the previous image based on the following request: [MODIFICATION_REQUEST]. Pass the previous response ID: [RESPONSE_ID]."

Your job is to:
1. Parse the prompt to extract the modification request (the text between "request: " and ". Pass the previous")
2. Parse the prompt to extract the response ID (the text after "response ID: ")
3. Call the modify_image tool with these exact extracted values
4. Return the ImageResult object directly

Example:
Input: "Modify the previous image based on the following request: Change the dog to a cat. Pass the previous response ID: resp_123abc."
You should extract:
- modification_request: "Change the dog to a cat"
- response_id: "resp_123abc"

Then call: modify_image(modification_request="Change the dog to a cat", response_id="resp_123abc")
""",
    output_type=ImageResult,
)


@meme_image_modification_agent.tool
def modify_image(
    ctx: RunContext[Deps],
    modification_request: str,
    response_id: str,
) -> ImageResult:
    """
    Modify an existing meme image based on user request.
    """
    # Debug print
    print(
        f"Modification request from meme_image_modification_agent.tool: {modification_request}, response_id: {response_id}"
    )

    # Build the prompt for modification
    prompt = f"Modify the image based on the following request: {modification_request}."

    # Synchronous call into the OpenAI client
    response = ctx.deps.client.responses.create(
        model="gpt-4.1-2025-04-14",
        input=prompt,
        previous_response_id=response_id,
        tools=[{"type": "image_generation"}],
    )

    if not response.output:
        raise ModelRetry("No image generated. Please try again.")

    # Convert the response to PNG bytes, mime type, and filename
    # This function will extract the base64-encoded image from the response
    converted_image = convert_response_to_png(response)

    # upload directly to Supabase storage bucket
    public_url = upload_image_to_supabase(
        storage_bucket=AI_IMAGE_BUCKET,
        contents=converted_image.contents,
        original_filename=converted_image.filename,
        content_type=converted_image.mime_type,
    )

    # add the url to the user_meme database table
    data = UserMemeCreate(
        conversation_id=ctx.deps.conversation_id,
        image_url=public_url,
        openai_response_id=response.id,
    )

    def create_user_meme_operation():
        return create_user_meme(
            data=data, session=ctx.deps.session, current_user=ctx.deps.current_user
        )

    user_meme = safe_db_operation(create_user_meme_operation, ctx.deps.session)
    print(f"Created user meme with ID: {user_meme.id}")
    print(f"Response ID: {response.id}")
    return ImageResult(image_id=user_meme.id, url=public_url, response_id=response.id)


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
   - Call `meme_image_generation` once on the selected variant. You will be returned an `ImageResult` object.
   - The `ImageResult` will contain: image_id: str (the database uuid), url: str (storage bucket URL), response_id: str (the OpenAI `response.id`)
   - Stream back the image URL.

6. **Image Tweaks**
   - If the user wants to modify an image,” first call `fetch_previous_response_id` and retrieve the `response_id` e.g. `resp_686d406b0f08819bb6f77467aa2068e702a8423ad56bed0a`.
   - Then call `meme_image_modification` passing the `response_id` and the requested modifications.
   meme_image_modification(
       response_id=response_id,
       modification_request=modification_request
   )
   You will be returned an `ImageResult` object.
   - Stream back the image URL.
   
7. **Favourite Memes**
   - If the user ever requests to “favourite” or “save this meme,” call `favourite_meme_in_db`.

**Tools Available**
- `web_search_preview` for up-to-date context (optional).
- `meme_theme_factory` for theme-based captions.
- `meme_image_generation` for image rendering.
- `fetch_previous_response_id` to get the last image's response ID.
- `meme_image_modification` for image tweaks.
- `meme_caption_refinement` for user-supplied captions.
- `meme_random_inspiration` for random mode.
- `favourite_meme_in_db` to mark memes as favourites in the database.

**Output Content & Format**
Always maintain a friendly tone.
Avoid double newlines in your output.
When the image is ready, return the public URL enclosed in Markdown image syntax (e.g., `![](your_url_here)`).
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
) -> str:
    """
    Call the image generation agent to create a meme image.
    """
    # Debug print
    print(f"Generating image with text_boxes: {text_boxes}, context: {context}")
    prompt = (
        f"Create a meme image with the following text boxes: {', '.join(text_boxes.values())}."
        + (f" Image context: {context}" if context else "")
    )
    # Call the image generation agent synchronously
    result = meme_image_generation_agent.run_sync(
        prompt,
        deps=ctx.deps,
        usage=ctx.usage,
    )
    # Wrap the image URL in Markdown so the frontend renders it inline
    image_url = (
        result.output.url if hasattr(result.output, "url") else str(result.output)
    )
    return f"![]({image_url})"


@manager_agent.tool
def meme_image_modification(
    ctx: RunContext[Deps],
    modification_request: str,
    response_id: str,
) -> str:
    """
    Modify an existing meme image based on user request.
    """
    prompt = f"Modify the previous image based on the following request: {modification_request}. Pass the previous response ID: {response_id}."
    # Debug print
    print(
        f"Modification request from manager_agent.tool meme_image_modification: {modification_request}, response_id: {response_id}"
    )
    # Call the image modification agent synchronously
    result = meme_image_modification_agent.run_sync(
        prompt,
        deps=ctx.deps,
        usage=ctx.usage,
    )

    # Wrap the image URL in Markdown so the frontend renders it inline
    image_url = (
        result.output.url if hasattr(result.output, "url") else str(result.output)
    )
    return f"![]({image_url})"


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


@manager_agent.tool
def favourite_meme_in_db(ctx: RunContext[Deps]) -> str:
    """
    Mark a meme as favourite in the database.
    This function updates the `is_favorite` field of the UserMeme model.
    If the meme is not found, it returns a friendly message.
    """
    try:

        def mark_meme_as_favourite_operation():
            user_meme = read_latest_conversation_meme(
                conversation_id=ctx.deps.conversation_id,
                session=ctx.deps.session,
                current_user=ctx.deps.current_user,
            )
            if not user_meme or not user_meme.openai_response_id:
                raise HTTPException(
                    status_code=404, detail="No previous meme found to favourite"
                )
            update_user_meme(
                meme_id=user_meme.id,
                data=UserMemeUpdate(is_favorite=True),
                session=ctx.deps.session,
                current_user=ctx.deps.current_user,
            )
            return user_meme.id

        favourited_meme_id = safe_db_operation(
            mark_meme_as_favourite_operation, ctx.deps.session
        )
    except HTTPException as http_exception:
        if http_exception.status_code == 404:
            return http_exception.detail
        else:
            raise ModelRetry(f"Error favouriting meme: {http_exception.detail}")

    return f"Marked meme {favourited_meme_id} as favourite."


@manager_agent.tool
def fetch_previous_image_id(ctx: RunContext[Deps]) -> str:
    """
    Fetch the previous image ID for a given meme.
    This function retrieves the image ID from the UserMeme model.
    """

    def read_latest_conversation_meme_operation():
        return read_latest_conversation_meme(
            conversation_id=ctx.deps.conversation_id,
            session=ctx.deps.session,
            current_user=ctx.deps.current_user,
        )

    user_meme = safe_db_operation(
        read_latest_conversation_meme_operation, ctx.deps.session
    )

    # Add validation to ensure we have a valid response ID
    if not user_meme:
        raise ModelRetry("No previous meme found in this conversation.")

    if not user_meme.openai_response_id:
        raise ModelRetry("Previous meme does not have a valid OpenAI response ID.")

    # Debug logging to help identify the issue
    print(f"Retrieved response ID: {user_meme.openai_response_id}")

    return user_meme.openai_response_id


@manager_agent.tool
def fetch_previous_response_id(ctx: RunContext[Deps]) -> str:
    """
    Fetch the previous response ID for a given image ID.
    This function retrieves the OpenAI response ID from the UserMeme model.
    """

    def read_latest_conversation_meme_operation():
        return read_latest_conversation_meme(
            conversation_id=ctx.deps.conversation_id,
            session=ctx.deps.session,
            current_user=ctx.deps.current_user,
        )

    user_meme = safe_db_operation(
        read_latest_conversation_meme_operation, ctx.deps.session
    )

    # Add validation to ensure we have a valid response ID
    if not user_meme:
        raise ModelRetry("No previous meme found in this conversation.")

    if not user_meme.openai_response_id:
        raise ModelRetry("Previous meme does not have a valid OpenAI response ID.")

    # Debug logging to help identify the issue
    print(f"Retrieved response ID: {user_meme.openai_response_id}")

    return user_meme.openai_response_id


# Helper function to safely handle database operations in agent context
def safe_db_operation(operation, session, max_retries=3):
    """
    Safely execute database operations with retry logic and proper error handling.
    This helps prevent connection pool exhaustion in long-running agent operations.
    """
    from sqlalchemy.exc import OperationalError
    import time

    for attempt in range(max_retries):
        try:
            return operation()
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(
                    f"Database operation failed (attempt {attempt + 1}), retrying: {e}"
                )
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            else:
                print(f"Database operation failed after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            print(f"Unexpected error in database operation: {e}")
            raise
