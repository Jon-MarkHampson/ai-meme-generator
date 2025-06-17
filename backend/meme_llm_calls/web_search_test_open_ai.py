from dotenv import load_dotenv
from openai import OpenAI
import logfire

load_dotenv()

logfire.configure()
logfire.instrument_openai()

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-2025-04-14",
    tools=[{"type": "web_search_preview"}],
    input="What was a positive news story from today?",
)

print(response.output_text)
