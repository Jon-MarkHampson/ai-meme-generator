from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get current temperature for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country e.g. Bogotá, Colombia",
                }
            },
            "required": ["location"],
            "additionalProperties": False,
        },
    }
]

response = client.responses.create(
    model="gpt-4.1-2025-04-14",
    input=[{"role": "user", "content": "What is the weather like in Paris today?"}],
    tools=tools,
)

print(response.output)
print("+" * 50)

response = client.responses.create(
    model="gpt-4.1-2025-04-14",
    input="Write a one-sentence bedtime story about a unicorn.",
)

print(response.output_text)
