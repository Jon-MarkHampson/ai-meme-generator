#!/usr/bin/env python3
"""
Test script for the models availability endpoint.
Run this to verify the backend endpoint is working.
"""

import os
import sys
import requests
import json
from datetime import datetime


def test_models_endpoint():
    # Backend base URL
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    endpoint = f"{base_url}/llm_providers/availability"

    print(f"🧪 Testing LLM providers availability endpoint: {endpoint}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)

    try:
        # Make the request (without auth for testing)
        response = requests.get(endpoint, timeout=10)

        print(f"📡 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()

            # Handle both new structured response and simple response
            if isinstance(data, dict) and "availability" in data:
                # New structured response
                availability = data["availability"]
                print(f"✅ SUCCESS (structured): {json.dumps(data, indent=2)}")
                print(f"\n📊 Metadata:")
                print(f"  📊 Data source: {data.get('data_source', 'unknown')}")
                print(f"  ⏰ Cache age: {data.get('cache_age_seconds', 0):.1f}s")
            else:
                # Simple response (dict of model_id -> bool)
                availability = data
                print(f"✅ SUCCESS (simple): {json.dumps(data, indent=2)}")

            enabled_models = [
                model_id for model_id, available in availability.items() if available
            ]
            disabled_models = [
                model_id
                for model_id, available in availability.items()
                if not available
            ]

            print(f"\n📊 Summary:")
            print(f"  🟢 Available models: {len(enabled_models)}")
            print(f"  🔴 Unavailable models: {len(disabled_models)}")

            if enabled_models:
                print(f"  Available: {', '.join(enabled_models)}")
            if disabled_models:
                print(f"  Unavailable: {', '.join(disabled_models)}")

        elif response.status_code == 401:
            print(f"🔐 AUTHENTICATION REQUIRED")
            print(f"   This endpoint requires user authentication.")
            print(f"   Response: {response.text}")

        elif response.status_code == 503:
            print(f"⚠️  SERVICE UNAVAILABLE")
            print(f"   This likely means the OpenAI API key is not configured.")
            print(f"   Response: {response.text}")

        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Cannot connect to {base_url}")
        print(f"   Make sure the backend server is running on port 8000")

    except requests.exceptions.Timeout:
        print(f"⏰ TIMEOUT ERROR: Request took longer than 10 seconds")

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


if __name__ == "__main__":
    test_models_endpoint()
