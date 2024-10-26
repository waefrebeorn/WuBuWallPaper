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


echo Setup complete. You can now run the main.py script.
pause
