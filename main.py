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
import sys

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
    def __init__(self, input_path, target_fps=25, quality=80, scale_factor=0.75, ram_disk_size_mb=250):
        self.input_path = input_path
        self.target_fps = target_fps
        self.frame_delay = 1.0 / target_fps
        self.quality = quality  # JPEG quality (0-100)
        self.scale_factor = scale_factor  # Scale factor for resolution
        self.ram_disk_size_mb = ram_disk_size_mb  # Size of the RAM disk in MB
        self.ram_disk_path = "R:\\"  # Default path for RAM Disk, change if needed

        # Initialize logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Create RAM disk automatically
        self.create_ram_disk()

        # Initialize frame queue
        self.frame_queue = queue.Queue(maxsize=1000)
        self.running = False

        # Create the AnimationFrames directory on RAM Disk
        self.frames_dir = os.path.join(self.ram_disk_path, "AnimationFrames")
        os.makedirs(self.frames_dir, exist_ok=True)
        self.logger.info(f"AnimationFrames directory set at {self.frames_dir}")

        # Initialize in-memory buffers
        self.buffer_count = 25  # Using 25 buffers for smoother playback
        self.temp_buffers = [BytesIO() for _ in range(self.buffer_count)]
        self.temp_image_paths = [os.path.join(self.frames_dir, f"temp_frame_{i}.jpg") for i in range(self.buffer_count)]
        self.current_buffer = 0

        # Lock for switching buffers
        self.buffer_lock = threading.Lock()

    def create_ram_disk(self):
        """Automatically create a RAM disk using ImDisk."""
        self.logger.info(f"Creating a RAM disk of size {self.ram_disk_size_mb}MB at {self.ram_disk_path}...")
        try:
            # ImDisk command to create a RAM disk
            subprocess.run(
                ["imdisk", "-a", "-s", f"{self.ram_disk_size_mb}M", "-m", self.ram_disk_path, "-p", "/fs:ntfs /q /y"],
                check=True
            )
            self.logger.info(f"RAM disk created successfully at {self.ram_disk_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create RAM disk: {e}")
            raise

    def remove_ram_disk(self):
        """Remove the RAM disk when done."""
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
        """Load preprocessed frames from the dedicated frames directory into memory"""
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

    def process_video(self):
        """Process video files by loading frames into memory as bytes and saving JPEG sequence"""
        cap = cv2.VideoCapture(self.input_path)
        frames_data = []
        new_width, new_height = self.get_optimal_monitor_resolution()

        try:
            frame_count = 0
            source_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_skip = max(1, int(source_fps / self.target_fps))

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_skip == 0:
                    frame_resized = cv2.resize(frame, (new_width, new_height),
                                               interpolation=cv2.INTER_LINEAR)
                    success, encoded_image = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
                    if not success:
                        self.logger.error(f"Failed to encode frame {frame_count}")
                        continue

                    frame_bytes = encoded_image.tobytes()
                    frames_data.append((frame_bytes, self.frame_delay))

                    # Save frame as JPEG file for archival
                    frame_path = os.path.join(self.frames_dir, f"frame_{len(frames_data) - 1}.jpg")
                    with open(frame_path, 'wb') as f:
                        f.write(frame_bytes)

                frame_count += 1
                if frame_count % 100 == 0:
                    self.logger.info(f"Processed {frame_count} frames...")

        finally:
            cap.release()

        self.logger.info(f"Total frames processed: {len(frames_data)}")
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
                self.frame_queue.put((frame_bytes, duration))
        self.logger.info("Frame producer finished.")

    def frame_consumer(self):
        """Consume frames from the queue and set them as wallpaper using in-memory buffers"""
        self.logger.info("Starting frame consumer...")
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
                    start_time = time.time()
                    self.set_wallpaper(temp_image_path)
                    end_time = time.time()
                    self.logger.info(f"Set wallpaper in {end_time - start_time:.4f} seconds")

                    # Switch to the next buffer
                    self.current_buffer = (self.current_buffer + 1) % self.buffer_count

                # Sleep for the duration of the frame
                time.sleep(duration)

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
            # Delete the temporary frame files
            for temp_path in self.temp_image_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    self.logger.info(f"Deleted temporary frame file {temp_path}")
        except Exception as e:
            self.logger.error(f"Error deleting temp files: {e}")

        # Remove the RAM disk when done
        self.remove_ram_disk()

    def run(self):
        """Main method to run the wallpaper animation"""
        self.logger.info("Initializing wallpaper animator...")

        try:
            if self.is_video_file() or Path(self.input_path).suffix.lower() in {'.gif'}:
                # Check if frames have already been processed
                existing_frame_files = sorted(Path(self.frames_dir).glob("frame_*.jpg"),
                                              key=lambda x: int(x.stem.split('_')[1]))
                if existing_frame_files:
                    self.logger.info(f"Detected existing frames in {self.frames_dir}. Loading from disk...")
                    frames_data = self.load_frames_from_directory()
                else:
                    self.logger.info("No existing frames found. Processing input file...")
                    if self.is_video_file():
                        self.logger.info("Processing video file...")
                        frames_data = self.process_video()
                    else:
                        self.logger.info("Processing GIF file...")
                        frames_data = self.process_gif()
            else:
                self.logger.error("Unsupported file format. Please provide a video or GIF file.")
                return

            if not frames_data:
                self.logger.error("No frames were processed or loaded!")
                return

            self.running = True

            # Start producer and consumer threads
            producer_thread = threading.Thread(target=self.frame_producer, args=(frames_data,), daemon=True)
            consumer_thread = threading.Thread(target=self.frame_consumer, daemon=True)

            producer_thread.start()
            consumer_thread.start()

            self.logger.info(f"Animation started with {len(frames_data)} frames. Press Ctrl+C to stop.")

            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.logger.info("\nStopping animation...")
                self.running = False
                producer_thread.join()
                consumer_thread.join()
                self.cleanup()
                self.logger.info("Animation stopped successfully")

        except Exception as e:
            self.logger.error(f"Error during animation: {e}")
            self.running = False
            self.cleanup()

if __name__ == "__main__":
    input_file = "cellBball.mp4"  # or "skull spinning.gif"
    animator = EnhancedWallpaperAnimator(
        input_file,
        target_fps=25,          # Adjusted to 25 FPS based on your requirements
        quality=80,             # Lower = smaller files (range 0-100)
        scale_factor=0.75,      # Lower = smaller resolution
        ram_disk_size_mb=250     # Adjust the size of the RAM disk in MB
    )
    animator.run()
