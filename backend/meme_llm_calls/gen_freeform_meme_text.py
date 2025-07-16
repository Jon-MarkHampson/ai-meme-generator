from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()


def hello_world() -> str:
    """
    Example function to demonstrate the use of an LLM agent to answer a simple question.

    Returns:
        str: The output from the LLM agent.
    """
    agent = Agent(
        "openai:gpt-4.1-2025-04-14",
        instructions="Be concise, reply with one sentence.",
    )

    result = agent.run_sync('Where does "hello world" come from?')
    return result.output
    """
    The first known use of "hello, world" was in a 1974 textbook about the C programming language.
    """


def generate_freeform_meme_text(prompt: str) -> str:
    """
    Generate freeform meme text using an LLM agent.

    Args:
        prompt (str): The input prompt for the LLM to generate text.

    Returns:
        str: The generated text from the LLM.
    """
    agent = Agent(
        "openai:gpt-4.1-2025-04-14",
        instructions="Generate a creative and humorous meme caption based on the provided prompt. "
        "Keep it concise and engaging, suitable for a meme format with two text boxes. "
        "Output format: JSON with 'text_box_1' and 'text_box_2' fields.",
    )
    result = agent.run_sync(prompt)
    return result.output
