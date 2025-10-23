import os
import uuid

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client()

chat = client.chats.create(
    model="gemini-2.5-flash-image",
)

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
folder = os.path.join(script_dir, "nano_banana_images")

# Create folder if it doesn't exist
os.makedirs(folder, exist_ok=True)


# Save the image
def save_image(response, path):
    for part in response.parts:
        if image := part.as_image():
            image.save(path)


while True:
    user_input = input("Enter a message (or 'exit' to quit): ")
    if user_input.lower() == "exit":
        break

    response = chat.send_message(
        user_input,
    )
    print("Chat object:", chat)
    print("Response:", response)
    save_image(response, f"{folder}/gen_Nano_Banana_{uuid.uuid4()}.png")
