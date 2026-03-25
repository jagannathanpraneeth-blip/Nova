@echo off
REM Nova OpenAI API Key Setup Script
REM This will permanently add your OpenAI API key to system environment variables

echo ========================================
echo    NOVA - OpenAI API Key Setup
echo ========================================
echo.
echo This script will help you set up screen vision for Nova.
echo.
echo First, get your API key from: https://platform.openai.com/api-keys
echo.
set /p API_KEY="Enter your OpenAI API key (starts with sk-): "

if "%API_KEY%"=="" (
    echo.
    echo ERROR: No API key entered!
    echo Please run the script again and enter your key.
    pause
    exit /b 1
)

echo.
echo Setting environment variable...
setx OPENAI_API_KEY "%API_KEY%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo    SUCCESS! API Key Installed!
    echo ========================================
    echo.
    echo Your OpenAI API key has been saved permanently!
    echo.
    echo IMPORTANT: Close this window and open a NEW PowerShell/Command Prompt
    echo Then run: python main.py
    echo.
    echo Nova can now see and analyze your screen! ^_^
    echo.
    echo Try saying: "Nova, analyze screen"
    echo.
) else (
    echo.
    echo ERROR: Failed to set environment variable
    echo Please try running this script as Administrator
    echo.
)

pause
