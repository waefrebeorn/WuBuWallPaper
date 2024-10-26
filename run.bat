@echo off
REM Navigate to the script directory
cd "%~dp0"

REM Activate the virtual environment and run the main script, logging output
venv\Scripts\activate && python main.py > output_log.txt 2>&1

REM Keep the command window open after execution to display any errors
type output_log.txt
pause
