#!/usr/bin/env python3
"""
Test script to check database connection health
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.core import check_db_connection, engine
from sqlmodel import Session, text


def test_connection():
    """Test database connection with various scenarios"""
    print("Testing database connection...")

    # Test 1: Basic connection health check
    print("\n1. Basic connection health check:")
    is_healthy = check_db_connection()
    print(f"   Result: {'✓ PASS' if is_healthy else '✗ FAIL'}")

    # Test 2: Test connection pool
    print("\n2. Testing connection pool (creating multiple sessions):")
    sessions = []
    try:
        for i in range(5):
            session = Session(engine)
            result = session.exec(text("SELECT 1")).first()
            sessions.append(session)
            print(f"   Session {i+1}: {'✓ PASS' if result else '✗ FAIL'}")

        # Close all sessions
        for session in sessions:
            session.close()
        print("   All sessions closed successfully")

    except Exception as e:
        print(f"   ✗ FAIL: {e}")
        for session in sessions:
            try:
                session.close()
            except:
                pass

    # Test 3: Test pool exhaustion scenario
    print("\n3. Testing pool exhaustion scenario:")
    try:
        sessions = []
        for i in range(25):  # Try to create more sessions than pool size
            session = Session(engine)
            sessions.append(session)

        print(f"   Created {len(sessions)} sessions")

        # Close all sessions
        for session in sessions:
            session.close()
        print("   All sessions closed successfully")

    except Exception as e:
        print(f"   ✗ FAIL: {e}")
        for session in sessions:
            try:
                session.close()
            except:
                pass


if __name__ == "__main__":
    test_connection()
