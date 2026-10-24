@echo off
cd /d "%~dp0"
py -3.13 -m unittest discover -s . -p "test_*.py" -v
pause
