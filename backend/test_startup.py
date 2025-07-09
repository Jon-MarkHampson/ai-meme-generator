#!/usr/bin/env python3
"""
Script to test the application startup and database connection
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from database.core import check_db_connection, get_session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_startup():
    """Test application startup and database connection"""
    print("Testing application startup...")

    # Test 1: Database connection
    print("\n1. Testing database connection:")
    is_healthy = check_db_connection()
    print(f"   Database: {'✓ HEALTHY' if is_healthy else '✗ UNHEALTHY'}")

    # Test 2: Test session dependency
    print("\n2. Testing session dependency:")
    try:
        session_gen = get_session()
        session = next(session_gen)
        print("   Session created successfully: ✓ PASS")

        # Try to close the session
        try:
            next(session_gen)
        except StopIteration:
            print("   Session closed successfully: ✓ PASS")
        except Exception as e:
            print(f"   Session close failed: ✗ FAIL - {e}")
    except Exception as e:
        print(f"   Session creation failed: ✗ FAIL - {e}")

    # Test 3: Test health endpoint
    print("\n3. Testing health endpoints:")
    try:
        client = TestClient(app)
        response = client.get("/")
        print(
            f"   Root health check: {'✓ PASS' if response.status_code == 200 else '✗ FAIL'}"
        )

        response = client.get("/health/db")
        print(
            f"   Database health check: {'✓ PASS' if response.status_code == 200 else '✗ FAIL'}"
        )
    except Exception as e:
        print(f"   Health endpoint test failed: ✗ FAIL - {e}")


if __name__ == "__main__":
    test_startup()
