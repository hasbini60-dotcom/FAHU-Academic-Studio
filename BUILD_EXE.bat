@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (echo Python Launcher not found. Install Python 3.13. & pause & exit /b 1)
py -3.13 -m pip install --upgrade pyinstaller matplotlib reportlab pillow
if errorlevel 1 (echo Dependency installation failed. & pause & exit /b 1)
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name FAHU_Academic_V4_1 FAHU_Academic_V4_1.py
if errorlevel 1 (echo Build failed. & pause & exit /b 1)
echo SUCCESS: dist\FAHU_Academic_V4_1.exe
pause
