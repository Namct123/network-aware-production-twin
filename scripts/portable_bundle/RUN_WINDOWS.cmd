@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP_WINDOWS.cmd first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" launch.py demo --view
set "twin_result=%errorlevel%"
pause
exit /b %twin_result%
