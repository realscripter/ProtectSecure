import os
import zipfile
import shutil
from cryptography.fernet import Fernet
import secrets
import tempfile
import struct
import platform
import hashlib
import uuid
import json
import threading
import queue
import psutil
import io

def secure_delete_file(file_path):
    """
    Securely deletes a file by overwriting it with random data before deletion.
    This makes file recovery impossible.
    """
    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            # Overwrite with random data (3 passes for extra security)
            for _ in range(3):
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(file_size))
            # Finally delete
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Secure delete warning: {e}")
        # Fallback to normal delete
        try:
            os.remove(file_path)
        except:
            pass
    return False

def secure_delete_directory(dir_path):
    """
    Securely deletes a directory and all its contents.
    Overwrites all files before deletion.
    """
    try:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            # First, securely delete all files
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    secure_delete_file(file_path)
            # Then remove empty directories
            shutil.rmtree(dir_path)
            return True
    except Exception as e:
        print(f"Secure delete directory warning: {e}")
        # Fallback to normal delete
        try:
            shutil.rmtree(dir_path)
        except:
            pass
    return False

# Magic headers
MAGIC_HEADER = b'PSv2'
MAGIC_HEADER_BETTER = b'PSx1' 
MAGIC_HEADER_PC = b'PSc1'

# Default Chunk size
DEFAULT_CHUNK_SIZE = 64 * 1024 * 1024 

def get_available_ram():
    """Returns available RAM in bytes."""
    return psutil.virtual_memory().available

def get_disk_space(path):
    """Returns free space in bytes for the drive containing path."""
    try:
        # If path doesn't exist (e.g. new file), get parent
        while not os.path.exists(path):
            path = os.path.dirname(path)
            if not path or len(path) < 4: # Root like C:\
                break
        return shutil.disk_usage(path).free
    except:
        return 0

def generate_key():
    return Fernet.generate_key()

def get_pc_signature():
    data = []
    data.append(str(uuid.getnode()))
    data.append(platform.node())
    data.append(platform.machine())
    data.append(platform.processor())
    signature_str = "|".join(data)
    import base64
    digest = hashlib.sha256(signature_str.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def zip_target(target_path, output_zip_path, stored_only=False):
    compression = zipfile.ZIP_STORED if stored_only else zipfile.ZIP_DEFLATED
    
    # Check space before zipping
    total_size = 0
    if os.path.isfile(target_path):
        total_size = os.path.getsize(target_path)
    else:
        for root, _, files in os.walk(target_path):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
    
    free_space = get_disk_space(os.path.dirname(output_zip_path))
    if free_space < total_size + (100 * 1024 * 1024): # Buffer 100MB
        raise OSError(f"Insufficient disk space on temp drive. Need {total_size/1024/1024:.1f}MB, have {free_space/1024/1024:.1f}MB.")

    with zipfile.ZipFile(output_zip_path, 'w', compression) as zipf:
        if os.path.isdir(target_path):
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(target_path))
                    zipf.write(file_path, arcname)
        else:
            zipf.write(target_path, os.path.basename(target_path))

def encrypt_file_pipelined(file_path, key, output_path, header=MAGIC_HEADER, progress_callback=None, offset_progress=0.0, scale_progress=1.0, use_max_hardware=False):
    f = Fernet(key)
    file_size = os.path.getsize(file_path)
    
    chunk_size = 256 * 1024 * 1024 if use_max_hardware else DEFAULT_CHUNK_SIZE
    queue_depth = 8 if use_max_hardware else 3
    
    q_read = queue.Queue(maxsize=queue_depth)
    q_write = queue.Queue(maxsize=queue_depth)
    
    error_event = threading.Event()
    
    def read_thread():
        try:
            with open(file_path, 'rb') as infile:
                while not error_event.is_set():
                    data = infile.read(chunk_size)
                    if not data:
                        break
                    q_read.put(data)
            q_read.put(None)
        except:
            error_event.set()
            
    def encrypt_thread():
        try:
            while not error_event.is_set():
                data = q_read.get()
                if data is None:
                    q_write.put(None)
                    break
                enc = f.encrypt(data)
                q_write.put((len(data), enc))
        except:
            error_event.set()

    t1 = threading.Thread(target=read_thread, daemon=True)
    t2 = threading.Thread(target=encrypt_thread, daemon=True)
    t1.start()
    t2.start()
    
    processed = 0
    with open(output_path, 'wb') as outfile:
        outfile.write(header)
        while True:
            if error_event.is_set():
                raise Exception("Error in processing pipeline")
            
            item = q_write.get()
            if item is None:
                break
                
            orig_len, enc_data = item
            
            outfile.write(struct.pack('<I', len(enc_data)))
            outfile.write(enc_data)
            
            processed += orig_len
            if progress_callback:
                relative_p = processed / file_size
                total_p = offset_progress + (relative_p * scale_progress)
                progress_callback(total_p)

