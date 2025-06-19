from dotenv import load_dotenv
import logfire

from pydantic_ai.direct import model_request_sync
from pydantic_ai.messages import ModelRequest
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.tools import ToolDefinition

load_dotenv()
logfire.configure()
logfire.instrument_pydantic_ai()

# 1) Define the tool with a fully specified schema
search_tool = ToolDefinition(
    name="web_search_preview",
    description="Fetch up-to-date web search results using OpenAI's built-in tool",
    parameters_json_schema={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,  # <-- this line is critical
    },
)

# 2) Build request parameters
req_params = ModelRequestParameters(
    function_tools=[search_tool],
    allow_text_output=True,
)

# 3) Call the model
response = model_request_sync(
    "openai:gpt-4.1-2025-04-14",
    [ModelRequest.user_text_prompt("What was a positive news story from today?")],
    model_request_parameters=req_params,
)

# 4) Handle each part
for part in response.parts:
    cls = part.__class__.__name__
    if hasattr(part, "content"):
        # This is plain text from the model
        print(part.content)
    elif hasattr(part, "name") and hasattr(part, "arguments"):
        # This is a tool call
        print(f">>> Tool call: {part.name}({part.arguments})")
    else:
        # Fallback
        print(part)
