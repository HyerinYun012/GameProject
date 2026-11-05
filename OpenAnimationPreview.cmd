@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if not errorlevel 1 (
  python "Tools\AnimationPreview\serve_preview.py"
  goto :end
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "Tools\AnimationPreview\serve_preview.py"
  goto :end
)

echo.
echo Python 3 was not found.
echo Install Python or run this project through another local HTTP server.
echo.
pause

:end
endlocal
