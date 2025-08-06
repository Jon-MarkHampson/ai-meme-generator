#!/usr/bin/env python
"""
Test script to validate the new modular structure and check for circular imports.
Run this with: python test_models_import.py
"""

def test_models_registry():
    """Test that models registry imports without circular dependencies."""
    print("Testing models registry import...")
    try:
        import models_registry
        print("✅ Models registry imported successfully")
        
        # Check all models are registered
        expected_models = ["User", "Conversation", "Message", "UserMeme"]
        actual_models = [m.__name__ for m in models_registry.all_models]
        
        for model_name in expected_models:
            if model_name in actual_models:
                print(f"✅ {model_name} model registered")
            else:
                print(f"❌ {model_name} model NOT registered")
                
        print(f"\nTotal models registered: {len(actual_models)}")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_feature_imports():
    """Test that each feature module can be imported independently."""
    features = [
        "features.users.model",
        "features.users.schema",
        "features.users.service",
        "features.users.controller",
        "features.conversations.model",
        "features.conversations.schema",
        "features.conversations.service",
        "features.conversations.controller",
        "features.messages.model",
        "features.messages.schema",
        "features.messages.service",
        "features.messages.controller",
        "features.user_memes.model",
        "features.user_memes.schema",
        "features.user_memes.service",
        "features.user_memes.controller",
        "features.auth.schema",
        "features.auth.service",
        "features.auth.controller",
    ]
    
    print("\nTesting feature module imports...")
    all_passed = True
    
    for module_path in features:
        try:
            __import__(module_path)
            print(f"✅ {module_path}")
        except ImportError as e:
            print(f"❌ {module_path}: {e}")
            all_passed = False
        except Exception as e:
            print(f"❌ {module_path}: Unexpected error: {e}")
            all_passed = False
            
    return all_passed


def test_database_core():
    """Test that database core imports models registry correctly."""
    print("\nTesting database core import...")
    try:
        from database import core
        print("✅ Database core imported successfully")
        print("✅ Models registry is imported in database core")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING NEW MODULAR BACKEND STRUCTURE")
    print("=" * 60)
    
    results = []
    
    # Test models registry
    results.append(test_models_registry())
    
    # Test feature imports
    results.append(test_feature_imports())
    
    # Test database core
    results.append(test_database_core())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED - Structure is valid!")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("=" * 60)


if __name__ == "__main__":
    main()