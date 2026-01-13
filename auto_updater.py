"""
Automatic updater for ProtectSecure.
Downloads and installs updates automatically.
"""
import os
import sys
import urllib.request
import urllib.error
import json
import subprocess
import tempfile
import shutil
from packaging import version

class AutoUpdater:
    def __init__(self, repo_url, current_version):
        """
        Initialize auto-updater.
        
        Args:
            repo_url: GitHub repository URL
            current_version: Current application version
        """
        self.repo_url = repo_url
        self.current_version = current_version
        self.temp_dir = None
        
    def get_latest_release_info(self):
        """
        Get latest release information from GitHub.
        Returns dict with release info or None.
        """
        if not self.repo_url or "github.com" not in self.repo_url:
            return None
            
        try:
            # Extract owner/repo from URL
            parts = self.repo_url.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
            owner, repo = parts.split("/")[:2]
            
            # Get latest release
            api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            with urllib.request.urlopen(api_url, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                # Find setup EXE in assets
                setup_exe_url = None
                setup_exe_name = None
                for asset in data.get("assets", []):
                    if "Setup.exe" in asset.get("name", "") or "setup.exe" in asset.get("name", "").lower():
                        setup_exe_url = asset.get("browser_download_url")
                        setup_exe_name = asset.get("name")
                        break
                
                return {
                    "version": data.get("tag_name", "").lstrip("v"),
                    "name": data.get("name", ""),
                    "body": data.get("body", ""),
                    "url": data.get("html_url", ""),
                    "setup_exe_url": setup_exe_url,
                    "setup_exe_name": setup_exe_name,
                    "assets": data.get("assets", [])
                }
        except Exception as e:
            print(f"Error getting release info: {e}")
            return None
    
    def check_for_updates(self):
        """
        Check if updates are available.
        Returns (has_update, release_info) tuple.
        """
        release_info = self.get_latest_release_info()
        
        if not release_info:
            return False, None
            
        try:
            latest_version = release_info["version"]
            if version.parse(latest_version) > version.parse(self.current_version):
                return True, release_info
        except:
            pass
            
        return False, None
    
    def download_update(self, release_info, progress_callback=None):
        """
        Download the setup EXE for the update.
        
        Args:
            release_info: Release information dict
            progress_callback: Optional callback function(percent, status)
            
        Returns:
            Path to downloaded file or None if failed
        """
        if not release_info or not release_info.get("setup_exe_url"):
            # Try to find setup EXE in assets
            for asset in release_info.get("assets", []):
                name = asset.get("name", "").lower()
                if "setup.exe" in name or "installer.exe" in name:
                    release_info["setup_exe_url"] = asset.get("browser_download_url")
                    release_info["setup_exe_name"] = asset.get("name")
                    break
        
        if not release_info.get("setup_exe_url"):
            print("No setup EXE found in release assets")
            return None
        
        try:
            # Create temp directory
            self.temp_dir = tempfile.mkdtemp(prefix="ProtectSecure_Update_")
            download_path = os.path.join(self.temp_dir, release_info.get("setup_exe_name", "ProtectSecure_Setup.exe"))
            
            if progress_callback:
                progress_callback(0, "Connecting to GitHub...")
            
            # Download with progress
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    if progress_callback:
                        progress_callback(percent, f"Downloading... {percent}%")
            
            urllib.request.urlretrieve(
                release_info["setup_exe_url"],
                download_path,
                reporthook=report_progress
            )
            
            if progress_callback:
                progress_callback(100, "Download complete!")
            
            return download_path
            
        except Exception as e:
            print(f"Error downloading update: {e}")
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
            return None
    
    def install_update(self, setup_exe_path, silent=True):
        """
        Install the update by running the setup EXE.
        
        Args:
            setup_exe_path: Path to the setup EXE
            silent: If True, run installer silently
            
        Returns:
            True if installation started successfully
        """
        if not os.path.exists(setup_exe_path):
            print(f"Setup file not found: {setup_exe_path}")
            return False
        
        try:
            if silent:
                # Silent installation (Windows Inno Setup)
                # /S = silent, /SP- = skip prompt, /SUPPRESSMSGBOXES = suppress messages
                subprocess.Popen([
                    setup_exe_path,
                    "/S",  # Silent mode
                    "/SP-",  # Skip "This will install..." prompt
                    "/SUPPRESSMSGBOXES",  # Suppress message boxes
                    "/FORCECLOSEAPPLICATIONS",  # Close running instances
                    "/RESTARTAPPLICATIONS"  # Restart after install
                ], shell=False)
            else:
                # Normal installation
                subprocess.Popen([setup_exe_path], shell=False)
            
            return True
            
        except Exception as e:
            print(f"Error installing update: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
            self.temp_dir = None
