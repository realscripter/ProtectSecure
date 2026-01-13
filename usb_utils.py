import psutil
import os
import platform
import ctypes

def get_usb_drives():
    drives = []
    if platform.system() == "Windows":
        # Use ctypes to get drive types for more accurate detection
        kernel32 = ctypes.windll.kernel32
        
        # Get logical drives
        bitmask = kernel32.GetLogicalDrives()
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if bitmask & 1:
                drive_root = f"{letter}:\\"
                drive_type = kernel32.GetDriveTypeW(drive_root)
                
                # DRIVE_REMOVABLE = 2
                # DRIVE_CDROM = 5
                if drive_type == 2 or drive_type == 5:
                    drives.append(drive_root)
                # Some large USB drives show up as Fixed (3)
                # We can include them if they are not the system drive (usually C:)
                elif drive_type == 3 and letter.upper() != 'C':
                     drives.append(drive_root)
            bitmask >>= 1
            
    else:
        # Linux/Mac implementation
        for partition in psutil.disk_partitions():
            if '/media' in partition.mountpoint or '/run/media' in partition.mountpoint or '/Volumes' in partition.mountpoint:
                drives.append(partition.mountpoint)
    
    return list(set(drives))
