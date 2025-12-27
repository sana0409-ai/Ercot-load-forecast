@echo off
REM Batch wrapper to run the PowerShell start script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_server_8001.ps1"
