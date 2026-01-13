"""
Script to help upload setup EXE to GitHub releases.
This script can be used to manually upload files or prepare them for release.
"""
import os
import sys
import subprocess

def check_files():
    """Check if build files exist."""
    files = {
        "Setup EXE": "Output/ProtectSecure_Setup.exe",
        "Standalone EXE": "dist/ProtectSecure.exe"
    }
    
    print("Checking build files...")
    print("=" * 50)
    
    all_exist = True
    for name, path in files.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024 * 1024)  # MB
            print(f"[OK] {name}: {path} ({size:.1f} MB)")
        else:
            print(f"[MISSING] {name}: {path} - NOT FOUND")
            all_exist = False
    
    print("=" * 50)
    return all_exist

def get_version():
    """Get version from version.json."""
    try:
        import json
        with open("version.json", "r") as f:
            data = json.load(f)
            return data.get("version", "1.0.0")
    except:
        return "1.0.0"

def create_release_instructions():
    """Print instructions for creating a release."""
    version = get_version()
    tag = f"v{version}"
    
    print("\n" + "=" * 50)
    print("GitHub Release Instructions")
    print("=" * 50)
    print(f"\nVersion: {version}")
    print(f"Tag: {tag}")
    print("\n1. Go to: https://github.com/realscripter/ProtectSecure/releases")
    print("2. Click 'Create a new release'")
    print(f"3. Tag version: {tag}")
    print(f"4. Release title: ProtectSecure {tag}")
    print("5. Description:")
    print("   ```")
    print(f"   ## Changes in {tag}")
    print("   - See CHANGELOG or commit history")
    print("   ```")
    print("6. Attach files:")
    print("   - Output/ProtectSecure_Setup.exe")
    print("   - dist/ProtectSecure.exe (optional)")
    print("7. Click 'Publish release'")
    print("\n" + "=" * 50)

def try_gh_cli():
    """Try to create release using GitHub CLI if available."""
    version = get_version()
    tag = f"v{version}"
    
    try:
        # Check if gh CLI is installed
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("\nGitHub CLI detected!")
            print(f"\nTo create release with tag {tag}, run:")
            print(f"\n  gh release create {tag} \\")
            print(f"    --title 'ProtectSecure {tag}' \\")
            print(f"    --notes '## Changes in {tag}' \\")
            print(f"    Output/ProtectSecure_Setup.exe")
            print(f"    dist/ProtectSecure.exe")
            print("\nOr run this command:")
            cmd = f'gh release create {tag} --title "ProtectSecure {tag}" --notes "## Changes in {tag}" Output/ProtectSecure_Setup.exe dist/ProtectSecure.exe'
            print(f"\n  {cmd}")
            return True
    except FileNotFoundError:
        pass
    
    return False

def main():
    print("ProtectSecure - Release Upload Helper")
    print("=" * 50)
    
    # Check if files exist
    files_exist = check_files()
    
    if not files_exist:
        print("\n⚠️  Some build files are missing!")
        print("Run 'python build.py' first to build the EXE and installer.")
        return
    
    # Try GitHub CLI
    has_gh = try_gh_cli()
    
    # Show manual instructions
    create_release_instructions()
    
    if has_gh:
        print("\n💡 Tip: You can use GitHub CLI (gh) to automate this process!")
    else:
        print("\n💡 Tip: Install GitHub CLI (gh) to automate release creation!")
        print("   Download: https://cli.github.com/")

if __name__ == "__main__":
    main()
