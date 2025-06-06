import os
import sys
import logging
import argparse
import mimetypes
import requests
from requests.exceptions import ReadTimeout, ConnectionError

logger = logging.getLogger(__name__)


def parse_args():
    p = argparse.ArgumentParser(
        description="Upload a local image to the FastAPI `/upload-image` endpoint."
    )
    p.add_argument(
        "--file-path",
        "-f",
        required=True,
        help="Path to the local image file you want to upload",
    )
    p.add_argument(
        "--api-url",
        "-u",
        required=True,
        help="Full URL of your FastAPI `/upload-image` endpoint (e.g. http://localhost:8000/upload-image/)",
    )
    p.add_argument(
        "--token", "-t", required=True, help="Your JWT access token (Bearer token)"
    )
    return p.parse_args()


def upload_image(file_path: str, api_url: str, token: str):
    if not os.path.isfile(file_path):
        logger.error(f"Error: file does not exist: {file_path}")
        sys.exit(1)

    filename = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type not in ("image/png", "image/jpeg", "image/gif"):
        logger.error(
            f"Error: unsupported file type ({mime_type}). Must be PNG/JPEG/GIF."
        )
        sys.exit(1)

    with open(file_path, "rb") as f:
        files = {
            # requests will send "Content-Type: <mime_type>" for this field
            "file": (filename, f, mime_type),
        }
        headers = {
            "Authorization": f"Bearer {token}",
        }

        logger.error(f"Uploading {filename}  →  {api_url} …")
        try:
            resp = requests.post(api_url, headers=headers, files=files, timeout=10.0)
        except ReadTimeout:
            logger.error("ERROR: Request timed out after 10 seconds.")
            return
        except ConnectionError as e:
            logger.error(f"ERROR: Connection error: {e}")
            return

    logger.error(f"Received HTTP status: {resp.status_code}")
    if 200 <= resp.status_code < 300:
        try:
            data = resp.json()
        except ValueError:
            logger.error(
                f"Upload succeeded (status {resp.status_code}) but response is not JSON:"
            )
            logger.error(resp.text)
            return
        logger.error("Upload successful! Response JSON:")
        logger.error(data)
    else:
        logger.error(f"Failed to upload. Status code: {resp.status_code}")
        try:
            logger.error(resp.json())
        except ValueError:
            logger.error(resp.text)


if __name__ == "__main__":
    args = parse_args()
    upload_image(args.file_path, args.api_url, args.token)
