"""
Data models for the meme generation system.

Defines the structure of data flowing through the multi-agent meme
generation pipeline, from initial requests to final results. These
models ensure type safety and clear contracts between components.
"""

from dataclasses import dataclass
from openai import OpenAI
from pydantic import BaseModel
from typing import Dict, Optional
from features.users.model import User
from sqlmodel import Session


@dataclass
class Deps:
    """
    Dependency injection container for AI agents.

    Bundles all external dependencies needed by meme generation agents,
    allowing clean separation of concerns and easier testing. Passed
    through the agent context to provide access to external services.

    Attributes:
        client: OpenAI API client for image generation
        current_user: Authenticated user making the request
        session: Database session for persistence
        conversation_id: Current conversation context
    """

    client: OpenAI
    current_user: User
    session: Session
    conversation_id: str


@dataclass
class ConvertedImageResult:
    """
    Container for processed image data from AI generation.

    Holds the raw image bytes and metadata after extracting and
    converting the base64-encoded response from OpenAI's image
    generation API.

    Attributes:
        contents: Raw PNG image data as bytes
        filename: Generated filename for storage
        mime_type: MIME type (always 'image/png')
    """

    contents: bytes
    filename: str
    mime_type: str


class GenerateMemeRequest(BaseModel):
    """
    API request model for meme generation endpoint.

    Validates incoming requests and provides model selection flexibility
    for experimenting with different AI providers and models.

    Attributes:
        prompt: User's natural language request for meme creation
        conversation_id: UUID linking to conversation history
        manager_model: AI model selection in 'provider:model' format
    """

    prompt: str
    conversation_id: str
    manager_model: str = "openai:gpt-4.1-2025-04-14"


class MemeCaptionAndContext(BaseModel):
    """
    Structured meme content for image generation.

    Defines the text layout and visual context for meme creation.
    Supports flexible text box configurations beyond simple top/bottom
    layouts for more creative meme formats.

    Attributes:
        text_boxes: Dictionary mapping position keys to caption text
                   (e.g., {'text_box_1': 'Top text', 'text_box_2': 'Bottom text'})
        context: Optional scene description for image generation
    """

    text_boxes: Dict[str, str]
    context: Optional[str] = None


class ImageResult(BaseModel):
    """
    Final meme generation result with storage details.

    Contains all information needed to display and reference the
    generated meme, including tracking IDs for modification requests.

    Attributes:
        image_id: Database ID for the stored meme
        url: Public URL for displaying the meme image
        response_id: OpenAI response ID for modification workflows
    """

    image_id: str
    url: str
    response_id: str
