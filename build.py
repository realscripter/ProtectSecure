"""
Build script for ProtectSecure.
Creates obfuscated EXE with PyInstaller.
"""
import os
import sys
import shutil
import subprocess
import py_compile

def obfuscate_code():
    """
    Obfuscate Python source files using PyArmor or basic obfuscation.
    Note: PyInstaller will handle obfuscation during packing if PyArmor is used.
    """
    print("Checking for obfuscation tools...")
    
    # Check if PyArmor is available
    try:
        result = subprocess.run([sys.executable, "-m", "pyarmor", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("PyArmor found - will use advanced obfuscation during build")
            return True
    except (ImportError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("PyArmor not found - using basic bytecode compilation")
    print("Note: For stronger obfuscation, install PyArmor: pip install pyarmor")
    
    # Basic obfuscation: compile to .pyc files
    source_files = ["main.py", "gui.py", "crypto_utils.py", "usb_utils.py", "update_checker.py"]
    
    for file in source_files:
        if os.path.exists(file):
            try:
                py_compile.compile(file, doraise=True)
                print(f"Compiled: {file}")
            except Exception as e:
                print(f"Warning: Could not compile {file}: {e}")
    
    return False

def build_exe(use_pyarmor=False):
    """
    Build EXE using PyInstaller.
    If PyArmor is available, use it for obfuscation.
    """
    print("Building EXE with PyInstaller...")
    
    if use_pyarmor:
        print("Using PyArmor for obfuscation...")
        # PyArmor obfuscates and then packs
        try:
            cmd = [
                sys.executable, "-m", "pyarmor", "gen",
                "--pack", "onefile",
                "--clean",
                "--name", "ProtectSecure",
                "--add-data", "requirements.txt;.",
                "--hidden-import", "customtkinter",
                "--hidden-import", "PIL",
                "--hidden-import", "cv2",
                "--hidden-import", "pygame",
                "--hidden-import", "cryptography",
                "--hidden-import", "psutil",
                "--hidden-import", "packaging",
                "main.py"
            ]
            subprocess.run(cmd, check=True)
            print("Obfuscated EXE build complete!")
            print(f"Output: dist/ProtectSecure.exe")
            return True
        except subprocess.CalledProcessError as e:
            print(f"PyArmor build failed: {e}")
            print("Falling back to standard PyInstaller...")
            use_pyarmor = False
    
    # Standard PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=ProtectSecure",
        "--onefile",
        "--windowed",  # No console window
        "--add-data=requirements.txt;.",
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=cv2",
        "--hidden-import=pygame",
        "--hidden-import=cryptography",
        "--hidden-import=psutil",
        "--hidden-import=packaging",
        "--collect-all=customtkinter",
        "--collect-all=PIL",
        "--collect-all=cv2",
        "--noconfirm",
        "--clean",
        "main.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("EXE build complete!")
        print(f"Output: dist/ProtectSecure.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    except FileNotFoundError:
        print("PyInstaller not found. Install it with: pip install pyinstaller")
        return False

def create_installer():
    """
    Create installer using Inno Setup (requires Inno Setup to be installed).
    """
    print("Creating installer...")
    
    # Check if Inno Setup compiler is available
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    inno_compiler = None
    for path in inno_paths:
        if os.path.exists(path):
            inno_compiler = path
            break
    
    if not inno_compiler:
        print("Inno Setup not found. Installer creation skipped.")
        print("Install Inno Setup from: https://jrsoftware.org/isdl.php")
        return False
    
    try:
        subprocess.run([inno_compiler, "installer.iss"], check=True)
        print("Installer created successfully!")
        print("Output: Output/ProtectSecure_Setup.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Installer creation failed: {e}")
        return False

def main():
    """
    Main build process.
    """
    print("=" * 50)
    print("ProtectSecure Build Script")
    print("=" * 50)
    
    # Step 1: Check for obfuscation tools
    use_pyarmor = obfuscate_code()
    
    # Step 2: Build EXE (with or without PyArmor)
    if build_exe(use_pyarmor=use_pyarmor):
        # Step 3: Create installer
        create_installer()
    
    print("\nBuild process complete!")
    print("\nNext steps:")
    print("1. Test the EXE: dist/ProtectSecure.exe")
    if os.path.exists("Output/ProtectSecure_Setup.exe"):
        print("2. Test installer: Output/ProtectSecure_Setup.exe")
    else:
        print("2. Install Inno Setup to create installer")
    print("3. Distribute the installer to users")

if __name__ == "__main__":
    main()
