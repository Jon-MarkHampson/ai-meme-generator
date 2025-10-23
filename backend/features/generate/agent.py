# backend/features/generate/agent.py
import logging
import os
import time
import uuid
from io import BytesIO
from typing import List

import logfire
from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import types
from openai import BadRequestError
from openai.types.responses import WebSearchToolParam
from PIL import Image
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import (OpenAIResponsesModel,
                                       OpenAIResponsesModelSettings)
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits
from sqlalchemy.exc import OperationalError

from features.conversations.schema import ConversationUpdate
from features.image_storage.service import (download_image_from_supabase,
                                            upload_image_to_supabase)
from features.user_memes.schema import UserMemeCreate, UserMemeUpdate
from features.user_memes.service import (create_user_meme,
                                         read_latest_conversation_meme,
                                         read_user_meme, update_user_meme)

from .agent_instructions.manager_agent import manager_agent_instructions
from .helpers import convert_gemini_response_to_png, convert_response_to_png
from .schema import Deps, ImageResult, MemeCaptionAndContext

load_dotenv()

logger = logging.getLogger(__name__)

logfire.configure()
logfire.instrument_pydantic_ai()

AI_IMAGE_BUCKET = os.getenv("AI_IMAGE_BUCKET", "memes")

model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[WebSearchToolParam(type="web_search_preview")]
)
model = OpenAIResponsesModel("gpt-4.1-2025-04-14")

# Summarize agent for conversation history management
summarize_agent = Agent(
    "openai:gpt-4o-mini",
    instructions="""
Summarize this conversation, omitting small talk and unrelated topics.
Focus on the technical discussion and next steps.
""",
)


async def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    # Summarize the oldest messages to keep recent context
    # Keep at least the last 5 messages to preserve recent conversation flow
    if len(messages) > 15:
        oldest_messages = messages[:10]
        summary = await summarize_agent.run(message_history=oldest_messages)
        # Return the summary plus the last 5 messages to preserve recent context
        return summary.new_messages() + messages[-5:]

    return messages


# ─── Meme Theme Generation Agent ──────────────────────────────────────────
meme_theme_generation_agent = Agent(
    model=model,
    model_settings=model_settings,
    instructions="""
You are an expert meme creator who understands internet humor, viral content, and what makes people laugh online.

# MEME WRITING PRINCIPLES

**Structure:**
- Text Box 1 (Top): Setup - establishes context with maximum 8 words
- Text Box 2 (Bottom): Punchline - delivers the humor with maximum 8 words
- Think: "When X happens" (top) → "Relatable/absurd response" (bottom)

**Style Rules:**
- ULTRA CONCISE: 3-8 words per text box. Brevity = impact.
- USE INTERNET VERNACULAR: "POV", "Nobody:", "Me:", "Literally", casual slang
- DON'T EXPLAIN: Let the image do half the work
- NO COMPLETE SENTENCES: Fragments are funnier
- EXAGGERATE: Push the absurdity, don't be literal
- USE CONTRAST: Unexpected juxtapositions create humor

**Common Meme Formats to Consider:**
- "Nobody: / [Subject]: [absurd action]" - highlights unprompted behavior
- "POV: [relatable scenario]" - first-person perspective
- "Me: [normal thing] / Also me: [contradictory thing]" - self-aware humor
- "When [situation] / [reaction]" - relatable scenarios
- "[Thing A]: exists / [Person/Thing]: [overreaction]" - exaggerated responses
- "They don't know that..." - social awkwardness
- Simple contrast: "[Serious thing] / [Absurd response]"

**What Makes Memes Funny:**
- Relatability (shared experiences)
- Absurdist exaggeration (taking things too far)
- Self-deprecation (roasting yourself)
- Subverting expectations (setup → surprising twist)
- Pop culture references (when appropriate)
- Timing and current relevance
- The unspoken truth (saying what everyone thinks)

**What to AVOID:**
- ❌ Explaining the joke in the text
- ❌ Long sentences or over-description  
- ❌ Being too literal or journalistic
- ❌ Repeating information between boxes
- ❌ Formal language or complete grammar
- ❌ Describing what's in the image

**Context Field Guidelines:**
- Describe the VISUAL SCENE for the image generator
- Be specific about expressions, poses, and atmosphere
- DON'T repeat the text box content
- Focus on what makes the image funny or impactful
- Include relevant visual details: setting, characters, style, mood
- Think cinematically: "wide shot of...", "close-up on...", "dramatic lighting"

# EXAMPLES OF GOOD VS BAD MEMES

**BAD (too literal, explanatory):**
Top: "Protesters say 'No Kings'"
Bottom: "Trump responds by making AI video as king"
Context: Trump dressed as king responding to protesters

**GOOD (concise, absurdist):**
Top: "Millions: NO KINGS"
Bottom: "Trump: *opens AI generator*"
Context: Split scene - massive protest crowd on left, Trump alone at computer with mischievous grin on right, golden crown poorly photoshopped floating above his head

**BAD:**
Top: "President Trump releases video"
Bottom: "Using artificial intelligence technology to mock protesters"

**GOOD:**
Top: "7 million people: We want democracy"
Bottom: "Trump: lol watch this AI go brrrr"
Context: Protest signs filling frame with "No Kings" messages, overlaid with Windows Movie Maker-style effects and cheesy crown graphics

# YOUR OUTPUT FORMAT

You MUST output ONLY valid JSON with this exact schema:

{
  "text_boxes": {
    "text_box_1": "<punchy setup, 3-8 words>",
    "text_box_2": "<punchy punchline, 3-8 words>"
  },
  "context": "<detailed visual scene description for image generator>"
}

**Critical Rules:**
- NO markdown, NO code fences, NO extra text
- JUST the JSON object
- Keep text boxes SHORT (3-8 words max)
- Make context DETAILED (2-3 sentences about the visual scene)
- Include multiple text boxes if requested (text_box_3, etc.)
- If no image_context provided, invent a fitting visual scene

**Remember:** You're not writing news headlines. You're creating viral internet content that makes people laugh and share. Be bold, be absurd, be concise!
""",
    output_type=MemeCaptionAndContext,
)

