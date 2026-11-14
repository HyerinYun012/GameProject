@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if not errorlevel 1 (
  python main.py
  goto :end
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 main.py
  goto :end
)

echo Python 3 was not found.
pause

:end
endlocal
