"""
Git-based update checker for ProtectSecure.
Checks for updates from a Git repository and alerts users.
"""
import subprocess
import os
import json
import urllib.request
import urllib.error
from packaging import version

class UpdateChecker:
    def __init__(self, repo_url=None, current_version="1.0.0"):
        """
        Initialize update checker.
        
        Args:
            repo_url: Git repository URL (e.g., "https://github.com/user/repo")
            current_version: Current application version
        """
        self.repo_url = repo_url
        self.current_version = current_version
        self.version_file = "version.json"
        
    def get_latest_version_from_git(self):
        """
        Get latest version from Git repository.
        Returns version string or None if unavailable.
        """
        if not self.repo_url:
            return None
            
        try:
            # Try to get version from GitHub API or raw file
            if "github.com" in self.repo_url:
                # Extract owner/repo from URL
                parts = self.repo_url.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
                owner, repo = parts.split("/")[:2]
                
                # Try to get latest release
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                try:
                    with urllib.request.urlopen(api_url, timeout=5) as response:
                        data = json.loads(response.read().decode())
                        return data.get("tag_name", "").lstrip("v")
                except:
                    pass
                
                # Fallback: try to get version.json from raw content (try main and master branches)
                for branch in ["main", "master"]:
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{self.version_file}"
                    try:
                        with urllib.request.urlopen(raw_url, timeout=5) as response:
                            data = json.loads(response.read().decode())
                            version = data.get("version", None)
                            if version:
                                return version
                    except:
                        continue
                    
        except Exception as e:
            print(f"Update check error: {e}")
            
        return None
    
    def check_for_updates(self):
        """
        Check if updates are available.
        Returns (has_update, latest_version) tuple.
        """
        latest_version = self.get_latest_version_from_git()
        
        if not latest_version:
            return False, None
            
        try:
            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                return True, latest_version
        except:
            # If version parsing fails, assume no update
            pass
            
        return False, None
    
    def get_update_info(self):
        """
        Get update information including changelog.
        Returns dict with update info or None.
        """
        if not self.repo_url:
            return None
            
        try:
            if "github.com" in self.repo_url:
                parts = self.repo_url.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
                owner, repo = parts.split("/")[:2]
                
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                with urllib.request.urlopen(api_url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    return {
                        "version": data.get("tag_name", "").lstrip("v"),
                        "name": data.get("name", ""),
                        "body": data.get("body", ""),
                        "url": data.get("html_url", ""),
                        "download_url": None
                    }
        except Exception as e:
            print(f"Update info error: {e}")
            
        return None
