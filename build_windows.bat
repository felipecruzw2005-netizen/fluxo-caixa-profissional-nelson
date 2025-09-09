
@echo off
setlocal enabledelayedexpansion

REM Create venv
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate

REM Upgrade pip and install deps
python -m pip install --upgrade pip wheel
pip install -r requirements.txt pyinstaller

REM Build
pyinstaller pyinstaller.spec --clean

echo.
echo Build finalizado.
echo Abra a pasta "dist\FluxoPro" e execute FluxoPro.exe
pause
