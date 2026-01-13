# ProtectSecure Build Instructions

## Prerequisites

1. **Python 3.8+** installed
2. **Git** installed (for update checking)
3. **Inno Setup 6** (optional, for installer creation)
   - Download from: https://jrsoftware.org/isdl.php

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Update Checker (Optional)

Edit `gui.py` and set your Git repository URL:

```python
self.update_checker = UpdateChecker(
    repo_url="https://github.com/yourusername/protectsecure",
    current_version="1.0.0"
)
```

### 3. Update Version

Edit `version.json` with your current version:

```json
{
    "version": "1.0.0",
    "build_date": "2024-01-01",
    "changelog": "Initial release"
}
```

### 4. Build the Application

Run the build script:

```bash
python build.py
```

This will:
1. Obfuscate the code (using PyArmor if available, or basic compilation)
2. Create a single EXE file using PyInstaller
3. Create an installer using Inno Setup (if installed)

### 5. Output Files

- **EXE**: `dist/ProtectSecure.exe` - Standalone executable
- **Installer**: `Output/ProtectSecure_Setup.exe` - Windows installer (if Inno Setup is installed)

## Advanced: Manual Obfuscation with PyArmor

For stronger obfuscation, install PyArmor:

```bash
pip install pyarmor
```

Then run:

```bash
pyarmor gen --pack onefile --clean main.py
```

## Advanced: Manual Build with PyInstaller

If you want to customize the build:

```bash
pyinstaller --name=ProtectSecure --onefile --windowed --hidden-import=customtkinter --hidden-import=PIL --hidden-import=cv2 --hidden-import=pygame --collect-all=customtkinter main.py
```

## Distribution

1. Test the EXE: `dist/ProtectSecure.exe`
2. If installer was created, test: `Output/ProtectSecure_Setup.exe`
3. Distribute the installer to users

## Update System

The application checks for updates from your Git repository:
- Checks GitHub releases API for latest version
- Falls back to `version.json` in repository root
- Shows update alerts to users
- Opens download page when user accepts update

## Code Obfuscation

The build process includes code obfuscation:
- **PyArmor** (if available): Advanced obfuscation with encryption
- **Basic** (fallback): Compiles to .pyc bytecode

Obfuscated code makes reverse engineering significantly more difficult.
