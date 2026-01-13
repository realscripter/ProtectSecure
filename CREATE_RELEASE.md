# How to Create a GitHub Release for Testing Updates

To test the auto-update system, you need to create a GitHub release. Here's how:

## Method 1: Using GitHub Web Interface

1. **Go to your repository**: https://github.com/realscripter/ProtectSecure

2. **Click "Releases"** (on the right sidebar)

3. **Click "Create a new release"**

4. **Fill in the release form**:
   - **Tag version**: `v1.0.1` (must start with 'v')
   - **Release title**: `ProtectSecure v1.0.1`
   - **Description**:
     ```
     ## Changes in v1.0.1
     - Removed "Ultimate Edition" from title
     - Improved update system
     - Better UI consistency
     ```
   - **Attach files** (optional): Upload `ProtectSecure_Setup.exe` as a release asset

5. **Click "Publish release"**

## Method 2: Using GitHub CLI (if installed)

```bash
gh release create v1.0.1 \
  --title "ProtectSecure v1.0.1" \
  --notes "## Changes in v1.0.1
- Removed 'Ultimate Edition' from title
- Improved update system
- Better UI consistency" \
  Output/ProtectSecure_Setup.exe
```

## Testing the Update System

After creating the release:

1. **Run the old version** (v1.0.0):
   - The app will check for updates 2 seconds after startup
   - It should detect v1.0.1 is available
   - A popup will appear asking if you want to download the update

2. **Test the update checker**:
   ```bash
   python test_update_checker.py
   ```

## How the Update System Works

- Checks GitHub Releases API for latest version
- Compares with current version (1.0.1)
- Shows alert if newer version is available
- Opens GitHub release page when user accepts

## Notes

- Release tags must start with 'v' (e.g., `v1.0.1`)
- The update checker uses semantic versioning comparison
- Update check happens 2 seconds after app startup (non-blocking)
