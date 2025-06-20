# backend/features/generate/agent.py
from dotenv import load_dotenv

from openai.types.responses import WebSearchToolParam
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings


load_dotenv()

model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[WebSearchToolParam(type="web_search_preview")],
    allow_tools=True,
)
model = OpenAIResponsesModel("gpt-4.1-2025-04-14")

chat_agent = Agent(
    model=model,
    model_settings=model_settings,
    system_prompt=(
        "You are an AI assistant for memes: concise, witty, and you may call web_search_preview "
        "if you need up-to-date info. Always reply in plain text."
    ),
)
