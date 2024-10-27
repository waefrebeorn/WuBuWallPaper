# Navigate to the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
cd $scriptDir

# Activate the virtual environment
.\venv\Scripts\Activate

# Run the Python script
python main.py
