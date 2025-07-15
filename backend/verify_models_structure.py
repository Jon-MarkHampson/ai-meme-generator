#!/usr/bin/env python3
"""
Verify that the llm_providers feature follows the same structure as other features.
"""

import os
from pathlib import Path


def check_feature_structure(feature_name: str) -> dict:
    """Check the structure of a feature directory."""
    feature_path = Path(f"features/{feature_name}")

    expected_files = ["__init__.py", "controller.py", "models.py", "service.py"]
    found_files = []
    missing_files = []

    if not feature_path.exists():
        return {"exists": False, "error": f"Feature directory {feature_name} not found"}

    for file in expected_files:
        file_path = feature_path / file
        if file_path.exists():
            found_files.append(file)
        else:
            missing_files.append(file)

    # Check if there are any unexpected files
    actual_files = [
        f.name
        for f in feature_path.iterdir()
        if f.is_file() and not f.name.startswith(".") and f.name != "__pycache__"
    ]
    unexpected_files = [f for f in actual_files if f not in expected_files]

    return {
        "exists": True,
        "found_files": found_files,
        "missing_files": missing_files,
        "unexpected_files": unexpected_files,
        "follows_pattern": len(missing_files) == 0 and len(unexpected_files) == 0,
    }


def main():
    print("🔍 Feature Structure Verification")
    print("=" * 50)

    # Check a few existing features first
    reference_features = ["auth", "users", "caption_requests"]
    models_feature = "llm_providers"

    print("\n📋 Reference Features:")
    reference_pattern = None
    for feature in reference_features:
        result = check_feature_structure(feature)
        if result["exists"]:
            status = "✅" if result["follows_pattern"] else "⚠️"
            print(f"  {status} {feature}: {len(result['found_files'])}/4 files")
            if result["follows_pattern"] and reference_pattern is None:
                reference_pattern = set(result["found_files"])

    print(f"\n🎯 Target Feature: {models_feature}")
    models_result = check_feature_structure(models_feature)

    if not models_result["exists"]:
        print(f"❌ {models_result['error']}")
        return

    status = "✅" if models_result["follows_pattern"] else "⚠️"
    print(f"  {status} Structure check: {len(models_result['found_files'])}/4 files")

    print(f"\n📊 Detailed Results for {models_feature}:")
    print(f"  ✅ Found files: {', '.join(models_result['found_files'])}")

    if models_result["missing_files"]:
        print(f"  ❌ Missing files: {', '.join(models_result['missing_files'])}")

    if models_result["unexpected_files"]:
        print(f"  ⚠️  Unexpected files: {', '.join(models_result['unexpected_files'])}")

    if models_result["follows_pattern"]:
        print(f"\n🎉 SUCCESS: {models_feature} follows the standard feature pattern!")
    else:
        print(f"\n⚠️  ISSUE: {models_feature} does not follow the standard pattern")

    # Test imports
    print(f"\n🧪 Testing {models_feature} imports...")
    try:
        import features.llm_providers.controller
        import features.llm_providers.service
        import features.llm_providers.models

        print("  ✅ All imports successful")

        # Test router
        router = features.llm_providers.controller.router
        print(f"  ✅ Router: {router.prefix} with {len(router.routes)} routes")

    except Exception as e:
        print(f"  ❌ Import error: {e}")


if __name__ == "__main__":
    main()
