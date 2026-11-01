@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 server.py --enable-experiments
) else (
  python server.py --enable-experiments
)
pause
