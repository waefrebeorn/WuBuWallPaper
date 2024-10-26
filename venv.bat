@echo off
echo Setting up Python virtual environment...

REM Check if "venv" directory exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
) else (
    echo Virtual environment not found. Please ensure Python and venv are installed correctly.
    exit /b 1
)

echo Virtual environment activated. You can now install dependencies with pip.
echo Type 'deactivate' to exit the virtual environment.
cmd /k
