import base64
import mimetypes
import uuid
from .models import ConvertedImageResult
from openai.types import ImagesResponse


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
