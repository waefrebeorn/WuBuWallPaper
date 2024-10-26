# Enhanced Wallpaper Animator

A high-performance Python application that turns videos and GIFs into animated desktop wallpapers for Windows. Supports both video files and GIF animations with optimized frame rates and resolution scaling.

## Features

- Support for multiple video formats (MP4, AVI, MKV, MOV, WMV)
- GIF animation support with frame timing preservation
- Automatic resolution scaling to match monitor dimensions
- Multi-threaded frame processing for smooth playback
- Configurable frame rates (up to 120 FPS)
- Automatic aspect ratio maintenance
- Resource cleanup on exit
- Progress logging
- Error handling and recovery

## Requirements

```bash
pip install -r requirements.txt
```

Required packages:
- opencv-python
- numpy
- Pillow
- screeninfo

## Usage

Basic usage:

```python
from wallpaper_animator import EnhancedWallpaperAnimator

# For video files
animator = EnhancedWallpaperAnimator("your_video.mp4", target_fps=60)
animator.run()

# For GIF files
animator = EnhancedWallpaperAnimator("your_animation.gif", target_fps=30)
animator.run()
```

Running from command line:

```bash
python wallpaper_animator.py
```

## Performance Tuning

You can adjust several parameters to optimize performance for your system:

1. Frame Rate:
```python
# Higher FPS for smoother animation
animator = EnhancedWallpaperAnimator("video.mp4", target_fps=60)

# Lower FPS for better performance
animator = EnhancedWallpaperAnimator("video.mp4", target_fps=30)
```

2. Frame Queue Size:
```python
# Modify the frame_queue maxsize in __init__
self.frame_queue = queue.Queue(maxsize=30)  # Adjust based on available memory
```

## Supported File Types

Video Formats:
- .mp4
- .avi
- .mkv
- .mov
- .wmv

Image Formats:
- .gif

## How It Works

The animator uses a producer-consumer pattern with two threads:

1. Producer Thread:
   - Reads and processes frames from the source file
   - Scales frames to match monitor resolution
   - Queues frames for display

2. Consumer Thread:
   - Retrieves frames from the queue
   - Sets the desktop wallpaper
   - Maintains frame timing

## Error Handling

The application includes comprehensive error handling:
- Graceful exit on Ctrl+C
- Automatic cleanup of temporary files
- Logging of errors and progress
- Recovery from frame processing errors

## Example Code

```python
from wallpaper_animator import EnhancedWallpaperAnimator

def main():
    # Initialize animator with a video file
    animator = EnhancedWallpaperAnimator(
        input_path="example.mp4",
        target_fps=60
    )
    
    # Start the animation
    animator.run()

if __name__ == "__main__":
    main()
```

## Limitations

- Windows only
- May require admin privileges for wallpaper setting
- Performance depends on system capabilities
- Large files may require significant memory

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - Feel free to use this code in your own projects.