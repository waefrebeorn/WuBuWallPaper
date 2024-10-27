import ctypes
import os
import time
import cv2
import numpy as np
from PIL import Image
from screeninfo import get_monitors
import threading
import queue
from pathlib import Path
import logging
import tempfile
from io import BytesIO

class EnhancedWallpaperAnimator:
    def __init__(self, input_path, target_fps=30, quality=80, scale_factor=0.75):
        self.input_path = input_path
        self.target_fps = target_fps
        self.frame_delay = 1.0 / target_fps
        self.quality = quality  # JPEG quality (0-100)
        self.scale_factor = scale_factor  # Scale factor for resolution

        # Initialize logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Initialize frame queue
        self.frame_queue = queue.Queue(maxsize=1000)  # Adjusted maxsize for memory management
        self.running = False

        # Create the AnimationFrames directory
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.animation_frames_dir = os.path.join(self.script_dir, "AnimationFrames")
        os.makedirs(self.animation_frames_dir, exist_ok=True)
        self.logger.info(f"AnimationFrames directory set at {self.animation_frames_dir}")

        # Create a dedicated frames directory based on the input file name
        self.input_filename = Path(self.input_path).stem  # e.g., "cellBball" from "cellBball.mp4"
        self.input_extension = Path(self.input_path).suffix  # e.g., ".mp4"
        self.frames_dir = os.path.join(self.animation_frames_dir, f"{self.input_filename}{self.input_extension}")
        os.makedirs(self.frames_dir, exist_ok=True)
        self.logger.info(f"Dedicated frames directory set at {self.frames_dir}")

        # Initialize double-buffering temp files
        self.temp_frame_paths = [
            os.path.join(self.frames_dir, "temp_frame1.jpg"),
            os.path.join(self.frames_dir, "temp_frame2.jpg")
        ]
        for temp_path in self.temp_frame_paths:
            with open(temp_path, 'wb') as f:
                pass  # Create empty temp files
            self.logger.info(f"Temporary frame file created at {temp_path}")

        self.current_temp = 0  # Index to track which temp file to use

        # Lock for switching temp files
        self.temp_lock = threading.Lock()

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
                # Assuming uniform frame_delay; you can modify if durations vary
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
                    # Resize frame
                    frame_resized = cv2.resize(frame, (new_width, new_height),
                                               interpolation=cv2.INTER_LINEAR)

                    # Encode frame to JPEG bytes
                    success, encoded_image = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
                    if not success:
                        self.logger.error(f"Failed to encode frame {frame_count}")
                        continue

                    frame_bytes = encoded_image.tobytes()
                    frames_data.append((frame_bytes, self.frame_delay))

                    # Save frame as JPEG file for archival
                    frame_path = os.path.join(self.frames_dir, f"frame_{len(frames_data)-1}.jpg")
                    with open(frame_path, 'wb') as f:
                        f.write(frame_bytes)

                frame_count += 1
                if frame_count % 100 == 0:
                    self.logger.info(f"Processed {frame_count} frames...")

        finally:
            cap.release()

        self.logger.info(f"Total frames processed: {len(frames_data)}")
        return frames_data

    def process_gif(self):
        """Process GIF files by loading frames into memory as bytes and saving JPEG sequence"""
        frames_data = []
        new_width, new_height = self.get_optimal_monitor_resolution()

        with Image.open(self.input_path) as gif:
            frame_count = 0
            while True:
                try:
                    duration = gif.info.get('duration', 100) / 1000.0  # Convert ms to seconds

                    frame = gif.copy()
                    frame = frame.resize((new_width, new_height), Image.LANCZOS)

                    if frame.mode != 'RGB':
                        frame = frame.convert('RGB')

                    # Save frame to BytesIO as JPEG
                    byte_io = BytesIO()
                    frame.save(byte_io, format='JPEG', quality=self.quality, optimize=True)
                    frame_bytes = byte_io.getvalue()

                    frames_data.append((frame_bytes, duration))

                    # Save frame as JPEG file for archival
                    frame_path = os.path.join(self.frames_dir, f"frame_{frame_count}.jpg")
                    with open(frame_path, 'wb') as f:
                        f.write(frame_bytes)

                    frame_count += 1
                    if frame_count % 10 == 0:
                        self.logger.info(f"Processed {frame_count} frames...")

                    gif.seek(gif.tell() + 1)

                except EOFError:
                    break

        self.logger.info(f"Total frames processed: {len(frames_data)}")
        return frames_data

    def set_wallpaper(self, image_path):
        """Set wallpaper using the provided image path"""
        SPI_SETDESKWALLPAPER = 20
        # SPIF_SENDWININICHANGE = 2 for potentially faster updates without writing to user profile
        success = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 2)
        if not success:
            self.logger.error("Failed to set wallpaper.")
        return success

    def frame_producer(self, frames_data):
        """Load frames into the queue from memory"""
        self.logger.info("Starting frame producer...")
        for frame_bytes, duration in frames_data:
            if not self.running:
                break
            self.frame_queue.put((frame_bytes, duration))
        self.logger.info("Frame producer finished.")

    def frame_consumer(self):
        """Consume frames from the queue and set them as wallpaper using double-buffering"""
        self.logger.info("Starting frame consumer...")
        while self.running:
            try:
                frame_bytes, duration = self.frame_queue.get(timeout=1)

                with self.temp_lock:
                    temp_path = self.temp_frame_paths[self.current_temp]

                    # Write frame bytes to the temporary file
                    with open(temp_path, 'wb') as f:
                        f.write(frame_bytes)

                    # Set the wallpaper to the temporary file
                    start_time = time.time()
                    self.set_wallpaper(temp_path)
                    end_time = time.time()
                    self.logger.info(f"Set wallpaper in {end_time - start_time:.4f} seconds")

                    # Switch to the other temp file for next frame
                    self.current_temp = 1 - self.current_temp

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
            for temp_path in self.temp_frame_paths:
                Path(temp_path).unlink(missing_ok=True)
                self.logger.info(f"Deleted temporary frame file {temp_path}")
        except Exception as e:
            self.logger.error(f"Error deleting temp files: {e}")

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
                while producer_thread.is_alive() or not self.frame_queue.empty():
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
        target_fps=30,          # Adjust based on your needs
        quality=50,             # Lower = smaller files (range 0-100)
        scale_factor=0.50       # Lower = smaller resolution
    )
    animator.run()
