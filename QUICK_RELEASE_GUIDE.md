# Quick Guide: Adding Setup EXE to GitHub Releases

## ✅ What's Been Set Up

1. **GitHub Actions Workflow** - Automatically builds and creates releases when you push a tag
2. **Upload Helper Script** - `upload_to_release.py` helps you prepare releases
3. **Documentation** - Complete instructions in `UPLOAD_TO_RELEASE.md`

## 🚀 Quick Steps to Add Setup EXE to Release

### Option 1: Automatic (Recommended)

1. **Build the EXE:**
   ```bash
   python build.py
   ```

2. **Create and push a version tag:**
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

3. **GitHub Actions will automatically:**
   - Build the EXE and installer
   - Create a GitHub release
   - Attach both files to the release

### Option 2: Manual Upload

1. **Build the EXE:**
   ```bash
   python build.py
   ```

2. **Run the helper script:**
   ```bash
   python upload_to_release.py
   ```
   This will show you exactly what to do.

3. **Or follow these steps:**
   - Go to: https://github.com/realscripter/ProtectSecure/releases
   - Click "Create a new release"
   - Tag: `v1.0.1`
   - Title: `ProtectSecure v1.0.1`
   - Drag and drop `Output/ProtectSecure_Setup.exe` into the file area
   - (Optional) Also add `dist/ProtectSecure.exe`
   - Click "Publish release"

### Option 3: Using GitHub CLI

If you have GitHub CLI installed:

```bash
# Build first
python build.py

# Create release
gh release create v1.0.1 \
  --title "ProtectSecure v1.0.1" \
  --notes "## Changes in v1.0.1" \
  Output/ProtectSecure_Setup.exe \
  dist/ProtectSecure.exe
```

## 📝 Important Notes

- **File Size**: The setup EXE is ~80MB, so upload may take a few minutes
- **Not in Repo**: Large EXE files are excluded from the Git repository (use releases instead)
- **Tag Format**: Must start with 'v' (e.g., `v1.0.1`, `v1.0.2`)
- **Automatic Builds**: GitHub Actions builds on Windows, ensuring compatibility

## 🔍 Verify Release

After creating a release, check:
- ✅ Release appears at: https://github.com/realscripter/ProtectSecure/releases
- ✅ `ProtectSecure_Setup.exe` is attached and downloadable
- ✅ Update checker will detect the new version

## 🧪 Test Update System

After creating a release with tag `v1.0.1`:

1. Run the app with version 1.0.0 (or modify `gui.py` temporarily)
2. Wait 2 seconds after startup
3. Should see update alert popup
4. Clicking "Yes" opens the GitHub release page