def decrypt_file_chunked(encrypted_path, key, output_path, progress_callback=None, offset_progress=0.0, scale_progress=1.0):
    f = Fernet(key)
    file_size = os.path.getsize(encrypted_path)
    processed = 0

    # Handle both file paths and file-like objects (BytesIO)
    if isinstance(output_path, str):
        outfile = open(output_path, 'wb')
        close_outfile = True
    else:
        outfile = output_path
        close_outfile = False

    try:
        with open(encrypted_path, 'rb') as infile:
            current_pos = infile.tell()
            if current_pos == 0:
                magic = infile.read(4)
                if magic in [MAGIC_HEADER, MAGIC_HEADER_BETTER, MAGIC_HEADER_PC]:
                    pass # Header skipped
                else:
                    infile.seek(0)

            while True:
                size_data = infile.read(4)
                if not size_data:
                    break

                chunk_size = struct.unpack('<I', size_data)[0]
                encrypted_chunk = infile.read(chunk_size)

                if len(encrypted_chunk) != chunk_size:
                    raise ValueError("Corrupted file or wrong key")

                decrypted_chunk = f.decrypt(encrypted_chunk)
                outfile.write(decrypted_chunk)

                processed += chunk_size
                if progress_callback:
                    relative_p = processed / file_size
                    total_p = offset_progress + (relative_p * scale_progress)
                    progress_callback(total_p)
    finally:
        if close_outfile:
            outfile.close()

def protect_process(target_path, destination_drive, mode="standard", progress_callback=None, status_callback=None, use_max_hardware=False, custom_layers=10):
    # Determine temp dir
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Check source size
        total_size = 0
        if os.path.isfile(target_path):
            total_size = os.path.getsize(target_path)
        else:
            for root, _, files in os.walk(target_path):
                for f in files:
                    total_size += os.path.getsize(os.path.join(root, f))

        # Check C: space
        if get_disk_space(temp_dir) < total_size:
            secure_delete_directory(temp_dir) 
            usb_temp = os.path.join(destination_drive, "PS_TEMP")
            os.makedirs(usb_temp, exist_ok=True)
            temp_dir = tempfile.mkdtemp(dir=usb_temp)
            
            if get_disk_space(temp_dir) < total_size:
                 secure_delete_directory(temp_dir)
                 raise OSError("Not enough disk space on both PC and USB Drive to prepare files.")
    except Exception as e:
        if os.path.exists(temp_dir): secure_delete_directory(temp_dir)
        raise e

    zip_name = "data.pkg"
    temp_zip_path = os.path.join(temp_dir, zip_name)
    
    try:
        if status_callback: status_callback("Packing files (Checking space first)...")
        zip_target(target_path, temp_zip_path, stored_only=True)
        
        filename = os.path.basename(target_path) or "folder"
        output_name = os.path.splitext(filename)[0]
        
        container_dir = os.path.join(destination_drive, output_name + "_Secure")
        os.makedirs(container_dir, exist_ok=True)
        
        final_output_path = os.path.join(container_dir, output_name + ".secure")
        final_key_path = os.path.join(container_dir, output_name + ".key")
        
        if mode == "better":
            # Use custom layers count
            num_layers = custom_layers
            keys = [generate_key() for _ in range(num_layers)]
            current_input = temp_zip_path
            
            for i, key in enumerate(keys):
                next_temp = os.path.join(temp_dir, f"temp_{i}.enc")
                
                if status_callback: status_callback(f"Better Protect: Layer {i+1}/{num_layers}...")
                offset = i / float(num_layers)
                scale = 1.0 / float(num_layers)
                
                # Only last layer gets the magic header
                header_to_use = b'' if i < (num_layers - 1) else MAGIC_HEADER_BETTER
                
                encrypt_file_pipelined(current_input, key, next_temp, 
                                     header=header_to_use, 
                                     progress_callback=progress_callback,
                                     offset_progress=offset,
                                     scale_progress=scale,
                                     use_max_hardware=use_max_hardware)
                
                if i > 0:
                     secure_delete_file(current_input)
                current_input = next_temp
            
            if status_callback: status_callback("Finalizing...")
            shutil.move(current_input, final_output_path)
            
            master_token = generate_key()
            f = Fernet(master_token)
            keys_data = json.dumps([k.decode() for k in keys]).encode()
            encrypted_keys = f.encrypt(keys_data)
            
            with open(final_output_path + ".keystore", "wb") as f:
                f.write(encrypted_keys)
            return master_token, final_output_path
            
        elif mode == "pc_lock":
            if status_callback: status_callback("Locking to PC...")
            pc_key = get_pc_signature()
            file_key = generate_key()
            
            encrypt_file_pipelined(temp_zip_path, file_key, final_output_path, 
                                 header=MAGIC_HEADER_PC, 
                                 progress_callback=progress_callback,
                                 use_max_hardware=use_max_hardware)
            
            f_pc = Fernet(pc_key)
            encrypted_file_key = f_pc.encrypt(file_key)
            with open(final_key_path, "wb") as f:
                f.write(encrypted_file_key)
            return b"PC_LOCKED", final_output_path
            
        else: # Standard
            if status_callback: status_callback("Encrypting...")
            token = generate_key()
            encrypt_file_pipelined(temp_zip_path, token, final_output_path, 
                                 progress_callback=progress_callback,
                                 use_max_hardware=use_max_hardware)
            return token, final_output_path
            
    finally:
        # SECURE DELETE: Overwrite all temp files before deletion
        secure_delete_directory(temp_dir)

