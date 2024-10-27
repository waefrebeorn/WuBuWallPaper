@echo off
echo Setting up environment and installing dependencies...

REM Create a virtual environment if it doesn't already exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Create a requirements.txt file if it does not exist
echo pillow > requirements.txt
echo screeninfo >> requirements.txt
echo opencv-python >> requirements.txt
echo pywin32 >> requirements.txt

REM Install other necessary libraries
pip install -r requirements.txt

REM Check for ImDisk installation
echo Checking for ImDisk installation...
where imdisk >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ImDisk not found. Downloading and installing ImDisk...
    
    REM Direct download URL for ImDisk
    set IMDISK_URL=https://static.ltr-data.se/files/imdiskinst.exe

    REM Check if curl is available, otherwise use PowerShell
    if exist "%SystemRoot%\System32\curl.exe" (
        echo Downloading with curl...
        curl -L -o ImDiskTk-x64.exe "https://static.ltr-data.se/files/imdiskinst.exe"
    ) else if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
        echo Downloading with PowerShell...
        powershell -Command "Invoke-WebRequest -Uri 'https://static.ltr-data.se/files/imdiskinst.exe' -OutFile 'ImDiskTk-x64.exe'"
    ) else (
        echo Neither curl nor PowerShell is available for downloading. Please download ImDisk manually from:
        echo https://static.ltr-data.se/files/imdiskinst.exe
        pause
        exit /b 1
    )

    REM Install ImDisk silently if the download was successful
    if exist "ImDiskTk-x64.exe" (
        echo Installing ImDisk Toolkit...
        start /wait ImDiskTk-x64.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
        echo ImDisk installation completed.

        REM Clean up the installer
        del ImDiskTk-x64.exe
    ) else (
        echo Failed to download ImDisk. Please check your internet connection and try again.
    )
) else (
    echo ImDisk is already installed.
)

echo Setup complete. You can now run the main.py script.
pause
