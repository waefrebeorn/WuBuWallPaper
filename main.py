import ctypes
import os
import time
import cv2
import numpy as np
from PIL import Image
from screeninfo import get_monitors
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
from pathlib import Path
import logging

class EnhancedWallpaperAnimator:
    def __init__(self, input_path, target_fps=30):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_path = input_path
        self.output_dir = os.path.join(self.script_dir, "AnimationFrames")
        self.frame_queue = queue.Queue(maxsize=30)  # Increased buffer for smoother playback
        self.running = False
        self.target_fps = target_fps
        self.frame_delay = 1.0 / target_fps
        
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        os.makedirs(self.output_dir, exist_ok=True)

    def get_optimal_monitor_resolution(self):
        """Get the optimal resolution while maintaining aspect ratio"""
        monitors = get_monitors()
        max_width = max(monitor.width for monitor in monitors)
        max_height = max(monitor.height for monitor in monitors)
        
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

        return new_width, new_height

    def is_video_file(self):
        """Check if the input file is a video format"""
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv'}
        return Path(self.input_path).suffix.lower() in video_extensions

    def process_video(self):
        """Process video files (MP4, etc.)"""
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
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_resized = cv2.resize(frame_rgb, (new_width, new_height), 
                                            interpolation=cv2.INTER_LINEAR)
                    
                    pil_image = Image.fromarray(frame_resized)
                    frame_path = os.path.join(self.output_dir, f"frame_{len(frames_data)}.bmp")
                    pil_image.save(frame_path, format="BMP", optimize=True)
                    frames_data.append((frame_path, self.frame_delay))
                
                frame_count += 1
                if frame_count % 100 == 0:
                    self.logger.info(f"Processed {frame_count} frames...")
        
        finally:
            cap.release()
        
        return frames_data

    def process_gif(self):
        """Process GIF files with optimization"""
        frames_data = []
        new_width, new_height = self.get_optimal_monitor_resolution()
        
        with Image.open(self.input_path) as gif:
            frame_count = 0
            while True:
                try:
                    duration = gif.info.get('duration', 100) / 1000.0
                    
                    frame = gif.copy()
                    frame = frame.resize((new_width, new_height), Image.BICUBIC)
                    
                    if frame.mode != 'RGB':
                        frame = frame.convert('RGB')
                    
                    frame_path = os.path.join(self.output_dir, f"frame_{frame_count}.bmp")
                    frame.save(frame_path, format="BMP", optimize=True)
                    frames_data.append((frame_path, duration))
                    
                    frame_count += 1
                    gif.seek(gif.tell() + 1)
                    
                    if frame_count % 10 == 0:
                        self.logger.info(f"Processed {frame_count} frames...")
                
                except EOFError:
                    break
        
        return frames_data

    @staticmethod
    def set_wallpaper(image_path):
        """Optimized wallpaper setting"""
        # Simple, fast wallpaper setting without extra flags
        SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 0)
        return True

    def frame_producer(self, frames_data):
        """Optimized frame producer"""
        while self.running:
            for frame_path, duration in frames_data:
                if not self.running:
                    break
                self.frame_queue.put((frame_path, duration))
                # Removed timeout and sleep to increase speed

    def frame_consumer(self):
        """Optimized frame consumer"""
        while self.running:
            try:
                frame_path, duration = self.frame_queue.get_nowait()
                self.set_wallpaper(frame_path)
                time.sleep(max(0, duration))  # Simplified timing
                self.frame_queue.task_done()
            except queue.Empty:
                time.sleep(0.001)  # Minimal sleep to prevent CPU thrashing
            except Exception as e:
                self.logger.error(f"Error in frame consumer: {e}")

    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up resources...")
        try:
            # Clean up frame files
            for file in Path(self.output_dir).glob("frame_*.bmp"):
                try:
                    file.unlink()
                except Exception as e:
                    self.logger.error(f"Error deleting file {file}: {e}")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Main method to run the wallpaper animation"""
        self.logger.info("Initializing wallpaper animator...")
        
        try:
            if self.is_video_file():
                self.logger.info("Processing video file...")
                frames_data = self.process_video()
            else:
                self.logger.info("Processing GIF file...")
                frames_data = self.process_gif()
            
            if not frames_data:
                self.logger.error("No frames were processed!")
                return
            
            self.running = True
            
            # Create and start threads
            producer_thread = threading.Thread(target=self.frame_producer, args=(frames_data,))
            consumer_thread = threading.Thread(target=self.frame_consumer)
            
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
    input_file = "skeleton.mp4"  # or "skull spinning.gif"
    animator = EnhancedWallpaperAnimator(input_file, target_fps=10)  # Increased target FPS
    animator.run()