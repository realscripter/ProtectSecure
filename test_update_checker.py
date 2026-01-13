"""
Test script to verify the update checker works correctly.
"""
from update_checker import UpdateChecker
import json

def test_update_checker():
    print("Testing Update Checker...")
    print("=" * 50)
    
    # Test with current version (should not find update)
    print("\n1. Testing with current version (1.0.1):")
    checker = UpdateChecker(
        repo_url="https://github.com/realscripter/ProtectSecure",
        current_version="1.0.1"
    )
    
    has_update, latest_version = checker.check_for_updates()
    print(f"   Has update: {has_update}")
    print(f"   Latest version: {latest_version}")
    
    # Test with old version (should find update if release exists)
    print("\n2. Testing with old version (1.0.0):")
    checker_old = UpdateChecker(
        repo_url="https://github.com/realscripter/ProtectSecure",
        current_version="1.0.0"
    )
    
    # First, check what version is available
    latest_available = checker_old.get_latest_version_from_git()
    print(f"   Latest version available: {latest_available}")
    
    has_update_old, latest_version_old = checker_old.check_for_updates()
    print(f"   Has update: {has_update_old}")
    print(f"   Latest version: {latest_version_old}")
    
    if has_update_old:
        print("\n3. Getting update info:")
        update_info = checker_old.get_update_info()
        if update_info:
            print(f"   Version: {update_info.get('version')}")
            print(f"   Name: {update_info.get('name')}")
            print(f"   URL: {update_info.get('url')}")
            print(f"   Changelog preview: {update_info.get('body', '')[:100]}...")
        else:
            print("   No update info available")
    else:
        print("\n   [WARNING] No update found. This is expected if:")
        print("      - No GitHub release exists yet")
        print("      - Or version.json shows same/older version")
        print("   To test: Create a GitHub release with tag v1.0.1 or higher")
    
    print("\n" + "=" * 50)
    print("Test complete!")
    print("\nNote: For the update checker to work, you need to:")
    print("1. Create a GitHub release with tag v1.0.1 or higher")
    print("2. Or ensure version.json exists in the repository root")

if __name__ == "__main__":
    test_update_checker()
