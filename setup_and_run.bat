@echo off
echo Nova Voice Assistant Setup
echo ==========================

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies. Please check your internet connection or python installation.
    pause
    exit /b %errorlevel%
)

echo [2/3] Downloading Language Model...
python -m spacy download en_core_web_sm
if %errorlevel% neq 0 (
    echo Error downloading spacy model.
    pause
    exit /b %errorlevel%
)

echo [3/3] Starting Nova...
python main.py

pause
