@echo off
setlocal
title AI Research Agent - Setup
color 0A

set APP_DIR=%~dp0
set OLLAMA_MODEL=qwen2.5:1.5b
set OLLAMA_INSTALLER=https://ollama.com/download/OllamaSetup.exe
set UV_INSTALLER=https://astral.sh/uv/install.ps1

echo ============================================
echo   AI Research Agent - First Time Setup
echo ============================================
echo.

:: ── Step 1: Check Ollama ──────────────────────────────────────────────────
echo [1/4] Checking Ollama...
where ollama >NUL 2>&1
if errorlevel 1 (
    echo     Ollama not found. Downloading installer...
    curl -L %OLLAMA_INSTALLER% -o "%TEMP%\OllamaSetup.exe"
    echo     Installing Ollama silently...
    "%TEMP%\OllamaSetup.exe" /S
    timeout /t 5 /nobreak >NUL
    echo     Ollama installed.
) else (
    echo     Ollama already installed. Skipping.
)

:: ── Step 2: Pull AI model ─────────────────────────────────────────────────
echo.
echo [2/4] Downloading AI model "%OLLAMA_MODEL%"...
echo     This may take a few minutes on first run.
start "" /B "C:\Program Files\Ollama\ollama.exe" serve
timeout /t 3 /nobreak >NUL
ollama pull %OLLAMA_MODEL%
echo     Model ready.

:: ── Step 3: Install uv + Python deps ─────────────────────────────────────
echo.
echo [3/4] Installing Python dependencies...
where uv >NUL 2>&1
if errorlevel 1 (
    echo     Installing uv package manager...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    :: Refresh PATH
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)
cd /d "%APP_DIR%"
uv sync
echo     Dependencies installed.

:: ── Step 4: Create desktop shortcut ──────────────────────────────────────
echo.
echo [4/4] Creating desktop shortcut...
set SHORTCUT=%USERPROFILE%\Desktop\AI Research Agent.lnk
set TARGET=%APP_DIR%launch.bat
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%APP_DIR%'; $s.IconLocation = 'shell32.dll,13'; $s.Description = 'AI Research Agent'; $s.Save()"
echo     Desktop shortcut created.

:: ── Done ──────────────────────────────────────────────────────────────────
echo.
echo ============================================
echo   Setup complete!
echo   Double-click "AI Research Agent" on your
echo   desktop to launch the app anytime.
echo ============================================
echo.
pause