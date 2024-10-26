import ctypes
import os
import time
from PIL import Image

# Get the current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to your GIF
gif_path = os.path.join(script_dir, "skull spinning.gif")

# Output directory for frames
output_dir = os.path.join(script_dir, "GifFrames")
os.makedirs(output_dir, exist_ok=True)

# Load the GIF and extract frames
gif = Image.open(gif_path)
frames = []
try:
    while True:
        frame = gif.copy()
        frame_path = os.path.join(output_dir, f"frame_{len(frames)}.bmp")
        frame.save(frame_path, format="BMP")
        frames.append(frame_path)
        gif.seek(gif.tell() + 1)
except EOFError:
    pass  # End of GIF frames

# Function to change desktop background
def set_wallpaper(image_path):
    # Use ctypes to set the desktop background on Windows
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)

# Loop through frames to create the animation effect
frame_delay = 0.1  # Adjust this for speed (0.1 = 100ms per frame)
while True:
    for frame_path in frames:
        set_wallpaper(frame_path)
        time.sleep(frame_delay)
