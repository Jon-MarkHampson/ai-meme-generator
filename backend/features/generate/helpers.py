import base64
import logging
import mimetypes
import uuid
from PIL import Image
from io import BytesIO
from .schema import ConvertedImageResult
from openai.types import ImagesResponse

logger = logging.getLogger(__name__)


def convert_response_to_png(response: ImagesResponse) -> ConvertedImageResult:
    """
    Converts a base64-encoded PNG from an OpenAI response to a byte string.
    """
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
            return ConvertedImageResult(contents, filename, mime_type)


def convert_gemini_response_to_png(response) -> ConvertedImageResult:
    """
    Converts inline image data from a GEMINI response to a byte string (PNG format).
    """
    # Validate response structure
    if (
        not response.candidates
        or not response.candidates[0].content
        or not response.candidates[0].content.parts
    ):
        raise ValueError("Invalid Gemini response: missing candidates, content, or parts")

    # Find the first image payload
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            # The inline_data.data is already bytes, no need to use PIL
            contents = part.inline_data.data
            logger.info("Received image data with %d bytes", len(contents))
            filename = f"{uuid.uuid4().hex}.png"

            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                # Default to PNG if we can't guess the type
                mime_type = "image/png"
            return ConvertedImageResult(contents, filename, mime_type)

    # If we get here, no image was found
    raise ValueError("No image data found in Gemini response")
