# ProtectSecure Setup & Build System

## ✅ What's Been Created

### 1. **Build System** (`build.py`)
- Automatically obfuscates code using PyArmor (if available) or basic bytecode compilation
- Creates a single EXE file using PyInstaller
- Generates Windows installer using Inno Setup
- Handles all dependencies and hidden imports

### 2. **Update Checker** (`update_checker.py`)
- Git-based update checking system
- Checks GitHub releases API for new versions
- Falls back to `version.json` in repository
- Shows update alerts to users
- Opens download page when update is accepted

### 3. **Installer Script** (`installer.iss`)
- Professional Windows installer using Inno Setup
- Creates desktop shortcuts
- Adds Start Menu entries
- Includes uninstaller

### 4. **Version Management** (`version.json`)
- Tracks current version
- Stores build date and changelog
- Used by update checker

### 5. **Quick Build Scripts**
- `quick_build.bat` - Windows batch script
- `quick_build.sh` - Linux/Mac shell script

## 🚀 How to Use

### Quick Start (Windows)
1. Double-click `quick_build.bat`
2. Wait for build to complete
3. Find EXE in `dist/ProtectSecure.exe`
4. Find installer in `Output/ProtectSecure_Setup.exe` (if Inno Setup installed)

### Manual Build
```bash
# Install dependencies
pip install -r requirements.txt

# Run build
python build.py
```

### Configure Update Checking
Edit `gui.py` line ~754:
```python
self.update_checker = UpdateChecker(
    repo_url="https://github.com/yourusername/protectsecure",
    current_version="1.0.0"
)
```

## 🔒 Code Obfuscation

The build system includes two levels of obfuscation:

1. **PyArmor** (Advanced - if installed)
   - Encrypts Python bytecode
   - Makes reverse engineering extremely difficult
   - Install: `pip install pyarmor`

2. **Basic** (Fallback)
   - Compiles to .pyc bytecode
   - Makes source code harder to read
   - Always available

## 📦 Output Files

After building:
- **`dist/ProtectSecure.exe`** - Standalone executable (can distribute directly)
- **`Output/ProtectSecure_Setup.exe`** - Professional installer (requires Inno Setup)

## 🔄 Update System

The application automatically:
1. Checks for updates 2 seconds after startup (non-blocking)
2. Compares current version with latest GitHub release
3. Shows alert if update is available
4. Opens download page when user accepts

## 📋 Requirements

### Build Requirements
- Python 3.8+
- PyInstaller (`pip install pyinstaller`)
- PyArmor (optional, for advanced obfuscation: `pip install pyarmor`)
- Inno Setup 6 (optional, for installer: https://jrsoftware.org/isdl.php)

### Runtime Requirements
All dependencies are bundled into the EXE - no installation needed for end users!

## 🛠️ Customization

### Change App Version
Edit `version.json`:
```json
{
    "version": "1.0.1",
    "build_date": "2024-01-15",
    "changelog": "Bug fixes and improvements"
}
```

### Change Installer Settings
Edit `installer.iss`:
- App name, version, publisher
- Installation directory
- Icons and shortcuts

### Disable Update Checking
In `gui.py`, comment out:
```python
# self.after(2000, self.check_for_updates_async)
```

## 📝 Notes

- The EXE is completely standalone - all dependencies are bundled
- Code is obfuscated to protect intellectual property
- Update checking requires internet connection
- Installer is optional but recommended for easier distribution
