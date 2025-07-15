#!/usr/bin/env python3
"""
Authenticated test script for the models availability endpoint.
This script logs in first, then tests the models endpoint.

Usage:
    python test_models_authenticated.py user@example.com password123
"""

import os
import sys
import requests
import json
from datetime import datetime


def test_with_auth(email: str, password: str):
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    print(f"🧪 Testing authenticated models availability endpoint")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print(f"👤 Email: {email}")
    print("-" * 60)

    try:
        # Step 1: Login
        print("🔐 Step 1: Logging in...")
        login_response = requests.post(
            f"{base_url}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return

        login_data = login_response.json()
        access_token = login_data.get("access_token")
        print(f"✅ Login successful")

        # Step 2: Test models endpoint
        print("🎯 Step 2: Testing models availability endpoint...")
        headers = {"Authorization": f"Bearer {access_token}"}

        models_response = requests.get(
            f"{base_url}/llm_providers/availability", headers=headers, timeout=10
        )

        print(f"📡 Response Status: {models_response.status_code}")

        if models_response.status_code == 200:
            data = models_response.json()

            # Handle both new structured response and simple response
            if isinstance(data, dict) and "availability" in data:
                # New structured response
                availability = data["availability"]
                print(f"✅ SUCCESS (structured): {json.dumps(data, indent=2)}")
                print(f"\n📊 Metadata:")
                print(f"  📊 Data source: {data.get('data_source', 'unknown')}")
                print(f"  ⏰ Cache age: {data.get('cache_age_seconds', 0):.1f}s")
                print(
                    f"  📈 Enabled/Total: {data.get('enabled_count', 0)}/{data.get('total_count', 0)}"
                )
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

        elif models_response.status_code == 503:
            print(f"⚠️  SERVICE UNAVAILABLE")
            print(f"   This likely means the OpenAI API key is not configured.")
            print(f"   Response: {models_response.text}")

        else:
            print(f"❌ ERROR: {models_response.status_code}")
            print(f"   Response: {models_response.text}")

    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Cannot connect to {base_url}")
        print(f"   Make sure the backend server is running on port 8000")

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_models_authenticated.py <email> <password>")
        print(
            "Example: python test_models_authenticated.py user@example.com password123"
        )
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    test_with_auth(email, password)
