@echo off
setlocal

:: ── Config ────────────────────────────────────────────────────────────────
set APP_DIR=%~dp0
set STREAMLIT_PORT=8501
set OLLAMA_MODEL=qwen2.5:1.5b

:: ── Step 1: Start Ollama if not running ───────────────────────────────────
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if errorlevel 1 (
    start "" /B "C:\Program Files\Ollama\ollama.exe" serve
    timeout /t 4 /nobreak >NUL
)

:: ── Step 2: Check Ollama is responding ────────────────────────────────────
:wait_ollama
curl -s http://localhost:11434 >NUL 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >NUL
    goto wait_ollama
)

:: ── Step 3: Launch Streamlit in background ────────────────────────────────
start "" /B cmd /c "cd /d "%APP_DIR%" && uv run streamlit run app\streamlit_app.py --server.port %STREAMLIT_PORT% --server.headless true > streamlit.log 2>&1"

:: ── Step 4: Wait for Streamlit to be ready ────────────────────────────────
:wait_streamlit
timeout /t 2 /nobreak >NUL
curl -s http://localhost:%STREAMLIT_PORT% >NUL 2>&1
if errorlevel 1 goto wait_streamlit

:: ── Step 5: Open browser ──────────────────────────────────────────────────
start "" http://localhost:%STREAMLIT_PORT%

:: ── Step 6: Keep Ollama alive, exit this window ───────────────────────────
exit /b