# ─── User Request Summary Agent ──────────────────────────────────────────
user_request_summary_agent = Agent(
    model="openai:gpt-4o-mini",
    model_settings=model_settings,
    instructions="""
You are a User Request Summary Agent.
Your job is to summarise the user request.
The summary should be concise and capture the essence of the user's request.
The summary should be less than 10 words. Omitting any intial actions like 'create a meme' or 'generate a meme'.
e.g. Input: "The user wants a meme about Donald Trump and Elon Musk's falling out.
The chosen caption is: 'When you used to retweet each other / But now you subtweet each other.'
The image context should show Trump and Musk standing back to back, arms crossed, both looking away with frustrated expressions."
    Output: "Trump and Musk's falling out"
""",
    output_type=str,
)

# ─── Image Generation Agent ──────────────────────────────────────────────
meme_image_generation_agent = Agent(
    model=model,
    model_settings=model_settings,
    deps_type=Deps,
    instructions="""
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


# ─── Image Generation Tool (UNIFIED) ─────────────────────────────────────
@meme_image_generation_agent.tool
def image_generation(
    ctx: RunContext[Deps],
    text_boxes: dict[str, str],
    context: str = "",
) -> ImageResult:
    """
    Generate image using either OpenAI or Gemini based on image_agent_model setting.
    Routes to the appropriate provider automatically.
    """
    # Parse the image_agent_model to determine provider
    provider, model_name = ctx.deps.image_agent_model.split(":")
    provider = provider.lower()

    print(f"Image generation with provider: {provider}, model: {model_name}")
    print(f"Text boxes: {text_boxes}, context: {context}")

    if provider == "openai":
        return _generate_image_openai(ctx, text_boxes, context)
    elif provider == "gemini":
        return _generate_image_gemini(ctx, text_boxes, context)
    else:
        raise ValueError(f"Unsupported image generation provider: {provider}")


def _generate_image_openai(
    ctx: RunContext[Deps],
    text_boxes: dict[str, str],
    context: str = "",
) -> ImageResult:
    """
    Generate image using OpenAI's image generation API.
    """
    boxes_desc = "; ".join(f"{key}: '{val}'" for key, val in text_boxes.items())

    prompt = (
        f"Create a meme image with the following text boxes using Impact font "
        f"(white, with black outline): {boxes_desc}."
        f" Take care creating the text layout and spacing to ensure it looks like a real meme."
        + (f" Image context: {context}" if context else "")
    )

    print(f"OpenAI image generation prompt: {prompt}")

    try:
        response = ctx.deps.client.responses.create(
            model="gpt-4.1-2025-04-14",
            input=prompt,
            tools=[{"type": "image_generation"}],
        )
    except BadRequestError as e:
        error_msg = str(e)
        if "moderation_blocked" in error_msg or "safety system" in error_msg:
            raise ModelRetry(
                "I'm sorry, but I can't create that meme as it was flagged by the "
                "content safety system. Please try a different caption or theme."
            )
        else:
            raise ModelRetry(f"Image generation failed: {error_msg}. Please try again.")
    except Exception as e:
        raise ModelRetry(f"Image generation failed: {str(e)}. Please try again.")

    if not response.output:
        raise ModelRetry("No image generated. Please try again.")

    # Convert OpenAI response to PNG
    converted_image = convert_response_to_png(response)

    # Upload to Supabase
    public_url = upload_image_to_supabase(
        storage_bucket=AI_IMAGE_BUCKET,
        contents=converted_image.contents,
        original_filename=converted_image.filename,
        content_type=converted_image.mime_type,
    )

    # Save to database
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
    print(f"OpenAI Response ID: {response.id}")

    return ImageResult(image_id=user_meme.id, url=public_url, response_id=response.id)


def _generate_image_gemini(
    ctx: RunContext[Deps],
    text_boxes: dict[str, str],
    context: str = "",
) -> ImageResult:
    """
    Generate image using Gemini's image generation API (Nano Banana).
    Creates a fresh chat session for each generation.
    """
    boxes_desc = "; ".join(f"{key}: '{val}'" for key, val in text_boxes.items())

    prompt = (
        f"Create a meme image with the following text boxes using Impact font "
        f"(white, with black outline): {boxes_desc}."
        f" Take care creating the text layout and spacing to ensure it looks like a real meme."
        + (f" Image context: {context}" if context else "")
    )

    print(f"Gemini image generation prompt: {prompt}")

    try:
        # Create fresh Gemini client and chat for this generation
        gemini_client = genai.Client()
        gemini_chat = gemini_client.chats.create(
            model="gemini-2.5-flash-image",
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        # Send message to generate image
        response = gemini_chat.send_message(prompt)

    except Exception as e:
        error_msg = str(e)
        if "moderation_blocked" in error_msg or "safety system" in error_msg:
            raise ModelRetry(
                "I'm sorry, but I can't create that meme as it was flagged by the "
                "content safety system. Please try a different caption or theme."
            )
        else:
            raise ModelRetry(f"Image generation failed: {error_msg}. Please try again.")

    # Validate response structure
    if (
        not response.candidates
        or not response.candidates[0].content
        or not response.candidates[0].content.parts
    ):
        raise ModelRetry("No image generated. Please try again.")

    # Debug: log text responses and save local copy
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(f"Gemini text response: {part.text}")
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            image.save("generated_image_MEME_by_Nano_Banana.png")
            print("Saved local copy to: generated_image_MEME_by_Nano_Banana.png")

    # Convert Gemini response to PNG
    converted_image = convert_gemini_response_to_png(response)

    # Upload to Supabase
    public_url = upload_image_to_supabase(
        storage_bucket=AI_IMAGE_BUCKET,
        contents=converted_image.contents,
        original_filename=converted_image.filename,
        content_type=converted_image.mime_type,
    )

    # Generate UUID for Gemini (no native response ID)
    gemini_response_id = f"gemini_{uuid.uuid4().hex}"

    # Save to database
    data = UserMemeCreate(
        conversation_id=ctx.deps.conversation_id,
        image_url=public_url,
        openai_response_id=gemini_response_id,
    )

    def create_user_meme_operation():
        return create_user_meme(
            data=data, session=ctx.deps.session, current_user=ctx.deps.current_user
        )

    user_meme = safe_db_operation(create_user_meme_operation, ctx.deps.session)
    print(f"Created user meme with ID: {user_meme.id}")
    print(f"Gemini Response ID: {gemini_response_id}")

    return ImageResult(
        image_id=user_meme.id, url=public_url, response_id=gemini_response_id
    )


# ─── Image Modification Agent ────────────────────────────────────────────
meme_image_modification_agent = Agent(
    model=model,
    model_settings=model_settings,
    deps_type=Deps,
    instructions="""
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


# ─── Image Modification Tool (UNIFIED) ───────────────────────────────────
@meme_image_modification_agent.tool
def modify_image(
    ctx: RunContext[Deps],
    modification_request: str,
    response_id: str,
) -> ImageResult:
    """
    Modify existing image using either OpenAI or Gemini based on image_agent_model.
    Routes to the appropriate provider automatically.
    """
    # Parse the image_agent_model to determine provider
    provider, model_name = ctx.deps.image_agent_model.split(":")
    provider = provider.lower()

    print(f"Image modification with provider: {provider}")
    print(f"Modification request: {modification_request}, response_id: {response_id}")

    if provider == "openai":
        return _modify_image_openai(ctx, modification_request, response_id)
    elif provider == "gemini":
        return _modify_image_gemini(ctx, modification_request, response_id)
    else:
        raise ValueError(f"Unsupported image modification provider: {provider}")


def _modify_image_openai(
    ctx: RunContext[Deps],
    modification_request: str,
    response_id: str,
) -> ImageResult:
    """
    Modify image using OpenAI's previous_response_id feature.
    """
    prompt = f"Modify the image based on the following request: {modification_request}."

    print(f"OpenAI modification prompt: {prompt}")

    try:
        response = ctx.deps.client.responses.create(
            model="gpt-4.1-2025-04-14",
            input=prompt,
            previous_response_id=response_id,
            tools=[{"type": "image_generation"}],
        )
    except BadRequestError as e:
        error_msg = str(e)
        if "moderation_blocked" in error_msg or "safety system" in error_msg:
            raise ModelRetry(
                "I'm sorry, but I can't modify that image as the request was flagged "
                "by the content safety system."
            )
        else:
            raise ModelRetry(
                f"Image modification failed: {error_msg}. Please try again."
            )
    except Exception as e:
        raise ModelRetry(f"Image modification failed: {str(e)}. Please try again.")

    if not response.output:
        raise ModelRetry("No image generated. Please try again.")

    # Convert OpenAI response to PNG
    converted_image = convert_response_to_png(response)

    # Upload to Supabase
    public_url = upload_image_to_supabase(
        storage_bucket=AI_IMAGE_BUCKET,
        contents=converted_image.contents,
        original_filename=converted_image.filename,
        content_type=converted_image.mime_type,
    )

    # Save to database
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
    print(f"Created modified meme with ID: {user_meme.id}")
    print(f"OpenAI Response ID: {response.id}")

    return ImageResult(image_id=user_meme.id, url=public_url, response_id=response.id)


def _modify_image_gemini(
    ctx: RunContext[Deps],
    modification_request: str,
    response_id: str,
) -> ImageResult:
    """
    Modify image using Gemini by fetching and passing the previous image explicitly.
    Gemini requires the actual image data to perform modifications.
    """
    prompt = f"Modify the previous image based on this request: {modification_request}"

    print(f"Gemini modification prompt: {prompt}")
    print(f"Fetching previous image with response_id: {response_id}")

    try:
        # Step 1: Find the previous meme by looking for the meme with this response_id
        def find_previous_meme_operation():
            # Get the latest meme from this conversation
            latest_meme = read_latest_conversation_meme(
                conversation_id=ctx.deps.conversation_id,
                session=ctx.deps.session,
                current_user=ctx.deps.current_user,
            )
            if not latest_meme or latest_meme.openai_response_id != response_id:
                raise ModelRetry(
                    f"Could not find previous image with response_id: {response_id}"
                )
            return latest_meme

        previous_meme = safe_db_operation(find_previous_meme_operation, ctx.deps.session)
        print(f"Found previous meme: {previous_meme.id}, URL: {previous_meme.image_url}")

        # Step 2: Extract filename from the public URL
        # URL format: https://...supabase.co/storage/v1/object/public/memes/filename.png
        image_url = previous_meme.image_url
        filename = image_url.split("/")[-1]  # Extract filename from URL
        print(f"Extracted filename: {filename}")

        # Step 3: Download the image from Supabase
        image_bytes = download_image_from_supabase(
            storage_bucket=AI_IMAGE_BUCKET,
            filename=filename,
        )
        print(f"Downloaded {len(image_bytes)} bytes")

        # Step 4: Load image as PIL.Image for Gemini
        previous_image = Image.open(BytesIO(image_bytes))
        print(f"Loaded PIL Image: {previous_image.size}, mode: {previous_image.mode}")

        # Step 5: Create fresh Gemini client and chat, then pass both prompt and image
        gemini_client = genai.Client()
        gemini_chat = gemini_client.chats.create(
            model="gemini-2.5-flash-image",
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        # Send modification request WITH the previous image
        response = gemini_chat.send_message([prompt, previous_image])

    except ModelRetry:
        # Re-raise ModelRetry exceptions
        raise
    except Exception as e:
        error_msg = str(e)
        if "moderation_blocked" in error_msg or "safety system" in error_msg:
            raise ModelRetry(
                "I'm sorry, but I can't modify that image as the request was flagged "
                "by the content safety system."
            )
        else:
            raise ModelRetry(
                f"Image modification failed: {error_msg}. Please try again."
            )

    # Validate response structure
    if (
        not response.candidates
        or not response.candidates[0].content
        or not response.candidates[0].content.parts
    ):
        raise ModelRetry("No modified image generated. Please try again.")

    # Debug: log responses
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(f"Gemini text response: {part.text}")
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            image.save("modified_image_MEME_by_Nano_Banana.png")
            print("Saved modified copy to: modified_image_MEME_by_Nano_Banana.png")

    # Convert Gemini response to PNG
    converted_image = convert_gemini_response_to_png(response)

    # Upload to Supabase
    public_url = upload_image_to_supabase(
        storage_bucket=AI_IMAGE_BUCKET,
        contents=converted_image.contents,
        original_filename=converted_image.filename,
        content_type=converted_image.mime_type,
    )

    # Generate UUID for Gemini
    gemini_response_id = f"gemini_{uuid.uuid4().hex}"

    # Save to database
    data = UserMemeCreate(
        conversation_id=ctx.deps.conversation_id,
        image_url=public_url,
        openai_response_id=gemini_response_id,
    )

    def create_user_meme_operation():
        return create_user_meme(
            data=data, session=ctx.deps.session, current_user=ctx.deps.current_user
        )

    user_meme = safe_db_operation(create_user_meme_operation, ctx.deps.session)
    print(f"Created modified meme with ID: {user_meme.id}")
    print(f"Gemini Response ID: {gemini_response_id}")

    return ImageResult(
        image_id=user_meme.id, url=public_url, response_id=gemini_response_id
    )


# ─── Caption Refinement Agent ────────────────────────────────────────────
meme_caption_refinement_agent = Agent(
    model=model,
    model_settings=model_settings,
    instructions="""
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

# ─── Random Inspiration Agent ────────────────────────────────────────────
meme_random_inspiration_agent = Agent(
    model=model,
    model_settings=model_settings,
    instructions="""
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

# ─── Manager Tools as Plain Functions ────────────────────────────────────


async def meme_theme_factory(
    ctx: RunContext[Deps], keywords: List[str], image_context: str = ""
) -> MemeCaptionAndContext:
    r = await meme_theme_generation_agent.run(
        f"Themes: {', '.join(keywords)}; Context: {image_context}",
        usage=ctx.usage,
    )
    return r.output


def meme_image_generation(
    ctx: RunContext[Deps],
    text_boxes: dict[str, str],
    context: str = "",
) -> str:
    """
    Call the image generation agent to create a meme image.
    Args:
        text_boxes: A dictionary with keys like 'text_box_1', 'text_box_2', etc., and string values for each text box
        context: Optional context describing the scene/background for the meme
    Returns:
        Markdown formatted image URL for display in chat
    """
    print(f"Generating image with text_boxes: {text_boxes}, context: {context}")

    # Validate input types
    if not isinstance(text_boxes, dict):
        raise ValueError(
            f"text_boxes must be a dictionary, got {type(text_boxes)}: {text_boxes}"
        )

    if not all(
        isinstance(k, str) and isinstance(v, str) for k, v in text_boxes.items()
    ):
        raise ValueError(
            f"text_boxes must be a dictionary with string keys and values, got: {text_boxes}"
        )

    # Build JSON string for the sub-agent
    import json

    input_data = {"text_boxes": text_boxes, "context": context}
    input_json = json.dumps(input_data)

    # Call the image generation agent synchronously
    result = meme_image_generation_agent.run_sync(
        input_json,
        deps=ctx.deps,
        usage=ctx.usage,
    )

    # Extract URL from ImageResult and return as markdown
    image_result = result.output
    print(f"Image generation complete. URL: {image_result.url}")
    return f"![Generated meme]({image_result.url})"


def meme_image_modification(
    ctx: RunContext[Deps],
    modification_request: str,
    response_id: str,
) -> str:
    """
    Modify an existing meme image based on user request.
    Returns:
        Markdown formatted image URL for display in chat
    """
    prompt = f"Modify the previous image based on the following request: {modification_request}. Pass the previous response ID: {response_id}."
    print(
        f"Modification request from manager: {modification_request}, response_id: {response_id}"
    )

    # Call the image modification agent synchronously
    result = meme_image_modification_agent.run_sync(
        prompt,
        deps=ctx.deps,
        usage=ctx.usage,
    )

    # Extract URL from ImageResult and return as markdown
    image_result = result.output
    print(f"Image modification complete. URL: {image_result.url}")
    return f"![Modified meme]({image_result.url})"


def meme_caption_refinement(
    ctx: RunContext[Deps], caption: str, image_context: str = ""
) -> MemeCaptionAndContext:
    """
    Refine or rewrite a user-supplied meme caption into perfect meme format.
    """
    prompt = f"Caption: {caption}; Context: {image_context}"
    r = meme_caption_refinement_agent.run_sync(prompt, usage=ctx.usage)
    return r.output


def meme_random_inspiration(ctx: RunContext[Deps]) -> MemeCaptionAndContext:
    """
    Generate a random meme caption and context.
    """
    prompt = "Invent a random meme caption and fitting context."
    r = meme_random_inspiration_agent.run_sync(prompt, usage=ctx.usage)
    return r.output


def favourite_meme_in_db(ctx: RunContext[Deps]) -> str:
    """
    Mark the most recent meme in this conversation as favourite.
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


def fetch_previous_image_id(ctx: RunContext[Deps]) -> str:
    """
    Fetch the response ID of the most recent image in this conversation.
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

    if not user_meme:
        raise ModelRetry("No previous meme found in this conversation.")

    if not user_meme.openai_response_id:
        raise ModelRetry("Previous meme does not have a valid response ID.")

    print(f"Retrieved response ID: {user_meme.openai_response_id}")
    return user_meme.openai_response_id


def summarise_request(ctx: RunContext[Deps], user_request: str) -> str:
    """
    Summarise the current user request and update the conversation.
    """
    from features.conversations.service import update_conversation

    print(f"Summarising user request: {user_request}")
    prompt = f"Summarise the following user request: {user_request}"
    r = user_request_summary_agent.run_sync(prompt, usage=ctx.usage)
    summary = r.output

    print(f"Summarised request: {summary}")

    def update_conversation_operation():
        return update_conversation(
            conversation_id=ctx.deps.conversation_id,
            updates=ConversationUpdate(summary=summary),
            session=ctx.deps.session,
            user_id=ctx.deps.current_user.id,
        )

    updated_conversation = safe_db_operation(
        update_conversation_operation, ctx.deps.session
    )
    print(f"Updated conversation {ctx.deps.conversation_id} with summary: {summary}")
    return f"Conversation summary updated: {summary}"


# ─── Factory for Manager Agent ───────────────────────────────────────────
def create_manager_agent(provider, model):
    print(f"Creating manager agent with model: {model} and provider: {provider}")

    if provider == "openai":
        settings = OpenAIResponsesModelSettings(
            openai_builtin_tools=[WebSearchToolParam(type="web_search_preview")]
        )
        model_typed = OpenAIResponsesModel(model)
    elif provider == "anthropic":
        extra_body = {
            "tools": [
                {"type": "web_search_20250305", "name": "web_search", "max_uses": 1}
            ]
        }
        settings = ModelSettings(extra_body=extra_body)
        model_typed = AnthropicModel(model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    agent = Agent(
        model=model_typed,
        model_settings=settings,
        deps_type=Deps,
        tools=[
            meme_theme_factory,
            meme_caption_refinement,
            meme_random_inspiration,
            summarise_request,
            meme_image_generation,
            fetch_previous_image_id,
            meme_image_modification,
            favourite_meme_in_db,
        ],
        instructions=manager_agent_instructions,
        output_type=str,
    )
    return agent


# Helper function for safe database operations
def safe_db_operation(operation, session, max_retries=3):
    """
    Safely execute database operations with retry logic and proper error handling.
    """
    for attempt in range(max_retries):
        try:
            return operation()
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(
                    f"Database operation failed (attempt {attempt + 1}), retrying: {e}"
                )
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                print(f"Database operation failed after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            print(f"Unexpected error in database operation: {e}")
            raise