def decrypt_secure_to_memory(encrypted_path, token):
    """
    Decrypts the entire secure file to memory, handling all encryption modes.
    Returns BytesIO containing the decrypted ZIP.
    """
    with open(encrypted_path, 'rb') as f:
        header = f.read(4)
    
    zip_data = io.BytesIO()
    
    if header == MAGIC_HEADER_BETTER:
        # Better Protect Mode (Multi-layer)
        keystore_path = encrypted_path + ".keystore"
        if not os.path.exists(keystore_path):
            raise FileNotFoundError(f"Keystore file missing: {keystore_path}")
            
        with open(keystore_path, 'rb') as f:
            encrypted_keys = f.read()
            
        f_master = Fernet(token)
        try:
            keys_data = f_master.decrypt(encrypted_keys)
        except:
            raise ValueError("Invalid Token or Corrupted Keystore")
            
        keys = json.loads(keys_data.decode())
        keys = [k.encode() for k in keys]
        
        current_input = encrypted_path
        num_layers = len(keys)
        
        # Decrypt layers in reverse
        temp_dir = tempfile.mkdtemp()
        try:
            for i in range(num_layers - 1, -1, -1):
                key = keys[i]
                next_output = os.path.join(temp_dir, f"temp_dec_{i}.pkg")
                
                decrypt_file_chunked(current_input, key, next_output)
                
                if current_input != encrypted_path:
                    secure_delete_file(current_input)
                current_input = next_output
                
            # Read final decrypted file to memory
            with open(current_input, 'rb') as f:
                zip_data.write(f.read())
            zip_data.seek(0)
        finally:
            # SECURE DELETE: Overwrite all temp files before deletion
            secure_delete_directory(temp_dir)
            
    elif header == MAGIC_HEADER_PC:
        # PC Lock Mode
        decrypt_file_chunked(encrypted_path, token, zip_data)
        zip_data.seek(0)
        
    elif header == MAGIC_HEADER or header == b'PSv2':
        # Standard V2
        decrypt_file_chunked(encrypted_path, token, zip_data)
        zip_data.seek(0)
        
    else:
        # Legacy
        f = Fernet(token)
        with open(encrypted_path, 'rb') as infile:
            data = infile.read()
        decrypted = f.decrypt(data)
        zip_data.write(decrypted)
        zip_data.seek(0)
    
    return zip_data

