#!/usr/bin/env python3
"""
Verify that all API imports work correctly.
"""


def test_imports():
    """Test that all feature imports work."""
    print("🧪 Testing API Structure")
    print("=" * 40)

    try:
        print("📦 Testing feature imports...")

        # Test auth
        from features.auth.controller import router as auth_router

        print(f"  ✅ auth: {auth_router.prefix}")

        # Test users
        from features.users.controller import router as user_router

        print(f"  ✅ users: {user_router.prefix}")

        # Test llm_providers
        from features.llm_providers.controller import router as llm_providers_router

        print(f"  ✅ llm_providers: {llm_providers_router.prefix}")

        # Test API module
        print("\n📡 Testing API module...")
        from api import register_routers

        print("  ✅ API import successful")

        print("\n🎉 All imports successful!")
        return True

    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
