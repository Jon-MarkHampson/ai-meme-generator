import os
import logging
from PIL import Image, ImageDraw, ImageFont
import datetime


logger = logging.getLogger(__name__)


# 1. Load template
img = Image.open("meme-text-over-image/coffee.png")

# 2. Prepare to draw
draw = ImageDraw.Draw(img)

# 2a. Compute font path
here = os.path.dirname(__file__)
font_path = os.path.join(here, "..", "fonts", "impact.ttf")

# 3. Prompt for user text, adjust font size, wrap lines, and center on image
text = input("Enter meme text: ").upper()
width, height = img.size
margin = int(width * 0.05)
max_width = width - 2 * margin
max_height = int(height * 0.2)

# adjust font size and wrap text into lines
font_size = 100
while font_size > 10:
    try:
        font = ImageFont.truetype(font_path, font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()
        break
    # wrap words to fit max_width
    lines = []
    words = text.split()
    if words:
        line = words[0]
        for w in words[1:]:
            test_line = f"{line} {w}"
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = w
        lines.append(line)
    else:
        lines = [""]
    # compute line spacing and total text block height to ensure vertical fit
    line_spacing = int(font_size * 0.2)
    text_heights = [
        (
            draw.textbbox((0, 0), l, font=font)[3]
            - draw.textbbox((0, 0), l, font=font)[1]
        )
        for l in lines
    ]
    total_height = sum(text_heights) + line_spacing * (len(lines) - 1)
    # break when text fits both width and max_height (first 20% of image)
    if (
        all(
            (
                draw.textbbox((0, 0), line, font=font)[2]
                - draw.textbbox((0, 0), line, font=font)[0]
            )
            <= max_width
            for line in lines
        )
        and total_height <= max_height
    ):
        break
    font_size -= 2

# calculate final text block height
line_spacing = int(font_size * 0.2)
text_heights = [
    (
        draw.textbbox((0, 0), line, font=font)[3]
        - draw.textbbox((0, 0), line, font=font)[1]
    )
    for line in lines
]
total_height = sum(text_heights) + line_spacing * (len(lines) - 1)

# starting y-coordinate within top 20% zone
y = int(height * 0.05)

# draw each line centered horizontally
for i, line in enumerate(lines):
    bbox = draw.textbbox((0, 0), line, font=font)
    w_line = bbox[2] - bbox[0]
    h_line = bbox[3] - bbox[1]
    x = (width - w_line) // 2
    draw.text(
        (x, y), line, font=font, fill="white", stroke_width=5, stroke_fill="black"
    )
    y += h_line + line_spacing

# 4. Save the result with a unique name in meme-output/
# ensure output folder exists
output_dir = os.path.join(here, "..", "meme-output")
os.makedirs(output_dir, exist_ok=True)
# generate unique filename by timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
output_path = os.path.join(output_dir, f"meme_{timestamp}.png")
img.save(output_path)
logger.error(f"Saved meme to: {output_path}")
