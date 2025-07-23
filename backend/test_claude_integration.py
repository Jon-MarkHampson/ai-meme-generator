#!/usr/bin/env python3
"""
Test script to verify Claude models integration.
Run this to check if the new provider system works correctly.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def test_providers():
    """Test both OpenAI and Anthropic providers."""
    print("🧪 Testing LLM Provider Integration...")
    print("-" * 50)

    # Test imports
    try:
        from features.llm_providers.providers.openai import OpenAIProvider
        from features.llm_providers.providers.anthropic import AnthropicProvider
        from features.llm_providers.multi_provider_service import (
            get_all_providers_availability,
        )

        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return

    # Test provider initialization
    print("\n📡 Testing provider initialization...")

    openai_provider = OpenAIProvider()
    anthropic_provider = AnthropicProvider()

    print(f"  OpenAI provider: {openai_provider.provider_name}")
    print(f"  Anthropic provider: {anthropic_provider.provider_name}")

    # Test model lists
    print("\n📋 Supported models:")
    print(f"  OpenAI models: {len(openai_provider.supported_models)}")
    for model in openai_provider.supported_models:
        print(f"    - {model.name} ({model.id})")

    print(f"  Anthropic models: {len(anthropic_provider.supported_models)}")
    for model in anthropic_provider.supported_models:
        print(f"    - {model.name} ({model.id})")

    # Test API key availability
    print("\n🔑 API Key status:")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    print(f"  OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Missing'}")
    print(f"  ANTHROPIC_API_KEY: {'✅ Set' if anthropic_key else '❌ Missing'}")

    # Test availability checking (only if API keys are available)
    print("\n🌐 Testing provider availability...")

    if openai_key:
        try:
            openai_availability = await openai_provider.check_availability()
            print(
                f"  OpenAI: {openai_availability.is_available} ({openai_availability.data_source})"
            )
            available_openai = sum(openai_availability.models.values())
            print(
                f"    Available models: {available_openai}/{len(openai_availability.models)}"
            )
        except Exception as e:
            print(f"  OpenAI: ❌ Error - {e}")
    else:
        print("  OpenAI: ⏭️ Skipped (no API key)")

    if anthropic_key:
        try:
            anthropic_availability = await anthropic_provider.check_availability()
            print(
                f"  Anthropic: {anthropic_availability.is_available} ({anthropic_availability.data_source})"
            )
            available_anthropic = sum(anthropic_availability.models.values())
            print(
                f"    Available models: {available_anthropic}/{len(anthropic_availability.models)}"
            )
        except Exception as e:
            print(f"  Anthropic: ❌ Error - {e}")
    else:
        print("  Anthropic: ⏭️ Skipped (no API key)")

    # Test agent creation
    print("\n🤖 Testing agent creation...")

    try:
        from features.generate.agent import create_manager_agent

        # Test OpenAI agent
        openai_agent = create_manager_agent("openai", "gpt-4.1-2025-04-14")
        print("  ✅ OpenAI agent created successfully")

        # Test Anthropic agent (if API key is available)
        if anthropic_key:
            anthropic_agent = create_manager_agent(
                "anthropic", "claude-3-5-sonnet-latest"
            )
            print("  ✅ Anthropic agent created successfully")
        else:
            print("  ⏭️ Anthropic agent creation skipped (no API key)")

    except Exception as e:
        print(f"  ❌ Agent creation error: {e}")

    print("\n✨ Test complete!")
    print("-" * 50)

    # Environment setup instructions
    if not anthropic_key:
        print("\n💡 To enable Claude models:")
        print("   1. Get an Anthropic API key from https://console.anthropic.com/")
        print("   2. Add ANTHROPIC_API_KEY=your_key_here to your .env file")
        print("   3. Restart your backend server")


if __name__ == "__main__":
    asyncio.run(test_providers())
