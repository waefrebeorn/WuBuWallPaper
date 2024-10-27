
# WuBuWallPaper

![WuBuWallPaper Banner](https://github.com/waefrebeorn/WuBuWallPaper/blob/master/skullspinning.gif) 

**WuBuWallPaper** is a dynamic desktop wallpaper animator for Windows that brings your favorite videos and GIFs to life as your desktop background. Leveraging frame skipping and RAM disk technology, WuBuWallPaper ensures smooth and efficient playback, providing a visually stunning and customizable desktop experience.

---

## 🛠️ Features

- **Frame Skipping Toggle:** Enable or disable frame skipping to balance performance and visual quality.
- **Automatic RAM Disk Management:** Utilizes a RAM disk for rapid frame access, enhancing playback speed.
- **High Customizability:** Adjust target FPS, JPEG quality, resolution scaling, and RAM disk size.
- **Auto-Restart Mechanism:** Seamlessly restarts the animation upon interruptions, ensuring continuous playback.
- **Supports Multiple Formats:** Compatible with various video formats (`.mp4`, `.avi`, `.mkv`, etc.) and GIFs (`.gif`).
- **Optimized Performance:** Resizes frames based on monitor resolution and scale factor for optimal display.
- **Comprehensive Logging:** Detailed logs for monitoring performance and troubleshooting.

---

## 📦 Installation

### 1. **Clone the Repository**

```bash
git clone https://github.com/waefrebeorn/WuBuWallPaper.git
cd WuBuWallPaper
```

### 2. **Install Python Dependencies**

Ensure you have **Python 3.6+** installed. Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

**`requirements.txt`:**

```plaintext
opencv-python
numpy
Pillow
screeninfo
```

### 3. **Install ImDisk**

**ImDisk** is essential for creating and managing RAM disks on Windows.

1. **Download ImDisk:**
   - Visit the [ImDisk Toolkit Download Page](http://www.ltr-data.se/opencode.html/#ImDisk) and download the latest version.

2. **Install ImDisk:**
   - Run the installer and follow the on-screen instructions to complete the installation.

> **Note:** Ensure you have administrative privileges during installation, as creating RAM disks requires elevated permissions.

---

## ⚙️ Usage

You can run the script directly by double-clicking the `WuBuWallPaper.py` file or via the command line.

### **Basic Execution**

Simply double-click the `WuBuWallPaper.py` file or run:

```bash
python WuBuWallPaper.py
```

This will use the default input file `badapple.mp4` located in the script's directory.

### **Command-Line Arguments**

The script offers various command-line options to customize its behavior:

| Argument          | Description                                                        | Default          |
|-------------------|--------------------------------------------------------------------|------------------|
| `input_file`      | Path to the input video or GIF file (e.g., `badapple.mp4`).        | `badapple.mp4`   |
| `--fps`           | Target frames per second for wallpaper animation.                  | `15`             |
| `--quality`       | JPEG quality for frame encoding (0-100).                           | `80`              |
| `--scale`         | Scale factor for resolution (e.g., `0.75` for 75% of original).    | `0.75`           |
| `--ram`           | RAM disk size in MB.                                               | `512`             |
| `--skip` / `--no-skip` | Enable (`--skip`) or disable (`--no-skip`) frame skipping.    | `--skip` (enabled) |

### **Examples**

1. **Run with Default Settings:**

   ```bash
   python WuBuWallPaper.py
   ```

2. **Specify a Different Input File:**

   ```bash
   python WuBuWallPaper.py path_to_your_video.mp4
   ```

3. **Disable Frame Skipping:**

   ```bash
   python WuBuWallPaper.py path_to_your_video.mp4 --no-skip
   ```

4. **Customize All Parameters:**

   ```bash
   python WuBuWallPaper.py path_to_your_video.mp4 --fps 20 --quality 90 --scale 0.8 --ram 1024
   ```

### **Stopping the Animation**

- **Restart Animation:** Press `Ctrl+C` once in the terminal to interrupt and automatically restart the animation.
- **Completely Stop the Script:** Press `Ctrl+C` twice quickly or close the terminal window. If the RAM disk was created by the script, it will be removed upon complete termination.

---

## 📈 Performance Optimization

- **RAM Disk Usage:** Ensure sufficient RAM is allocated for the RAM disk to store all frames. Adjust the `--ram` parameter based on your system's available memory.
- **Resolution Scaling:** Use the `--scale` parameter to reduce the resolution of frames, which can enhance performance on lower-end systems.
- **Frame Skipping:** Enable frame skipping (`--skip`) to maintain a consistent target FPS, especially useful for high-FPS source videos.

---

## 🐞 Troubleshooting

### **1. RAM Disk Not Creating**

- **Issue:** The script attempts to create a RAM disk but fails or conflicts with existing drive letters.
- **Solution:**
  - Ensure **ImDisk** is installed correctly.
  - Verify that the drive letter `R:\` is available or specify a different one by modifying the `self.ram_disk_path` variable in the script or adding a command-line argument for drive letter customization.

### **2. Wallpaper Not Updating**

- **Issue:** Frames are processed, but the wallpaper does not change.
- **Solution:**
  - Ensure the script is running with **administrative privileges**.
  - Verify that the frames are correctly saved in the RAM disk and accessible.
  - Check the logs for any errors related to `SystemParametersInfoW`.

### **3. High CPU Usage**

- **Issue:** The script consumes excessive CPU resources.
- **Solution:**
  - Reduce the target FPS using the `--fps` parameter.
  - Enable frame skipping to lower the number of frames processed per second.
  - Lower the JPEG quality with the `--quality` parameter to reduce encoding overhead.

### **4. Frame Queue Full Warning**

- **Issue:** Logs indicate that the frame queue is full, leading to skipped frames.
- **Solution:**
  - Increase the RAM disk size using the `--ram` parameter to allow more frames to be loaded.
  - Optimize the script's performance by reducing resolution or FPS.

---

## 📝 Configuration

You can modify the script's default settings by editing the `main()` function or by passing command-line arguments as shown in the **Usage** section.

### **Custom RAM Disk Path**

If you prefer a different drive letter for the RAM disk, modify the `self.ram_disk_path` variable in the `__init__` method of the `EnhancedWallpaperAnimator` class or extend the script to accept a command-line argument for the RAM disk path.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**
2. **Create a New Branch**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add Your Feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Open a Pull Request**

Please ensure your code adheres to the project's coding standards and includes appropriate tests where necessary.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 📞 Contact

For any questions or support, please open an issue on the [GitHub repository](https://github.com/waefrebeorn/WuBuWallPaper/issues) or contact [eman56447@gmail.com](mailto:eman56447@gmail.com).

---

## 🌟 Acknowledgements

- [ImDisk Toolkit](http://www.ltr-data.se/opencode.html/#ImDisk) for RAM disk management.
- [OpenCV](https://opencv.org/) for video processing.
- [Pillow](https://python-pillow.org/) for image handling.
- [Screeninfo](https://pypi.org/project/screeninfo/) for monitor information.
- [GitHub](https://github.com/) for version control and collaboration.

---

> **Disclaimer:** This script modifies system wallpaper settings and creates RAM disks. Use it responsibly and ensure that you have backups of your important data. The author is not liable for any damage or data loss resulting from the use of this script.
```

---

