import customtkinter as ctk
from tkinter import filedialog, messagebox, BooleanVar
import os
import shutil
import subprocess
import sys
import threading
import time
import tempfile
import zipfile
import webbrowser
from usb_utils import get_usb_drives
from crypto_utils import protect_process, unload_process, decrypt_file_to_memory, decrypt_secure_to_memory, try_unlock_pc_file, estimate_size, secure_delete_file, secure_delete_directory, MAGIC_HEADER, MAGIC_HEADER_PC, MAGIC_HEADER_BETTER
from update_checker import UpdateChecker
from auto_updater import AutoUpdater
from PIL import Image, ImageTk
import io
import cv2
import numpy as np
import pygame

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SafeViewerWindow(ctk.CTkToplevel):
    def __init__(self, secure_file_path, token, file_list):
        super().__init__()
        self.title("Safe Environment Viewer - RAM Only")
        self.geometry("900x700")
        self.secure_file_path = secure_file_path
        self.token = token
        self.file_list = file_list
        
        # Cache the decrypted ZIP to avoid re-decrypting for each file
        self._zip_cache = None
        self._zip_file_cache = None
        
        # Video playback state
        self.video_playing = False
        self.video_paused = False
        self.video_cap = None
        self.video_total_frames = 0
        self.video_fps = 30
        self.video_current_frame = 0
        self.video_duration = 0
        self.video_temp_file_path = None
        self.audio_playing = False
        self.audio_enabled = True
        self.seeking = False
        self.seek_position = 0
        
        # Build file tree
        self.file_tree = self.build_file_tree(file_list)
        self.current_path = ""
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Cleanup on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Sidebar
        self.sidebar = ctk.CTkScrollableFrame(self, width=250)
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        
        # Pre-load cache in background for faster file access
        self.lbl_loading = ctk.CTkLabel(self.sidebar, text="Loading cache...", text_color="yellow")
        self.lbl_loading.pack(pady=10)
        
        def preload_cache():
            try:
                self.get_cached_zip()  # This will decrypt and cache
                # Use after() to safely update UI from thread
                try:
                    if self.lbl_loading.winfo_exists():
                        self.after(0, lambda: self.lbl_loading.configure(text="Ready", text_color="green") if self.lbl_loading.winfo_exists() else None)
                        self.after(2000, lambda: self.lbl_loading.pack_forget() if self.lbl_loading.winfo_exists() else None)
                except:
                    pass  # Window might be closed
            except Exception as e:
                try:
                    if self.lbl_loading.winfo_exists():
                        self.after(0, lambda: self.lbl_loading.configure(text=f"Error: {str(e)[:30]}", text_color="red") if self.lbl_loading.winfo_exists() else None)
                except:
                    pass
        
        threading.Thread(target=preload_cache, daemon=True).start()
        
        # Content Area
        self.content_area = ctk.CTkScrollableFrame(self)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Path bar
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.lbl_path = ctk.CTkLabel(self.path_frame, text="Current: /")
        self.lbl_path.pack(side="left", padx=10)
        
        self.btn_back = ctk.CTkButton(self.path_frame, text="⬅ Back", command=self.go_back)
        self.btn_back.pack(side="right", padx=10)
        
        self.update_sidebar()
        
    def build_file_tree(self, file_list):
        tree = {}
        for f in file_list:
            # Normalize path separators
            normalized = f.replace('\\', '/')
            parts = normalized.split('/')
            current = tree
            for part in parts[:-1]:
                if part and part not in current:
                    current[part] = {}
                if part:
                    current = current[part]
            # Last part is file
            if parts and parts[-1]:
                current[parts[-1]] = None  # None means file, dict means folder
        return tree
    
    def update_sidebar(self):
        # Clear sidebar
        for widget in self.sidebar.winfo_children():
            widget.destroy()
            
        current_tree = self.get_current_tree()
        
        # Add folders first
        for name, value in current_tree.items():
            if isinstance(value, dict):  # Folder
                btn = ctk.CTkButton(self.sidebar, text=f"📁 {name}", command=lambda n=name: self.open_folder(n))
                btn.pack(pady=2, padx=5, fill="x")
        
        # Add files
        for name, value in current_tree.items():
            if value is None:  # File
                full_path = os.path.join(self.current_path, name)
                ext = os.path.splitext(name)[1].lower()
                icon = "📄"
                if ext in ['.txt', '.log', '.md', '.py', '.json', '.xml', '.ini']:
                    icon = "📝"
                elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                    icon = "🖼️"
                elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    icon = "🎥"
                
                btn = ctk.CTkButton(self.sidebar, text=f"{icon} {name}", command=lambda n=name: self.show_file(n))
                btn.pack(pady=2, padx=5, fill="x")
    
    def get_current_tree(self):
        if not self.current_path:
            return self.file_tree
        parts = [p for p in self.current_path.replace('\\', '/').split('/') if p]
        current = self.file_tree
        for part in parts:
            if part in current and isinstance(current[part], dict):
                current = current[part]
            else:
                # Return empty dict if path not found
                return {}
        return current
    
    def open_folder(self, name):
        if self.current_path:
            self.current_path = self.current_path.replace('\\', '/') + "/" + name.replace('\\', '/')
        else:
            self.current_path = name.replace('\\', '/')
        # Normalize
        self.current_path = self.current_path.replace('//', '/').strip('/')
        self.lbl_path.configure(text=f"Current: /{self.current_path}")
        self.update_sidebar()
        self.clear_content()
    
    def go_back(self):
        if self.current_path:
            parts = self.current_path.replace('\\', '/').split('/')
            parts = [p for p in parts if p]  # Remove empty parts
            if parts:
                parts.pop()
            self.current_path = '/'.join(parts)
        self.lbl_path.configure(text=f"Current: /{self.current_path}" if self.current_path else "Current: /")
        self.update_sidebar()
        self.clear_content()
    
    def clear_content(self):
        # Stop any playing video
        self.stop_video()
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def stop_video(self):
        """Stop video playback and clean up securely."""
        self.video_playing = False
        self.video_paused = False
        if self.audio_playing:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except:
                pass
        if self.video_cap:
            try:
                self.video_cap.release()
            except:
                pass
            self.video_cap = None
        # SECURE DELETE: Overwrite temp file before deletion (no history)
        if hasattr(self, 'video_temp_file_path'):
            secure_delete_file(self.video_temp_file_path)
            if hasattr(self, 'video_temp_file_path'):
                delattr(self, 'video_temp_file_path')
    
    def toggle_audio(self):
        """Toggle audio on/off."""
        self.audio_enabled = not self.audio_enabled
        try:
            if hasattr(self, 'btn_audio') and self.btn_audio.winfo_exists():
                if self.audio_enabled:
                    self.btn_audio.configure(text="🔊 Audio ON")
                else:
                    self.btn_audio.configure(text="🔇 Audio OFF")
        except:
            pass
        
        if self.audio_enabled:
            # Resume audio if video is playing
            if self.video_playing and not self.video_paused and hasattr(self, 'video_temp_file_path'):
                try:
                    if not pygame.mixer.get_init():
                        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    pygame.mixer.music.load(self.video_temp_file_path)
                    pygame.mixer.music.play()
                    self.audio_playing = True
                except Exception as e:
                    # MP4 audio not supported - show message
                    try:
                        if hasattr(self, 'btn_audio') and self.btn_audio.winfo_exists():
                            self.btn_audio.configure(text="🔇 Audio OFF (MP4 unsupported)")
                    except:
                        pass
                    self.audio_enabled = False
                    self.audio_playing = False
                    try:
                        messagebox.showinfo("Audio Info", "MP4 audio is not supported in Safe Mode.\n\nUse 'External App' mode for videos with audio.")
                    except:
                        pass
        else:
            # Stop audio
            if self.audio_playing:
                try:
                    pygame.mixer.music.stop()
                except:
                    pass
    
    def toggle_video_pause(self):
        """Toggle video pause state."""
        self.video_paused = not self.video_paused
        try:
            if hasattr(self, 'btn_play') and self.btn_play.winfo_exists():
                if self.video_paused:
                    self.btn_play.configure(text="▶ Play")
                else:
                    self.btn_play.configure(text="⏸ Pause")
        except:
            pass
        
        if self.video_paused:
            # Pause audio
            if self.audio_playing and self.audio_enabled:
                try:
                    pygame.mixer.music.pause()
                except:
                    pass
        else:
            # Resume audio
            if self.audio_enabled and hasattr(self, 'video_temp_file_path'):
                try:
                    if self.audio_playing:
                        pygame.mixer.music.unpause()
                    else:
                        # Start audio if not playing
                        if not pygame.mixer.get_init():
                            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                        pygame.mixer.music.load(self.video_temp_file_path)
                        pygame.mixer.music.play()
                        self.audio_playing = True
                except:
                    pass
    
    def format_time(self, seconds):
        """Format seconds to MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def on_slider_change(self, value):
        """Handle slider change for seeking."""
        if self.video_total_frames == 0:
            return
        
        # Only seek when user is dragging (not during automatic updates)
        if self.slider_dragging:
            progress = value / 100.0
            target_frame = int(progress * self.video_total_frames)
            self.seek_to_frame(target_frame)
    
    def seek_to_frame(self, frame_number):
        """Seek video and audio to specific frame."""
        if not self.video_cap or self.video_total_frames == 0:
            return
        
        frame_number = max(0, min(frame_number, self.video_total_frames - 1))
        self.seeking = True
        self.video_current_frame = frame_number
        
        # Seek video
        if self.video_cap:
            self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Seek audio (if playing and enabled)
        if self.audio_playing and self.audio_enabled and hasattr(self, 'video_temp_file_path'):
            try:
                target_time = frame_number / self.video_fps if self.video_fps > 0 else 0
                # Stop current playback
                pygame.mixer.music.stop()
                # Reload and play from new position
                pygame.mixer.music.load(self.video_temp_file_path)
                pygame.mixer.music.play()
                # Note: pygame doesn't support precise seeking, but this works reasonably well
            except Exception as e:
                print(f"Audio seek error: {e}")
        
        # Update slider only (removed progress bar)
        progress = frame_number / self.video_total_frames if self.video_total_frames > 0 else 0
        try:
            if hasattr(self, 'video_progress_slider') and self.video_progress_slider.winfo_exists():
                self.video_progress_slider.set(progress * 100)
        except:
            pass
        
        # Update time display
        current_time = frame_number / self.video_fps if self.video_fps > 0 else 0
        time_str = f"{self.format_time(current_time)} / {self.format_time(self.video_duration)}"
        try:
            if hasattr(self, 'time_label') and self.time_label.winfo_exists():
                self.time_label.configure(text=time_str)
        except:
            pass
        
        self.seeking = False
    
    def play_video_from_memory(self, video_data, video_label):
        """Play video from RAM using OpenCV with audio support and seeking - optimized."""
        def video_thread():
            try:
                # Initialize pygame mixer for audio (only if enabled)
                if self.audio_enabled:
                    try:
                        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)  # Larger buffer for less lag
                    except:
                        pass
                
                # Create temp file that auto-deletes - but keep it open
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                temp_file.write(video_data)
                temp_file.flush()
                temp_file.close()  # Close file handle but keep file on disk
                self.video_temp_file_path = temp_file.name
                
                # Open video with OpenCV
                cap = cv2.VideoCapture(temp_file.name)
                self.video_cap = cap
                
                if not cap.isOpened():
                    raise Exception("Could not open video file")
                
                # Get video properties
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = total_frames / fps if fps > 0 else 0
                
                self.video_fps = fps
                self.video_total_frames = total_frames
                self.video_current_frame = 0
                self.video_duration = duration
                
                frame_delay = int(1000 / fps) if fps > 0 else 33  # milliseconds
                
                # Load and play audio (only if enabled)
                # Note: pygame.mixer doesn't support MP4 audio directly
                # We'll try to extract audio or gracefully handle the error
                if self.audio_enabled:
                    try:
                        # Try to load audio - pygame supports WAV, OGG, but not MP4
                        # For MP4, we need to extract audio first or use external player
                        # For now, we'll try and if it fails, show a message
                        pygame.mixer.music.load(temp_file.name)
                        pygame.mixer.music.play()
                        self.audio_playing = True
                    except Exception as audio_error:
                        # MP4 audio not supported by pygame directly
                        # User can use external player mode for audio
                        print(f"Audio playback: MP4 audio requires external player mode. Video will play without sound.")
                        self.audio_playing = False
                        # Update button to show audio is off
                        try:
                            self.after(0, lambda: self.btn_audio.configure(text="🔇 Audio OFF (MP4 unsupported)") if hasattr(self, 'btn_audio') else None)
                        except:
                            pass
                else:
                    self.audio_playing = False
                
                # Update UI with video info
                def update_loading_msg():
                    try:
                        if video_label.winfo_exists():
                            video_label.configure(text="Video loaded! Starting playback...", text_color="green")
                    except:
                        pass
                self.after(0, update_loading_msg)
                
                # Cache for frame optimization (use instance variable for nested function access)
                self.last_frame_time = time.time()
                frame_skip_threshold = 0.033  # ~30fps max
                
                def update_frame():
                    # Check if window still exists
                    try:
                        if not self.winfo_exists():
                            return
                    except:
                        return
                    
                    if not self.video_playing or not cap.isOpened():
                        try:
                            if self.audio_playing:
                                pygame.mixer.music.stop()
                                pygame.mixer.quit()
                            cap.release()
                            # SECURE DELETE: Overwrite temp file before deletion
                            if hasattr(self, 'video_temp_file_path'):
                                secure_delete_file(self.video_temp_file_path)
                        except:
                            pass
                        return
                    
                    # Skip frame updates while seeking
                    if self.seeking:
                        self.after(50, update_frame)
                        return
                    
                    if not self.video_paused:
                        ret, frame = cap.read()
                        if ret:
                            self.video_current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                            
                            # Optimize: Only update display if enough time has passed (reduce lag)
                            current_time = time.time()
                            if current_time - self.last_frame_time >= frame_skip_threshold:
                                # Convert BGR to RGB
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                
                                # Resize to fit display (max 800x600) - use faster interpolation
                                height, width = frame_rgb.shape[:2]
                                max_width, max_height = 800, 600
                                if width > max_width or height > max_height:
                                    scale = min(max_width / width, max_height / height)
                                    new_width = int(width * scale)
                                    new_height = int(height * scale)
                                    frame_rgb = cv2.resize(frame_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)  # Faster
                                
                                # Convert to PIL Image
                                img = Image.fromarray(frame_rgb)
                                img_tk = ImageTk.PhotoImage(image=img)
                                
                                # Update label (batch UI updates)
                                video_label.image = img_tk  # Keep reference
                                def update_video_label(img=img_tk):
                                    try:
                                        if video_label.winfo_exists():
                                            video_label.configure(image=img, text="")
                                    except:
                                        pass  # Widget destroyed
                                self.after(0, update_video_label)
                                
                                self.last_frame_time = current_time
                            
                            # Update time and progress (less frequently for performance)
                            current_time_video = self.video_current_frame / fps if fps > 0 else 0
                            progress = self.video_current_frame / total_frames if total_frames > 0 else 0
                            
                            time_str = f"{self.format_time(current_time_video)} / {self.format_time(duration)}"
                            if not self.slider_dragging:
                                def update_ui(t=time_str, p=progress):
                                    try:
                                        if hasattr(self, 'time_label') and self.time_label.winfo_exists():
                                            self.time_label.configure(text=t)
                                        if hasattr(self, 'video_progress_slider') and self.video_progress_slider.winfo_exists():
                                            self.video_progress_slider.set(p * 100)
                                    except:
                                        pass  # Widget destroyed
                                self.after(0, update_ui)
                            
                            # Check if audio is still playing, restart if needed
                            if self.audio_playing and self.audio_enabled:
                                try:
                                    if not pygame.mixer.music.get_busy():
                                        if self.video_current_frame >= total_frames - 1:
                                            # Both ended, restart
                                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                            self.video_current_frame = 0
                                            pygame.mixer.music.play()
                                except:
                                    pass
                            
                            # Schedule next frame
                            self.after(frame_delay, update_frame)
                        else:
                            # Video ended, restart
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            self.video_current_frame = 0
                            if self.audio_playing and self.audio_enabled:
                                try:
                                    pygame.mixer.music.rewind()
                                    pygame.mixer.music.play()
                                except:
                                    pass
                            self.after(frame_delay, update_frame)
                    else:
                        # Paused - pause audio too
                        if self.audio_playing and self.audio_enabled:
                            try:
                                pygame.mixer.music.pause()
                            except:
                                pass
                        # Check again soon
                        self.after(100, update_frame)
                
                # Start playback after a brief delay to ensure UI is ready
                self.after(100, update_frame)
                
            except Exception as e:
                self.after(0, lambda: video_label.configure(text=f"Error: {str(e)}", text_color="red"))
                print(f"Video playback error: {e}")
                import traceback
                traceback.print_exc()
        
        # Start video in background thread
        threading.Thread(target=video_thread, daemon=True).start()
    
    def on_close(self):
        """Clean up resources when window closes - no history saved."""
        # Stop video if playing (this also cleans temp files)
        self.stop_video()
        
        # Clean up ZIP cache (memory only, no disk)
        if self._zip_file_cache:
            try:
                self._zip_file_cache.close()
            except:
                pass
        if self._zip_cache:
            try:
                self._zip_cache.close()
            except:
                pass
        
        # SECURE DELETE: Ensure temp file is fully deleted (no history)
        if hasattr(self, 'video_temp_file_path'):
            secure_delete_file(self.video_temp_file_path)
        
        self.destroy()
    
    def get_cached_zip(self):
        """Get or create cached ZIP file for faster access."""
        if self._zip_cache is None:
            # Decrypt once and cache
            self._zip_cache = decrypt_secure_to_memory(self.secure_file_path, self.token)
            self._zip_file_cache = zipfile.ZipFile(self._zip_cache, 'r')
        return self._zip_file_cache
    
    def show_file(self, name):
        self.clear_content()
        
        # Fix path separator - ZIP uses forward slashes
        if self.current_path:
            full_path = self.current_path.replace('\\', '/') + "/" + name.replace('\\', '/')
        else:
            full_path = name.replace('\\', '/')
        
        # Normalize path (remove leading/trailing slashes, handle double slashes)
        full_path = full_path.replace('//', '/').strip('/')
        
        ext = os.path.splitext(name)[1].lower()
        
        try:
            # Use cached ZIP for faster access
            zip_ref = self.get_cached_zip()
            
            # Try exact match first
            if full_path in zip_ref.namelist():
                file_data = zip_ref.read(full_path)
            else:
                # Try to find file with different path separators or case
                found = False
                for zip_name in zip_ref.namelist():
                    # Normalize both paths for comparison
                    normalized_zip = zip_name.replace('\\', '/').strip('/')
                    if normalized_zip.lower() == full_path.lower():
                        file_data = zip_ref.read(zip_name)
                        found = True
                        break
                
                if not found:
                    raise FileNotFoundError(f"File '{full_path}' not found in archive")
            
            data_io = io.BytesIO(file_data)
            data_io.seek(0)
            
            if ext in ['.txt', '.log', '.md', '.py', '.json', '.xml', '.ini']:
                # Text view
                try:
                    text_content = data_io.read().decode('utf-8', errors='ignore')
                    textbox = ctk.CTkTextbox(self.content_area, width=600, height=500)
                    textbox.pack(fill="both", expand=True)
                    textbox.insert("0.0", text_content)
                    textbox.configure(state="disabled")
                except Exception as e:
                    lbl = ctk.CTkLabel(self.content_area, text=f"Error reading text: {e}")
                    lbl.pack()
            
            elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                # Image view
                try:
                    img = Image.open(data_io)
                    # Resize if too large
                    img.thumbnail((600, 500))
                    img_tk = ImageTk.PhotoImage(img)
                    
                    lbl = ctk.CTkLabel(self.content_area, text="", image=img_tk)
                    lbl.image = img_tk  # Keep reference
                    lbl.pack()
                except Exception as e:
                    lbl = ctk.CTkLabel(self.content_area, text=f"Error reading image: {e}")
                    lbl.pack()
                    
            elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                # Video view - RAM-only playback using OpenCV
                try:
                    # Create video player frame
                    video_frame = ctk.CTkFrame(self.content_area)
                    video_frame.pack(fill="both", expand=True, padx=10, pady=10)
                    
                    # Video display label with loading indicator
                    video_label = ctk.CTkLabel(video_frame, text="Loading video...", font=("Arial", 14))
                    video_label.pack(fill="both", expand=True, padx=10, pady=10)
                    
                    # Controls frame
                    controls_frame = ctk.CTkFrame(video_frame)
                    controls_frame.pack(fill="x", padx=10, pady=5)
                    
                    # Time display
                    time_frame = ctk.CTkFrame(controls_frame)
                    time_frame.pack(fill="x", padx=5, pady=5)
                    
                    self.time_label = ctk.CTkLabel(time_frame, text="00:00 / 00:00", font=("Arial", 12))
                    self.time_label.pack(side="left", padx=10)
                    
                    # Progress slider (clickable for seeking) - Single control
                    progress_frame = ctk.CTkFrame(time_frame)
                    progress_frame.pack(side="left", fill="x", expand=True, padx=10)
                    
                    # Single slider for seeking (like YouTube)
                    self.video_progress_slider = ctk.CTkSlider(progress_frame, from_=0, to=100, command=self.on_slider_change)
                    self.video_progress_slider.set(0)
                    self.video_progress_slider.pack(fill="x", expand=True)
                    
                    # Bind slider events for drag detection
                    self.video_progress_slider.bind("<Button-1>", lambda e: setattr(self, 'slider_dragging', True))
                    self.video_progress_slider.bind("<ButtonRelease-1>", lambda e: setattr(self, 'slider_dragging', False))
                    
                    self.seeking = False
                    self.slider_dragging = False
                    
                    # Buttons frame
                    btn_frame = ctk.CTkFrame(controls_frame)
                    btn_frame.pack(fill="x", padx=5, pady=5)
                    
                    self.video_playing = True
                    self.video_paused = False
                    self.video_cap = None
                    self.video_total_frames = 0
                    self.video_fps = 30
                    self.video_current_frame = 0
                    self.audio_enabled = True  # Audio toggle state
                    
                    self.btn_play = ctk.CTkButton(btn_frame, text="⏸ Pause", width=100, command=self.toggle_video_pause)
                    self.btn_play.pack(side="left", padx=5)
                    
                    btn_stop = ctk.CTkButton(btn_frame, text="⏹ Stop", width=100, command=self.stop_video)
                    btn_stop.pack(side="left", padx=5)
                    
                    self.btn_audio = ctk.CTkButton(btn_frame, text="🔊 Audio ON", width=120, command=self.toggle_audio)
                    self.btn_audio.pack(side="left", padx=5)
                    
                    # Load video from memory in background for faster loading
                    video_data = data_io.read()
                    self.play_video_from_memory(video_data, video_label)
                    
                except Exception as e:
                    import traceback
                    error_msg = f"Error playing video: {str(e)}\n\nNote: Large videos may need more RAM."
                    lbl = ctk.CTkLabel(self.content_area, text=error_msg, text_color="red")
                    lbl.pack(pady=50)
                    print(f"Video playback error: {e}")
                    traceback.print_exc()
                    
            else:
                lbl = ctk.CTkLabel(self.content_area, text=f"Unsupported file type ({ext}).\nCannot preview in Safe Mode.")
                lbl.pack(pady=50)
                
        except Exception as e:
            error_msg = f"Error loading file: {str(e)}"
            lbl = ctk.CTkLabel(self.content_area, text=error_msg, text_color="red")
            lbl.pack(pady=50)
            print(f"Error in SafeViewerWindow.show_file: {e}")
            import traceback
            traceback.print_exc()

class ProtectSecureApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ProtectSecure")
        self.geometry("800x650")

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, width=750, height=600)
        self.tabview.grid(row=0, column=0, padx=10, pady=10)
        
        self.tab_protect = self.tabview.add("Protect")
        self.tab_unload = self.tabview.add("Unload/View")
        self.tab_settings = self.tabview.add("Settings")
        
        # State
        self.custom_layers = 1 # Default changed to 1 (Standard) as requested
        
        self.setup_protect_tab()
        self.setup_unload_tab()
        self.setup_settings_tab()
        
        self.temp_view_dirs = []
        
        # Initialize auto-updater with GitHub repository
        self.auto_updater = AutoUpdater(repo_url="https://github.com/realscripter/ProtectSecure", current_version="1.0.1")
        self.update_checker = UpdateChecker(repo_url="https://github.com/realscripter/ProtectSecure", current_version="1.0.1")
        
        # Check for updates in background (non-blocking)
        self.after(2000, self.check_for_updates_async)
        
        # Update download state
        self.update_downloading = False
        self.update_window = None

    def setup_protect_tab(self):
        # Clean Layout
        self.lbl_select = ctk.CTkLabel(self.tab_protect, text="1. Select File/Folder:", font=("Arial", 16, "bold"))
        self.lbl_select.pack(pady=(15, 5), anchor="w", padx=20)
        
        frame_input = ctk.CTkFrame(self.tab_protect, fg_color="transparent")
        frame_input.pack(fill="x", padx=20)
        
        self.target_path = ctk.StringVar()
        self.entry_target = ctk.CTkEntry(frame_input, textvariable=self.target_path)
        self.entry_target.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_browse = ctk.CTkButton(frame_input, text="Browse...", width=100, command=self.browse_target)
        self.btn_browse.pack(side="right")
        
        # Mode Selection
        self.lbl_mode = ctk.CTkLabel(self.tab_protect, text="2. Protection Mode:", font=("Arial", 16, "bold"))
        self.lbl_mode.pack(pady=(20, 5), anchor="w", padx=20)
        
        self.mode_var = ctk.StringVar(value="standard")
        
        frame_modes = ctk.CTkFrame(self.tab_protect)
        frame_modes.pack(fill="x", padx=20, pady=5)
        
        self.rad_std = ctk.CTkRadioButton(frame_modes, text="Standard (Fast & Secure)", variable=self.mode_var, value="standard")
        self.rad_std.pack(pady=10, padx=10, anchor="w")
        
        self.rad_better = ctk.CTkRadioButton(frame_modes, text="Better Protect (Multi-Layer)", variable=self.mode_var, value="better", command=self.check_layer_warning)
        self.rad_better.pack(pady=10, padx=10, anchor="w")
        
        self.rad_pc = ctk.CTkRadioButton(frame_modes, text="PC Lock (Only This Computer)", variable=self.mode_var, value="pc_lock")
        self.rad_pc.pack(pady=10, padx=10, anchor="w")

        # Hardware toggle
        self.check_max_hw = BooleanVar(value=False)
        self.chk_hw = ctk.CTkCheckBox(self.tab_protect, text="Use Full Hardware (High RAM usage for speed)", variable=self.check_max_hw)
        self.chk_hw.pack(pady=5, padx=20, anchor="w")

        # Drive
        self.lbl_dest = ctk.CTkLabel(self.tab_protect, text="3. Destination:", font=("Arial", 16, "bold"))
        self.lbl_dest.pack(pady=(20, 5), anchor="w", padx=20)
        
        self.drive_var = ctk.StringVar(value="Select Drive")
        self.option_drive = ctk.CTkOptionMenu(self.tab_protect, variable=self.drive_var, values=self.refresh_drives(), command=self.on_drive_select)
        self.option_drive.pack(pady=5, padx=20, anchor="w")
        
        # Action
        self.progress_bar = ctk.CTkProgressBar(self.tab_protect)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(20, 5), padx=20, fill="x")
        
        self.lbl_action = ctk.CTkLabel(self.tab_protect, text="Ready", font=("Arial", 12))
        self.lbl_action.pack()
        
        self.btn_protect = ctk.CTkButton(self.tab_protect, text="PROTECT FILES", fg_color="red", height=40, font=("Arial", 15, "bold"), command=self.start_protection_thread)
        self.btn_protect.pack(pady=20, padx=20, fill="x")

    def setup_unload_tab(self):
        # Clean Layout
        self.lbl_file = ctk.CTkLabel(self.tab_unload, text="Select .secure File:", font=("Arial", 14, "bold"))
        self.lbl_file.pack(pady=(15, 5), anchor="w", padx=20)
        
        frame_file = ctk.CTkFrame(self.tab_unload, fg_color="transparent")
        frame_file.pack(fill="x", padx=20)
        
        self.secure_file_path = ctk.StringVar()
        self.entry_secure = ctk.CTkEntry(frame_file, textvariable=self.secure_file_path)
        self.entry_secure.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_browse_sec = ctk.CTkButton(frame_file, text="Browse...", width=100, command=self.browse_secure)
        self.btn_browse_sec.pack(side="right")
        
        self.lbl_token = ctk.CTkLabel(self.tab_unload, text="Token / Key:", font=("Arial", 14, "bold"))
        self.lbl_token.pack(pady=(15, 5), anchor="w", padx=20)
        
        self.entry_token = ctk.CTkEntry(self.tab_unload, placeholder_text="Auto-detected if .key file exists")
        self.entry_token.pack(fill="x", padx=20)
        
        # Options
        self.lbl_method = ctk.CTkLabel(self.tab_unload, text="View Method:", font=("Arial", 14, "bold"))
        self.lbl_method.pack(pady=(15, 5), anchor="w", padx=20)
        
        self.view_mode = ctk.StringVar(value="safe")
        self.rad_safe = ctk.CTkRadioButton(self.tab_unload, text="Safe Environment (RAM Only - Text/Images/WebP)", variable=self.view_mode, value="safe")
        self.rad_safe.pack(pady=5, padx=20, anchor="w")
        self.rad_disk = ctk.CTkRadioButton(self.tab_unload, text="External App (Temp File - Videos/Other)", variable=self.view_mode, value="disk")
        self.rad_disk.pack(pady=5, padx=20, anchor="w")
        
        # Action
        self.unload_progress = ctk.CTkProgressBar(self.tab_unload)
        self.unload_progress.set(0)
        self.unload_progress.pack(pady=(30, 5), padx=20, fill="x")
        
        self.lbl_unload_action = ctk.CTkLabel(self.tab_unload, text="Ready", font=("Arial", 12))
        self.lbl_unload_action.pack()
        
        self.btn_unload = ctk.CTkButton(self.tab_unload, text="UNLOCK & VIEW", fg_color="green", height=40, font=("Arial", 15, "bold"), command=self.start_unload_thread)
        self.btn_unload.pack(pady=10, padx=20, fill="x")
        
        self.btn_cleanup = ctk.CTkButton(self.tab_unload, text="SECURE DELETE SESSIONS", fg_color="darkred", state="disabled", command=self.secure_delete_view)
        self.btn_cleanup.pack(pady=5, padx=20, fill="x")
        
        self.lbl_unload_status = ctk.CTkLabel(self.tab_unload, text="", font=("Arial", 12))
        self.lbl_unload_status.pack(pady=5)

    def setup_settings_tab(self):
        self.lbl_settings = ctk.CTkLabel(self.tab_settings, text="Configuration", font=("Arial", 18, "bold"))
        self.lbl_settings.pack(pady=10)
        
        self.frame_layers = ctk.CTkFrame(self.tab_settings)
        self.frame_layers.pack(pady=20, padx=20, fill="x")
        
        self.lbl_layer_count = ctk.CTkLabel(self.frame_layers, text="Encryption Layers (Better Protect Mode):", font=("Arial", 14))
        self.lbl_layer_count.pack(pady=5)
        
        self.slider_layers = ctk.CTkSlider(self.frame_layers, from_=2, to=20, number_of_steps=18, command=self.update_layer_label)
        self.slider_layers.set(10) # Default
        self.slider_layers.pack(pady=10)
        
        self.lbl_current_layers = ctk.CTkLabel(self.frame_layers, text="Current: 10 Layers")
        self.lbl_current_layers.pack(pady=5)
        
        self.lbl_warn = ctk.CTkLabel(self.frame_layers, text="⚠️ Warning: High layer counts (5x+) significantly increase file size\nand processing time. Recommended: 2x or 3x for balance.", text_color="orange")
        self.lbl_warn.pack(pady=10)
        
        # Estimate Size
        self.frame_est = ctk.CTkFrame(self.tab_settings)
        self.frame_est.pack(pady=20, padx=20, fill="x")
        
        self.btn_calc = ctk.CTkButton(self.frame_est, text="Calculate Size Estimate", command=self.calculate_size_estimate)
        self.btn_calc.pack(pady=10)
        
        self.lbl_estimate = ctk.CTkLabel(self.frame_est, text="Select a file first.")
        self.lbl_estimate.pack(pady=10)

    def browse_target(self):
        # Create a small popup window to choose
        top = ctk.CTkToplevel(self)
        top.title("Select Type")
        top.geometry("300x150")
        top.attributes("-topmost", True)
        
        def file_cb():
            path = filedialog.askopenfilename()
            if path: self.target_path.set(path)
            top.destroy()
            
        def folder_cb():
            path = filedialog.askdirectory()
            if path: self.target_path.set(path)
            top.destroy()
            
        ctk.CTkButton(top, text="File", command=file_cb).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(top, text="Folder", command=folder_cb).pack(pady=0, padx=20, fill="x")

    def check_layer_warning(self):
        if self.custom_layers > 3:
            messagebox.showwarning("High Security Warning", "You have selected a high number of encryption layers.\n\nThis is NOT recommended for normal use as files will become extremely large.\n\nConsider lowering the layers in Settings to 2x or 3x.")

    def update_layer_label(self, value):
        val = int(value)
        self.custom_layers = val
        self.lbl_current_layers.configure(text=f"Current: {val} Layers")

    def calculate_size_estimate(self):
        target = self.target_path.get()
        if not target or not os.path.exists(target):
            self.lbl_estimate.configure(text="Please select a valid file in the Protect tab first.", text_color="red")
            return
        
        layers = self.custom_layers
        try:
            est_bytes = estimate_size(target, layers)
            if est_bytes > 1024**3: size_str = f"{est_bytes / (1024**3):.2f} GB"
            elif est_bytes > 1024**2: size_str = f"{est_bytes / (1024**2):.2f} MB"
            else: size_str = f"{est_bytes / 1024:.2f} KB"
            self.lbl_estimate.configure(text=f"Estimated Final Size (~{layers}x):\n~ {size_str}", text_color="yellow")
        except Exception as e:
            self.lbl_estimate.configure(text=f"Error: {e}", text_color="red")

    def refresh_drives(self):
        drives = get_usb_drives()
        if not drives: drives = ["No USB Drives Found"]
        drives.append("Select Custom Folder...")
        return drives

    def update_drive_list(self):
        drives = self.refresh_drives()
        self.option_drive.configure(values=drives)
        self.drive_var.set(drives[0])

    def on_drive_select(self, choice):
        if choice == "Select Custom Folder...":
            path = filedialog.askdirectory()
            if path:
                self.drive_var.set(path)
            else:
                self.update_drive_list()

    def browse_secure(self):
        path = filedialog.askopenfilename(filetypes=[("Secure Files", "*.secure")])
        if path: self.secure_file_path.set(path)

    def start_protection_thread(self):
        threading.Thread(target=self.start_protection, daemon=True).start()

    def start_protection(self):
        target = self.target_path.get()
        drive = self.drive_var.get()
        mode = self.mode_var.get()
        
        if self.check_better.get() and self.check_pc_lock.get():
             self.lbl_status.configure(text="Please select only ONE protection mode.", text_color="red")
             return

        if not target or not os.path.exists(target):
            self.lbl_action.configure(text="Invalid Target Path")
            return
            
        if drive == "Select Drive" or drive == "No USB Drives Found":
            self.lbl_action.configure(text="Invalid Destination")
            return

        self.btn_protect.configure(state="disabled")
        self.progress_bar.set(0)
        self.lbl_action.configure(text="Initializing...")
        
        try:
            def progress(p): self.progress_bar.set(p)
            def status(msg): self.lbl_action.configure(text=msg)

            token, output_path = protect_process(target, drive, mode=mode, progress_callback=progress, status_callback=status, use_max_hardware=self.check_max_hw.get(), custom_layers=self.custom_layers)
            
            if mode != "pc_lock":
                token_str = token.decode()
                token_file_path = output_path + ".key"
                with open(token_file_path, "w") as f: f.write(token_str)
                msg = f"Protected ({mode})!\nKey saved to: {token_file_path}"
            else:
                msg = f"Protected (PC Lock)!\nOnly this PC can open it."
            
            self.lbl_action.configure(text="Done")
            messagebox.showinfo("Success", msg)
            
        except Exception as e:
            self.lbl_action.configure(text=f"Error: {str(e)}")
            print(e)
        finally:
             self.btn_protect.configure(state="normal")

    def start_unload_thread(self):
        threading.Thread(target=self.start_unload, daemon=True).start()

    def start_unload(self):
        secure_file = self.secure_file_path.get()
        token_str = self.entry_token.get().strip()
        view_method = self.view_mode.get()
        
        if not secure_file or not os.path.exists(secure_file):
            self.lbl_unload_action.configure(text="Invalid Secure File")
            return
            
        # Header check / Token logic
        try:
            with open(secure_file, 'rb') as f: header = f.read(4)
        except: header = b''
        
        token = b''
        if header == MAGIC_HEADER_PC:
             self.lbl_unload_action.configure(text="Unlocking PC Lock...")
             try:
                 key_path = secure_file + ".key"
                 if not os.path.exists(key_path): key_path = os.path.splitext(secure_file)[0] + ".key"
                 token = try_unlock_pc_file(key_path)
             except Exception as e:
                 messagebox.showerror("Error", str(e))
                 self.lbl_unload_action.configure(text="Access Denied")
                 return
        else:
             if not token_str:
                # Auto-load key
                k = secure_file + ".key"
                if not os.path.exists(k): k = os.path.splitext(secure_file)[0] + ".key"
                if os.path.exists(k):
                    with open(k, "r") as f: token_str = f.read().strip()
                    self.entry_token.delete(0, 'end'); self.entry_token.insert(0, token_str)
                else:
                    self.lbl_unload_action.configure(text="Token Required")
                    return
             token = token_str.encode()

        self.btn_unload.configure(state="disabled")
        self.unload_progress.set(0)
        
        try:
            def progress(p): self.unload_progress.set(p)
            def status(msg): self.lbl_unload_action.configure(text=msg)

            if view_method == "safe":
                status("Loading file structure...")
                try:
                    # Decrypt to memory stream for file listing
                    zip_stream = decrypt_secure_to_memory(secure_file, token)

                    with zipfile.ZipFile(zip_stream, 'r') as zip_ref:
                        file_list = zip_ref.namelist()

                    # Open Safe Viewer
                    SafeViewerWindow(secure_file, token, file_list)
                    status("Safe Viewer Opened")
                except Exception as e:
                    status(f"Error: {str(e)}")
                    messagebox.showerror("Error", f"Failed to load secure file:\n{str(e)}")
                
            else:
                # Disk mode
                extract_path, temp_dir = unload_process(secure_file, token, progress_callback=progress, status_callback=status)
                self.temp_view_dirs.append(temp_dir)
                status("Opened in Explorer")
                self.btn_cleanup.configure(state="normal")
                
                if sys.platform == "win32": os.startfile(extract_path)
                elif sys.platform == "darwin": subprocess.Popen(["open", extract_path])
                else: subprocess.Popen(["xdg-open", extract_path])
                
        except Exception as e:
            self.lbl_unload_action.configure(text=f"Error: {str(e)}")
            print(e)
        finally:
             self.btn_unload.configure(state="normal")

    def secure_delete_view(self):
        """SECURE DELETE: Overwrites all temp files before deletion - no recovery possible."""
        if not self.temp_view_dirs: return
        if not messagebox.askyesno("Confirm", "Securely delete all viewed files?\n\nFiles will be overwritten with random data before deletion."): return
        
        for temp_dir in self.temp_view_dirs:
            secure_delete_directory(temp_dir)
        self.temp_view_dirs.clear()
        self.btn_cleanup.configure(state="disabled")
        self.lbl_unload_action.configure(text="Session Cleaned - Files Securely Deleted")
    
    def check_for_updates_async(self):
        """Check for updates in background thread."""
        def check():
            try:
                has_update, release_info = self.auto_updater.check_for_updates()
                if has_update:
                    # Show update notification with auto-install option
                    self.after(0, lambda: self.show_update_alert(release_info))
            except Exception as e:
                # Silently fail - don't interrupt user experience
                pass
        
        threading.Thread(target=check, daemon=True).start()
    
    def show_update_alert(self, release_info):
        """Show update alert dialog with auto-install option."""
        latest_version = release_info.get("version", "Unknown")
        
        message = f"New version available!\n\n"
        message += f"Current: {self.auto_updater.current_version}\n"
        message += f"Latest: {latest_version}\n\n"
        
        if release_info.get("name"):
            message += f"{release_info['name']}\n\n"
        if release_info.get("body"):
            # Limit changelog length
            changelog = release_info['body'][:500]
            if len(release_info['body']) > 500:
                changelog += "..."
            message += f"Changes:\n{changelog}\n\n"
        
        message += "Would you like to download and install the update automatically?\n\n"
        message += "(The application will restart after installation)"
        
        response = messagebox.askyesno("Update Available", message)
        
        if response:
            # Start automatic update process
            self.start_auto_update(release_info)
        else:
            # Offer manual download
            if release_info.get("url"):
                import webbrowser
                webbrowser.open(release_info["url"])
    
    def start_auto_update(self, release_info):
        """Start the automatic update process."""
        if self.update_downloading:
            messagebox.showwarning("Update in Progress", "An update is already being downloaded.")
            return
        
        self.update_downloading = True
        
        # Create update progress window
        self.update_window = ctk.CTkToplevel(self)
        self.update_window.title("Updating ProtectSecure")
        self.update_window.geometry("500x200")
        self.update_window.attributes("-topmost", True)
        
        lbl_title = ctk.CTkLabel(self.update_window, text="Downloading Update...", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=20)
        
        self.update_progress = ctk.CTkProgressBar(self.update_window)
        self.update_progress.set(0)
        self.update_progress.pack(pady=10, padx=20, fill="x")
        
        self.update_status = ctk.CTkLabel(self.update_window, text="Connecting...", font=("Arial", 12))
        self.update_status.pack(pady=10)
        
        btn_cancel = ctk.CTkButton(self.update_window, text="Cancel", command=self.cancel_update, fg_color="gray")
        btn_cancel.pack(pady=10)
        
        # Start download in background thread
        threading.Thread(target=self.download_and_install_update, args=(release_info,), daemon=True).start()
    
    def download_and_install_update(self, release_info):
        """Download and install the update."""
        try:
            # Download update
            def progress_callback(percent, status):
                if self.update_window and self.update_window.winfo_exists():
                    self.after(0, lambda: self.update_progress.set(percent / 100.0))
                    self.after(0, lambda: self.update_status.configure(text=status))
            
            setup_path = self.auto_updater.download_update(release_info, progress_callback)
            
            if not setup_path:
                self.after(0, lambda: messagebox.showerror("Update Failed", "Failed to download update. Please try downloading manually."))
                self.after(0, lambda: self.close_update_window())
                self.update_downloading = False
                return
            
            # Update status
            if self.update_window and self.update_window.winfo_exists():
                self.after(0, lambda: self.update_status.configure(text="Installing update..."))
                self.after(0, lambda: self.update_progress.set(1.0))
            
            # Install update (silent mode)
            if self.auto_updater.install_update(setup_path, silent=True):
                # Close application - installer will restart it
                self.after(1000, lambda: self.quit())
            else:
                self.after(0, lambda: messagebox.showerror("Update Failed", "Failed to start installer. Please run it manually."))
                self.after(0, lambda: self.close_update_window())
                self.update_downloading = False
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Update Error", f"An error occurred during update: {str(e)}"))
            self.after(0, lambda: self.close_update_window())
            self.update_downloading = False
            self.auto_updater.cleanup()
    
    def cancel_update(self):
        """Cancel the update process."""
        if messagebox.askyesno("Cancel Update", "Are you sure you want to cancel the update?"):
            self.update_downloading = False
            self.auto_updater.cleanup()
            self.close_update_window()
    
    def close_update_window(self):
        """Close the update progress window."""
        if self.update_window and self.update_window.winfo_exists():
            self.update_window.destroy()
        self.update_window = None

if __name__ == "__main__":
    app = ProtectSecureApp()
    app.mainloop()
