# How to Upload Setup EXE to GitHub Releases

There are two ways to add the setup EXE to GitHub releases:

## Method 1: Automatic (Recommended) - Using GitHub Actions

The repository includes a GitHub Actions workflow that automatically builds and creates releases.

### How it works:
1. **Create and push a version tag:**
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

2. **GitHub Actions will automatically:**
   - Build the EXE and installer
   - Create a GitHub release
   - Attach both `ProtectSecure_Setup.exe` and `ProtectSecure.exe` to the release

### To use this method:
1. Make sure `.github/workflows/build-and-release.yml` exists in your repository
2. Push a tag (e.g., `v1.0.1`)
3. Check the "Actions" tab in GitHub to see the build progress
4. The release will be created automatically with the files attached

## Method 2: Manual Upload

### Step 1: Build the EXE and Installer
```bash
python build.py
```

This creates:
- `dist/ProtectSecure.exe`
- `Output/ProtectSecure_Setup.exe`

### Step 2: Create GitHub Release

1. **Go to Releases page:**
   - Visit: https://github.com/realscripter/ProtectSecure/releases
   - Click "Create a new release"

2. **Fill in release details:**
   - **Tag version**: `v1.0.1` (must start with 'v')
   - **Release title**: `ProtectSecure v1.0.1`
   - **Description**: 
     ```markdown
     ## Changes in v1.0.1
     - Removed "Ultimate Edition" from title
     - Improved update system
     - Better UI consistency
     ```

3. **Attach files:**
   - Click "Attach binaries by dropping them here or selecting them"
   - Select `Output/ProtectSecure_Setup.exe`
   - (Optional) Also attach `dist/ProtectSecure.exe`

4. **Publish release:**
   - Click "Publish release"

### Step 3: Verify

After publishing, the release should show:
- Release notes
- Download links for:
  - `ProtectSecure_Setup.exe` (installer)
  - `ProtectSecure.exe` (standalone EXE, if uploaded)

## Method 3: Using GitHub CLI (gh)

If you have GitHub CLI installed:

```bash
# Build first
python build.py

# Create release with files
gh release create v1.0.1 \
  --title "ProtectSecure v1.0.1" \
  --notes "## Changes in v1.0.1
- Removed 'Ultimate Edition' from title
- Improved update system
- Better UI consistency" \
  Output/ProtectSecure_Setup.exe \
  dist/ProtectSecure.exe
```

## Testing the Update System

After creating a release:

1. **Run the old version** (v1.0.0):
   - The app checks for updates 2 seconds after startup
   - Should detect v1.0.1 is available
   - Popup will appear asking to download update
   - Clicking "Yes" opens the GitHub release page

2. **Test script:**
   ```bash
   python test_update_checker.py
   ```

## Notes

- **Tag format**: Must start with 'v' (e.g., `v1.0.1`, `v1.0.2`)
- **File size**: The installer is ~80MB, so upload may take a few minutes
- **Automatic builds**: GitHub Actions will build on Windows, ensuring compatibility
- **Manual builds**: Make sure to build on Windows to create Windows-compatible EXE
