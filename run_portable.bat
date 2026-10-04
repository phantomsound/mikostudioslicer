@echo off
setlocal enabledelayedexpansion
title Miko Studio Slicer - Portable Edition

set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

echo =======================================================
echo    Miko Studio Slicer - Offline Production Suite       
echo =======================================================
echo.

set "PY_BIN="
if exist "%APP_DIR%python_portable\python.exe" (
    set "PY_BIN=%APP_DIR%python_portable\python.exe"
    echo [*] Using Portable Python runtime from USB drive.
) else if exist "%APP_DIR%venv\Scripts\python.exe" (
    set "PY_BIN=%APP_DIR%venv\Scripts\python.exe"
    echo [*] Using local virtual environment.
) else (
    where python.exe >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_BIN=python.exe"
        echo [*] Using System Python on host machine.
    )
)

if "%PY_BIN%"=="" (
    echo [ERROR] No Python runtime detected.
    echo Please bundle an embeddable Python package in the 'python_portable' directory.
    pause
    exit /b 1
)

set "PORT=8088"
:find_port
netstat -ano | findstr /r /c:":%PORT% *LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    set /a PORT+=1
    if !PORT! gtr 8138 (
        echo [ERROR] No open ports available in range 8088-8138.
        pause
        exit /b 1
)
    goto find_port
)

echo [*] Starting server daemon on http://localhost:%PORT% ...
echo.
start "" /b "%PY_BIN%" "%APP_DIR%server.py" --port %PORT%
timeout /t 2 /nobreak >nul
start http://localhost:%PORT%

echo [READY] Studio is running on http://localhost:%PORT%
echo Keep this terminal window open while working.
echo.
cmd /k