def decrypt_file_to_memory(encrypted_path, token, file_path_in_zip):
    """
    Decrypts a specific file from the secure container to memory.
    Returns BytesIO object.
    """
    try:
        # Decrypt the ZIP to memory first
        zip_data = decrypt_secure_to_memory(encrypted_path, token)

        # Open the ZIP in memory
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            if file_path_in_zip in zip_ref.namelist():
                file_data = zip_ref.read(file_path_in_zip)
                return io.BytesIO(file_data)
            else:
                raise FileNotFoundError(f"File {file_path_in_zip} not found in archive")

    except Exception as e:
        raise e

def unload_process(encrypted_path, token, progress_callback=None, status_callback=None):
    with open(encrypted_path, 'rb') as f:
        header = f.read(4)
        
    temp_dir = tempfile.mkdtemp()
    decrypted_zip_path = os.path.join(temp_dir, "decrypted.pkg")
    
    try:
        if header == MAGIC_HEADER_BETTER:
            if status_callback: status_callback("Unlocking Keystore...")
            keystore_path = encrypted_path + ".keystore"
            if not os.path.exists(keystore_path):
                # Try finding it in the same directory using different naming conventions if needed
                # But standard is file.secure + .keystore
                pass
                
            if not os.path.exists(keystore_path):
                 raise FileNotFoundError(f"Keystore file missing: {keystore_path}")
                
            with open(keystore_path, 'rb') as f:
                encrypted_keys = f.read()
                
            f_master = Fernet(token)
            try:
                keys_data = f_master.decrypt(encrypted_keys)
            except:
                raise ValueError("Invalid Token or Corrupted Keystore")
                
            keys = json.loads(keys_data.decode())
            keys = [k.encode() for k in keys]
            
            current_input = encrypted_path
            num_layers = len(keys)
            
            # Decrypt layers in reverse
            for i in range(num_layers - 1, -1, -1):
                key = keys[i]
                next_output = os.path.join(temp_dir, f"temp_dec_{i}.pkg")
                
                if status_callback: status_callback(f"Decrypting Layer {num_layers-i}/{num_layers}...")
                
                offset = (num_layers - 1 - i) / float(num_layers)
                scale = 1.0 / float(num_layers)
                
                decrypt_file_chunked(current_input, key, next_output, 
                                     progress_callback=progress_callback,
                                     offset_progress=offset,
                                     scale_progress=scale)
                
                if current_input != encrypted_path:
                    secure_delete_file(current_input)
                current_input = next_output
                
            shutil.move(current_input, decrypted_zip_path)
            
        elif header == MAGIC_HEADER_PC:
            if status_callback: status_callback("Verifying PC Signature...")
            decrypt_file_chunked(encrypted_path, token, decrypted_zip_path, progress_callback=progress_callback)

        elif header == MAGIC_HEADER or header == b'PSv2':
            if status_callback: status_callback("Decrypting...")
            decrypt_file_chunked(encrypted_path, token, decrypted_zip_path, progress_callback=progress_callback)
            
        else:
            if status_callback: status_callback("Decrypting (Legacy)...")
            f = Fernet(token)
            with open(encrypted_path, 'rb') as infile:
                 data = infile.read()
            decrypted = f.decrypt(data)
            with open(decrypted_zip_path, 'wb') as outfile:
                 outfile.write(decrypted)

        if status_callback: status_callback("Unpacking files...")
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(decrypted_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            
        return extract_path, temp_dir
        
    except Exception as e:
        # SECURE DELETE: Overwrite temp files before deletion even on error
        secure_delete_directory(temp_dir)
        raise e

def try_unlock_pc_file(key_file_path):
    pc_key = get_pc_signature()
    f = Fernet(pc_key)
    
    with open(key_file_path, 'rb') as file:
        encrypted_key = file.read()
        
    try:
        return f.decrypt(encrypted_key)
    except:
        raise ValueError("This file is locked to another PC. Access Denied.")

# Helper alias for external calls if needed, but we use pipelined internally now
encrypt_file_chunked = encrypt_file_pipelined

def estimate_size(source_path, layers=1):
    total_size = 0
    if os.path.isfile(source_path):
        total_size = os.path.getsize(source_path)
    else:
        for root, _, files in os.walk(source_path):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
                
    # Base64 expansion factor ~1.3333...
    factor = 1.34 # Safe estimate
    final_size = total_size * (factor ** layers)
    return final_size
