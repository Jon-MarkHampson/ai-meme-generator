import os
import re
import requests
from urllib.parse import urlparse
from pathlib import Path

# ─── CONFIG ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent.parent / "classic_meme_templates"
IMGFLIP_API = "https://api.imgflip.com/get_memes"
TOP_N = 100  # how many to pull

# ─── HELPERS ───────────────────────────────────────────────────────────────────


def slugify(name: str) -> str:
    """Turn “Distracted Boyfriend” → “distracted_boyfriend”."""
    name = name.lower()
    # keep letters/numbers, replace everything else with underscore
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")


def get_extension(url: str) -> str:
    """Pick up the “.jpg” or “.png” from a URL (default to .jpg)."""
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    return ext if ext in {".jpg", ".jpeg", ".png", ".gif"} else ".jpg"


# ─── MAIN ─────────────────────────────────────────────────────────────────────


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    res = requests.get(IMGFLIP_API, timeout=10)
    res.raise_for_status()
    payload = res.json()
    if not payload.get("success"):
        print("Imgflip error:", payload.get("error_message"))
        return

    for meme in payload["data"]["memes"][:TOP_N]:
        name = meme["name"]
        url = meme["url"]
        fname = slugify(name) + get_extension(url)
        dest = OUTPUT_DIR / fname

        if dest.exists():
            print(f"↻ already have {fname}")
            continue

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(dest, "wb") as f:
                f.write(r.content)
            print(f"✔ downloaded {name!r} → {fname}")
        except Exception as e:
            print(f"✖ failed {name!r}: {e}")


if __name__ == "__main__":
    main()
