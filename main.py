import ctypes
import os
import subprocess
import time
import cv2
import numpy as np
from PIL import Image
from screeninfo import get_monitors
import threading
import queue
from pathlib import Path
import logging
from io import BytesIO
import shutil
import sys
import argparse

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("Script is not running with elevated privileges. Restarting with elevation...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()
        
class EnhancedWallpaperAnimator:
    def __init__(self, input_path, target_fps=15, quality=80, scale_factor=0.75, ram_disk_size_mb=512, enable_frame_skipping=True):
        self.input_path = input_path
        self.target_fps = target_fps
        self.frame_delay = 1.0 / target_fps
        self.quality = quality  # JPEG quality (0-100)
        self.scale_factor = scale_factor  # Scale factor for resolution
        self.ram_disk_size_mb = ram_disk_size_mb  # Size of the RAM disk in MB
        self.ram_disk_path = "R:\\"  # Default path for RAM Disk, change if needed
        self.enable_frame_skipping = enable_frame_skipping  # Toggle for frame skipping

        # Initialize logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Log the frame skipping status
        if self.enable_frame_skipping:
            self.logger.info("Frame skipping is ENABLED.")
        else:
            self.logger.info("Frame skipping is DISABLED.")

        # Flag to track if RAM disk was created by the script
        self.created_ram_disk = False

        # Create RAM disk if it doesn't exist
        self.create_ram_disk()

        # Initialize frame queue
        self.frame_queue = queue.Queue(maxsize=1000)
        self.running = False

        # Create the AnimationFrames directory
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.animation_frames_dir = os.path.join(self.script_dir, "AnimationFrames")
        os.makedirs(self.animation_frames_dir, exist_ok=True)

        # Set up directories based on input file name
        self.input_filename = Path(self.input_path).stem.replace(".", "_")
        self.input_extension = Path(self.input_path).suffix.lower().strip('.')
        self.archive_dir = os.path.join(self.animation_frames_dir, f"{self.input_filename}_{self.input_extension}")
        os.makedirs(self.archive_dir, exist_ok=True)
        self.logger.info(f"Archive directory set at {self.archive_dir}")

        # Initialize in-memory buffers
        self.buffer_count = 25
        self.temp_buffers = [BytesIO() for _ in range(self.buffer_count)]
        self.temp_image_paths = [os.path.join(self.ram_disk_path, f"temp_frame_{i}.jpg") for i in range(self.buffer_count)]
        self.current_buffer = 0

        # Lock for switching buffers
        self.buffer_lock = threading.Lock()

    def create_ram_disk(self):
        """Automatically create a RAM disk using ImDisk if it doesn't exist."""
        if os.path.exists(self.ram_disk_path) and os.path.isdir(self.ram_disk_path):
            self.logger.info(f"RAM disk at {self.ram_disk_path} already exists. Skipping creation.")
            self.created_ram_disk = False
        else:
            self.logger.info(f"Creating a RAM disk of size {self.ram_disk_size_mb}MB at {self.ram_disk_path}...")
            try:
                # ImDisk command to create a RAM disk
                subprocess.run(
                    ["imdisk", "-a", "-s", f"{self.ram_disk_size_mb}M", "-m", self.ram_disk_path, "-p", "/fs:ntfs /q /y"],
                    check=True
                )
                self.logger.info(f"RAM disk created successfully at {self.ram_disk_path}")
                self.created_ram_disk = True
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to create RAM disk: {e}")
                raise

    def remove_ram_disk(self):
        """Remove the RAM disk when done, only if it was created by the script."""
        if self.created_ram_disk:
            self.logger.info(f"Removing RAM disk at {self.ram_disk_path}...")
            try:
                # ImDisk command to remove the RAM disk
                subprocess.run(
                    ["imdisk", "-D", "-m", self.ram_disk_path],
                    check=True
                )
                self.logger.info("RAM disk removed successfully.")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to remove RAM disk: {e}")
        else:
            self.logger.info(f"RAM disk at {self.ram_disk_path} was not created by the script. Skipping removal.")

    def get_optimal_monitor_resolution(self):
        """Get the optimal resolution while maintaining aspect ratio"""
        monitors = get_monitors()
        max_width = max(monitor.width for monitor in monitors)
        max_height = max(monitor.height for monitor in monitors)

        # Apply scale factor to reduce resolution
        max_width = int(max_width * self.scale_factor)
        max_height = int(max_height * self.scale_factor)

        if self.is_video_file():
            cap = cv2.VideoCapture(self.input_path)
            orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
        else:
            with Image.open(self.input_path) as img:
                orig_width, orig_height = img.size

        aspect_ratio = orig_width / orig_height

        if max_width / aspect_ratio <= max_height:
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(max_height * aspect_ratio)

        self.logger.info(f"Optimal resolution: {new_width}x{new_height}")
        return new_width, new_height

    def is_video_file(self):
        """Check if the input file is a video format"""
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv'}
        return Path(self.input_path).suffix.lower() in video_extensions
            
    def load_frames_from_directory(self):
        """Load preprocessed frames from the RAM disk into memory"""
        frames_data = []
        frame_files = sorted(Path(self.frames_dir).glob("frame_*.jpg"),
                             key=lambda x: int(x.stem.split('_')[1]))  # Sort by frame number

        if not frame_files:
            self.logger.warning(f"No frame files found in {self.frames_dir}")
            return frames_data

        for frame_file in frame_files:
            try:
                with open(frame_file, 'rb') as f:
                    frame_bytes = f.read()
                frames_data.append((frame_bytes, self.frame_delay))
            except Exception as e:
                self.logger.error(f"Failed to load frame {frame_file}: {e}")

        self.logger.info(f"Loaded {len(frames_data)} frames from {self.frames_dir}")
        return frames_data
            
    def load_frames_from_archive(self):
        """Copy archived frames into RAM disk for faster access"""
        self.logger.info(f"Copying frames from {self.archive_dir} to RAM disk at {self.frames_dir}...")
        try:
            shutil.copytree(self.archive_dir, self.frames_dir, dirs_exist_ok=True)
            self.logger.info("Frames successfully loaded into RAM disk.")
        except Exception as e:
            self.logger.error(f"Failed to load frames into RAM disk: {e}")
            raise

    def process_video(self):
        """Process video files with or without frame skipping to maintain target FPS"""
        cap = cv2.VideoCapture(self.input_path)
        frames_data = []
        new_width, new_height = self.get_optimal_monitor_resolution()
        
        # Get source video properties
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if self.enable_frame_skipping:
            # Calculate frame skip based on source and target FPS
            frame_skip = max(1, round(source_fps / self.target_fps))
            actual_fps = source_fps / frame_skip
            frame_duration = 1.0 / self.target_fps  # Maintain consistent playback speed
            
            self.logger.info(f"Source FPS: {source_fps:.2f}, Target FPS: {self.target_fps}")
            self.logger.info(f"Frame skip: {frame_skip}, Actual FPS: {actual_fps:.2f}")
        else:
            # No frame skipping; adjust frame duration based on target FPS
            frame_duration = 1.0 / self.target_fps  # Maintain consistent playback speed
            self.logger.info(f"Processing all frames without frame skipping. Target FPS: {self.target_fps}")

        frame_count = 0
        saved_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if self.enable_frame_skipping:
                    if frame_count % frame_skip == 0:
                        self._process_and_save_frame(frame, new_width, new_height, frames_data, saved_count)
                        saved_count += 1
                else:
                    self._process_and_save_frame(frame, new_width, new_height, frames_data, saved_count)
                    saved_count += 1
                
                frame_count += 1
                
                if self.enable_frame_skipping and saved_count % 100 == 0:
                    self.logger.info(f"Processed {saved_count} frames...")
                elif not self.enable_frame_skipping and saved_count % 100 == 0:
                    self.logger.info(f"Processed {saved_count} frames...")
                    
        finally:
            cap.release()
            
        self.logger.info(f"Processed {saved_count} frames from {total_frames} source frames")
        return frames_data

    def _process_and_save_frame(self, frame, new_width, new_height, frames_data, saved_count):
        """Helper method to resize, encode, and save a single frame"""
        try:
            frame_resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            success, encoded_image = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            
            if success:
                frame_bytes = encoded_image.tobytes()
                frames_data.append((frame_bytes, self.frame_delay))
                
                # Save frame for archival
                frame_path = os.path.join(self.archive_dir, f"frame_{saved_count}.jpg")
                with open(frame_path, 'wb') as f:
                    f.write(frame_bytes)
        except Exception as e:
            self.logger.error(f"Error processing frame {saved_count}: {e}")

    def process_gif(self):
        """Process GIF files with or without frame skipping to maintain target FPS"""
        frames_data = []
        new_width, new_height = self.get_optimal_monitor_resolution()
        
        with Image.open(self.input_path) as img:
            # Get total number of frames and calculate frame skip
            n_frames = getattr(img, 'n_frames', 1)
            frame_durations = []
            
            # First pass: get frame durations
            for frame_idx in range(n_frames):
                img.seek(frame_idx)
                frame_duration = img.info.get('duration', 100)  # Default to 100ms if not specified
                frame_durations.append(frame_duration / 1000.0)  # Convert to seconds
            
            if self.enable_frame_skipping:
                # Calculate effective source FPS
                avg_frame_duration = sum(frame_durations) / len(frame_durations) if frame_durations else 0.1
                source_fps = 1.0 / avg_frame_duration if avg_frame_duration > 0 else self.target_fps
                
                # Calculate frame skip
                frame_skip = max(1, round(source_fps / self.target_fps))
                frame_duration = 1.0 / self.target_fps  # Maintain consistent playback speed
                
                self.logger.info(f"GIF Source FPS: {source_fps:.2f}, Target FPS: {self.target_fps}")
                self.logger.info(f"Frame skip: {frame_skip}, Total frames: {n_frames}")
            else:
                # No frame skipping; adjust frame duration based on target FPS
                frame_duration = 1.0 / self.target_fps  # Maintain consistent playback speed
                self.logger.info(f"Processing all GIF frames without frame skipping. Target FPS: {self.target_fps}")
            
            frame_count = 0
            saved_count = 0
            
            try:
                for frame_idx in range(n_frames):
                    if self.enable_frame_skipping and (frame_idx % frame_skip != 0):
                        continue
                    img.seek(frame_idx)
                    frame = img.convert('RGB')
                    frame_resized = frame.resize((new_width, new_height), Image.LANCZOS)
                    
                    with BytesIO() as buffer:
                        frame_resized.save(buffer, format='JPEG', quality=self.quality)
                        frame_bytes = buffer.getvalue()
                    
                    frames_data.append((frame_bytes, frame_duration))
                    
                    # Save frame for archival
                    frame_path = os.path.join(self.archive_dir, f"frame_{saved_count}.jpg")
                    with open(frame_path, 'wb') as f:
                        f.write(frame_bytes)
                    saved_count += 1
                    
                    if saved_count % 100 == 0:
                        self.logger.info(f"Processed {saved_count} frames...")
                    
                    frame_count += 1
                    
            except EOFError:
                pass
            
        self.logger.info(f"Processed {saved_count} frames from {n_frames} source frames")
        return frames_data

    def set_wallpaper(self, image_path):
        """Set wallpaper using the provided image path"""
        SPI_SETDESKWALLPAPER = 20
        success = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 2)
        if not success:
            self.logger.error("Failed to set wallpaper.")
        return success

    def frame_producer(self, frames_data):
        """Load frames into the queue from memory and loop indefinitely"""
        self.logger.info("Starting frame producer...")
        while self.running:
            for frame_bytes, duration in frames_data:
                if not self.running:
                    break
                try:
                    self.frame_queue.put((frame_bytes, duration), timeout=1)
                except queue.Full:
                    self.logger.warning("Frame queue is full. Skipping frame.")
        self.logger.info("Frame producer finished.")

    def frame_consumer(self):
        """Consume frames from the queue and set them as wallpaper using in-memory buffers"""
        self.logger.info("Starting frame consumer...")
        next_frame_time = time.perf_counter()
        while self.running:
            try:
                frame_bytes, duration = self.frame_queue.get(timeout=1)

                with self.buffer_lock:
                    buffer = self.temp_buffers[self.current_buffer]
                    buffer.seek(0)
                    buffer.truncate()
                    buffer.write(frame_bytes)
                    buffer.seek(0)

                    # Write buffer to the corresponding temporary file on RAM Disk
                    temp_image_path = self.temp_image_paths[self.current_buffer]
                    with open(temp_image_path, 'wb') as temp_image:
                        temp_image.write(buffer.getvalue())

                    # Set the wallpaper to the temporary file
                    start_time = time.perf_counter()
                    self.set_wallpaper(temp_image_path)
                    end_time = time.perf_counter()
                    self.logger.debug(f"Set wallpaper in {end_time - start_time:.4f} seconds")

                    # Switch to the next buffer
                    self.current_buffer = (self.current_buffer + 1) % self.buffer_count

                # Calculate the next frame time
                next_frame_time += duration
                sleep_duration = next_frame_time - time.perf_counter()
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                else:
                    self.logger.warning("Frame processing is lagging behind.")

                self.frame_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in frame consumer: {e}")

        self.logger.info("Frame consumer finished.")

    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up resources...")
        try:
            # Delete the temporary frame files from the RAM disk
            for temp_path in self.temp_image_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    self.logger.debug(f"Deleted temporary frame file {temp_path}")
        except Exception as e:
            self.logger.error(f"Error deleting temp files: {e}")

        # Remove the RAM disk only if it was created by the script
        self.remove_ram_disk()

    def run_animation(self):
        """Run the wallpaper animation"""
        self.logger.info("Initializing wallpaper animator...")

        try:
            # Create RAM disk frame directory if not exists
            self.frames_dir = os.path.join(self.ram_disk_path, f"{self.input_filename}_{self.input_extension}")
            os.makedirs(self.frames_dir, exist_ok=True)

            # Load frames if already archived, otherwise process them
            existing_frame_files = sorted(Path(self.archive_dir).glob("frame_*.jpg"),
                                          key=lambda x: int(x.stem.split('_')[1]))
            if existing_frame_files:
                self.logger.info("Loading frames from archive...")
                self.load_frames_from_archive()
                frames_data = self.load_frames_from_directory()
            else:
                self.logger.info("No existing frames found. Processing input file...")
                if self.is_video_file():
                    frames_data = self.process_video()
                else:
                    frames_data = self.process_gif()

            if not frames_data:
                self.logger.error("No frames were processed or loaded!")
                return

            self.running = True

            # Start producer and consumer threads
            producer_thread = threading.Thread(target=self.frame_producer, args=(frames_data,), daemon=True)
            consumer_thread = threading.Thread(target=self.frame_consumer, daemon=True)

            producer_thread.start()
            consumer_thread.start()

            self.logger.info(f"Animation started with {len(frames_data)} frames. Press Ctrl+C to restart.")

            while self.running:
                time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error during animation: {e}")
            self.running = False
            self.cleanup()

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Enhanced Wallpaper Animator")
    parser.add_argument('input_file', nargs='?', type=str, default="badapple.mp4",
                        help='Path to the input video or GIF file (e.g., badapple.mp4 or skull_spinning.gif). Defaults to "badapple.mp4" if not provided.')
    parser.add_argument('--fps', type=int, default=15, help='Target frames per second for wallpaper animation (default: 15)')
    parser.add_argument('--quality', type=int, default=80, help='JPEG quality (0-100, default: 80)')
    parser.add_argument('--scale', type=float, default=0.75, help='Scale factor for resolution (default: 0.75)')
    parser.add_argument('--ram', type=int, default=512, help='RAM disk size in MB (default: 512)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--skip', action='store_true', help='Enable frame skipping (default)')
    group.add_argument('--no-skip', dest='skip', action='store_false', help='Disable frame skipping')
    parser.set_defaults(skip=True)
    
    args = parser.parse_args()
    
    animator = EnhancedWallpaperAnimator(
        input_path=args.input_file,
        target_fps=args.fps,
        quality=args.quality,
        scale_factor=args.scale,
        ram_disk_size_mb=args.ram,
        enable_frame_skipping=args.skip
    )
    
    while True:
        try:
            animator.run_animation()
        except KeyboardInterrupt:
            animator.logger.info("\nAnimation interrupted. Restarting...")
            animator.running = False
            animator.cleanup()
            time.sleep(1)  # Short pause before restarting
            animator = EnhancedWallpaperAnimator(
                input_path=args.input_file,
                target_fps=args.fps,
                quality=args.quality,
                scale_factor=args.scale,
                ram_disk_size_mb=args.ram,
                enable_frame_skipping=args.skip
            )
            continue
        except Exception as e:
            animator.logger.error(f"Unexpected error: {e}")
            animator.cleanup()
            sys.exit(1)

if __name__ == "__main__":
    main()
