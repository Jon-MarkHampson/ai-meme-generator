import os
import sys
import argparse
import mimetypes
import requests
from requests.exceptions import ReadTimeout, ConnectionError

def parse_args():
    p = argparse.ArgumentParser(
        description="Upload a local image to the FastAPI `/upload-image` endpoint."
    )
    p.add_argument(
        "--file-path", "-f",
        required=True,
        help="Path to the local image file you want to upload"
    )
    p.add_argument(
        "--api-url", "-u",
        required=True,
        help="Full URL of your FastAPI `/upload-image` endpoint (e.g. http://localhost:8000/upload-image/)"
    )
    p.add_argument(
        "--token", "-t",
        required=True,
        help="Your JWT access token (Bearer token)"
    )
    return p.parse_args()

def upload_image(file_path: str, api_url: str, token: str):
    if not os.path.isfile(file_path):
        print(f"Error: file does not exist: {file_path}")
        sys.exit(1)

    filename = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type not in ("image/png", "image/jpeg", "image/gif"):
        print(f"Error: unsupported file type ({mime_type}). Must be PNG/JPEG/GIF.")
        sys.exit(1)

    with open(file_path, "rb") as f:
        files = {
            # requests will send "Content-Type: <mime_type>" for this field
            "file": (filename, f, mime_type),
        }
        headers = {
            "Authorization": f"Bearer {token}",
        }

        print(f"Uploading {filename}  →  {api_url} …")
        try:
            resp = requests.post(api_url, headers=headers, files=files, timeout=10.0)
        except ReadTimeout:
            print("ERROR: Request timed out after 10 seconds.")
            return
        except ConnectionError as e:
            print(f"ERROR: Connection error: {e}")
            return

    print(f"Received HTTP status: {resp.status_code}")
    if 200 <= resp.status_code < 300:
        try:
            data = resp.json()
        except ValueError:
            print(f"Upload succeeded (status {resp.status_code}) but response is not JSON:")
            print(resp.text)
            return
        print("Upload successful! Response JSON:")
        print(data)
    else:
        print(f"Failed to upload. Status code: {resp.status_code}")
        try:
            print(resp.json())
        except ValueError:
            print(resp.text)

if __name__ == "__main__":
    args = parse_args()
    upload_image(args.file_path, args.api_url, args.token)