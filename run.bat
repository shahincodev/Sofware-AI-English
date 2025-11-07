@echo off
::
:: Sofware-AI - اسکریپت اجرا برای ویندوز (CMD)
:: This script creates a virtualenv named .venv, installs dependencies,
:: creates it from .env.example if it doesn't exist, and then runs the main program.

REM --- Create virtual environment if missing ---
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Creating virtual environment .venv...
    python -m venv "%~dp0.venv" 2>NUL || python3 -m venv "%~dp0.venv"
)

REM --- Activate venv ---
call "%~dp0.venv\Scripts\activate.bat"

echo Using Python: %~dp0.venv\Scripts\python.exe

REM --- Upgrade pip and install requirements if any ---
python -m pip install --upgrade pip
if exist "%~dp0requirements.txt" (
    echo Installing requirements from requirements.txt...
    python -m pip install -r "%~dp0requirements.txt"
)

REM --- If the .env.example file does not exist, copy it to .env (does not overwrite existing .env) ---
if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" (
        copy "%~dp0.env.example" "%~dp0.env" >NUL
        echo Created .env from .env.example. Please edit .env and add real API keys before use.
    ) else (
        echo Warning: .env not found and .env.example not present.
    )
)

REM --- Create the required directories ---
if not exist "%~dp0data" mkdir "%~dp0data"
if not exist "%~dp0data\logs" mkdir "%~dp0data\logs"
if not exist "%~dp0data\logs\cache" mkdir "%~dp0data\logs\cache"

REM --- Run the application (forward arguments) ---
echo Launching application...
python "%~dp0main.py" %*

REM Deactivate (for clarity in interactive sessions)
if defined VIRTUAL_ENV (
    deactivate 2>NUL || REM If disabling is not available, it will be disabled.
)
exit /B %ERRORLEVEL%
