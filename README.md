# ProtectSecure - Ultimate File Protection System

A professional-grade secure file protection utility that encrypts and protects your files with multiple security layers, designed for maximum privacy and security.

## 🔒 Features

### Core Protection
- **Standard Protection**: Fast encryption with high-entropy tokens
- **Better Protect**: Multi-layer encryption (2x-20x customizable) with encrypted key storage
- **Only This PC**: Hardware-bound encryption that only works on the current computer
- **Full Hardware Mode**: Maximum speed using all available resources (reserves 1GB RAM)

### Security Features
- **Secure Deletion**: All temp files are overwritten 3 times before deletion (unrecoverable)
- **Safe Environment Viewer**: RAM-only viewing for text, images, and videos (no disk traces)
- **PC Lock**: Files encrypted with hardware-specific keys (MAC address, hostname, processor)
- **Token-Based Access**: High-entropy tokens for file decryption

### Advanced Features
- **USB Drive Detection**: Automatic detection and selection of USB drives
- **Progress Tracking**: Real-time progress bars with detailed status updates
- **File Size Estimation**: Calculate final encrypted file size before protection
- **Multi-Format Support**: View text, images (PNG, JPG, GIF, BMP, WebP), and videos (MP4) in safe environment
- **Folder Navigation**: Browse encrypted archives with folder structure
- **Video Player**: Full-featured video player with seeking, pause, and audio control

## 📦 Installation

### Option 1: Install from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/realscripter/ProtectSecure.git
   cd ProtectSecure
   ```

2. **Install Python 3.8+** (if not already installed)

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

### Option 2: Use Pre-built Installer

1. Download `ProtectSecure_Setup.exe` from [Releases](https://github.com/realscripter/ProtectSecure/releases)
2. Run the installer
3. Launch ProtectSecure from Start Menu or Desktop

## 🚀 Usage

### Protecting Files

1. **Select File/Folder**: Click "Browse..." and select the file or folder to protect
2. **Choose Protection Mode**:
   - **Standard**: Fast, single-layer encryption
   - **Better Protect**: Multi-layer encryption (recommended: 2x-3x layers)
   - **Only This PC**: Hardware-bound encryption (only works on this computer)
3. **Select Destination**: Choose USB drive or custom folder
4. **Optional**: Enable "Full Hardware" mode for maximum speed
5. **Click "PROTECT FILES"**: Wait for encryption to complete
6. **Save Your Token**: The `.key` file contains your token - keep it safe!

### Viewing Protected Files

1. **Select Secure File**: Browse to your `.secure` file
2. **Enter Token**: Paste your token (or it will auto-load from `.key` file)
3. **Choose View Method**:
   - **Safe Environment (RAM Only)**: View text/images/videos without writing to disk
   - **External App (Temp File)**: Extract to temporary folder for external applications
4. **Click "UNLOCK & VIEW"**: Files will be decrypted and opened

### Settings

- **Encryption Layers**: Adjust the number of encryption layers for "Better Protect" mode (2-20)
- **Size Estimation**: Calculate the final encrypted file size before protection
- **Update Checking**: Automatic updates from GitHub repository

## 🔐 Security Details

### Encryption
- Uses **Fernet** (AES-128 CBC with HMAC) from the `cryptography` library
- Keys are generated using `secrets` module (cryptographically secure)
- Multi-layer encryption encrypts files multiple times with different keys
- Keys themselves are encrypted in "Better Protect" mode

### Secure Deletion
- All temporary files are overwritten **3 times** with random data before deletion
- Makes file recovery **impossible**
- No traces left on disk when using "Safe Environment" viewer

### PC Lock Mode
- Generates a 10MB hardware signature using:
  - MAC address
  - Hostname
  - Machine identifier
  - Processor information
- Files encrypted with this signature can **only** be opened on the same computer

## 🛠️ Building from Source

### Prerequisites
- Python 3.8+
- PyInstaller: `pip install pyinstaller`
- PyArmor (optional, for code obfuscation): `pip install pyarmor`
- Inno Setup 6 (optional, for installer): [Download](https://jrsoftware.org/isdl.php)

### Build Steps

1. **Install build dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run build script:**
   ```bash
   python build.py
   ```

   Or use the quick build scripts:
   - Windows: `quick_build.bat`
   - Linux/Mac: `bash quick_build.sh`

3. **Output:**
   - EXE: `dist/ProtectSecure.exe`
   - Installer: `Output/ProtectSecure_Setup.exe` (if Inno Setup installed)

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for detailed build information.

## 📋 Requirements

### Runtime (Bundled in EXE)
- All dependencies are bundled - no installation needed for end users!

### Development
- Python 3.8+
- cryptography
- psutil
- customtkinter
- Pillow
- opencv-python
- pygame
- packaging

## 🔄 Update System

ProtectSecure automatically checks for updates from the GitHub repository:
- Checks for new releases on startup (non-blocking)
- Shows update alerts when new version is available
- Opens download page when update is accepted

## ⚠️ Important Notes

- **Keep your tokens safe**: Without the token, files cannot be decrypted
- **PC Lock files**: Cannot be transferred to other computers
- **High encryption layers**: 5x+ layers significantly increase file size and processing time
- **Recommended**: Use 2x-3x layers for "Better Protect" mode for best balance

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Issues

Found a bug? Please open an issue on [GitHub Issues](https://github.com/realscripter/ProtectSecure/issues).

## 📧 Contact

- GitHub: [@realscripter](https://github.com/realscripter)
- Repository: https://github.com/realscripter/ProtectSecure

---

**⚠️ Security Warning**: This software is provided as-is. Always keep backups of your tokens and test with non-critical files first.
