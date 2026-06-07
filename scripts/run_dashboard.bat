@echo off
cd /d "%~dp0\.."
if "%MONEYPRINTER_TURBO_DIR%"=="" set "MONEYPRINTER_TURBO_DIR=%USERPROFILE%\Applications\MoneyPrinterTurbo"
if "%MONEYPRINTER_TURBO_OUTPUT_DIR%"=="" set "MONEYPRINTER_TURBO_OUTPUT_DIR=%MONEYPRINTER_TURBO_DIR%\storage\tasks"
if "%MONEYPRINTER_TURBO_COMMAND%"=="" set "MONEYPRINTER_TURBO_COMMAND=python main.py"
python -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787
