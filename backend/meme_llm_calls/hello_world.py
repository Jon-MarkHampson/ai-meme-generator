from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()

agent = Agent(
    "openai:gpt-4.1-2025-04-14",
    instructions="Be concise, reply with one sentence.",
)

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
