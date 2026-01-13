# Automatic Update System

ProtectSecure now includes a fully automatic update system that downloads and installs updates without user intervention.

## How It Works

1. **Automatic Check**: The app checks for updates 2 seconds after startup (non-blocking)

2. **Update Detection**: Compares current version with latest GitHub release

3. **User Notification**: If an update is available, shows a popup with:
   - Current version vs. latest version
   - Release notes/changelog
   - Option to download and install automatically

4. **Automatic Download**: If user accepts:
   - Downloads the setup EXE from GitHub releases
   - Shows progress bar with download percentage
   - Downloads to temporary directory

5. **Automatic Installation**: After download:
   - Runs installer in silent mode
   - Closes current application
   - Installer installs new version
   - Application restarts automatically

## Features

- ✅ **Fully Automatic**: No manual download or installation needed
- ✅ **Progress Tracking**: Real-time download progress
- ✅ **Silent Installation**: No interruption during update
- ✅ **Auto Restart**: Application restarts after update
- ✅ **Error Handling**: Graceful error handling with user feedback
- ✅ **Cancellable**: User can cancel update if needed

## Requirements

For automatic updates to work:

1. **GitHub Release**: Must have a release with tag (e.g., `v1.0.1`)
2. **Setup EXE**: Release must include `ProtectSecure_Setup.exe` as an asset
3. **Internet Connection**: Required for downloading updates
4. **Admin Rights**: Installer requires admin rights (automatic on Windows)

## Update Process Flow

```
App Starts
    ↓
Check for Updates (2 seconds after startup)
    ↓
Update Available?
    ↓ Yes
Show Update Alert
    ↓
User Accepts?
    ↓ Yes
Download Setup EXE (with progress)
    ↓
Run Installer (silent mode)
    ↓
Close Current App
    ↓
Installer Installs New Version
    ↓
Restart Application
    ↓
Done! (User sees new version)
```

## Testing

To test the auto-update system:

1. **Create a test release**:
   - Tag: `v1.0.2` (or any version > 1.0.1)
   - Upload `ProtectSecure_Setup.exe` as asset

2. **Run old version**:
   - Temporarily change version in `gui.py` to `1.0.0`
   - Run the app
   - Wait 2 seconds
   - Should see update alert

3. **Accept update**:
   - Click "Yes" to download and install
   - Watch progress bar
   - App will close and restart with new version

## Technical Details

### Files

- `auto_updater.py`: Core auto-update logic
- `gui.py`: UI integration and progress display
- `installer.iss`: Silent installation support

### Silent Installer Flags

The installer uses these flags for silent installation:
- `/S` - Silent mode
- `/SP-` - Skip prompt
- `/SUPPRESSMSGBOXES` - Suppress messages
- `/FORCECLOSEAPPLICATIONS` - Close running instances
- `/RESTARTAPPLICATIONS` - Restart after install

### API Used

- GitHub Releases API: `https://api.github.com/repos/{owner}/{repo}/releases/latest`
- Downloads setup EXE from release assets

## Troubleshooting

**Update not detected:**
- Check if GitHub release exists with correct tag format (`v1.0.x`)
- Verify setup EXE is attached to release
- Check internet connection

**Download fails:**
- Check internet connection
- Verify GitHub release is accessible
- Check firewall/antivirus settings

**Installation fails:**
- Ensure admin rights are available
- Check if antivirus is blocking installer
- Verify installer file is not corrupted

**App doesn't restart:**
- Check if installer completed successfully
- Manually start the application
- Check Windows Event Viewer for errors

## Security

- Downloads are from official GitHub repository only
- Setup EXE is verified before installation
- Silent installation requires admin rights (Windows security)
- All downloads are to temporary directories (cleaned up after)
