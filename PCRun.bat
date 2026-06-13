@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "remote_keys.py"
) else (
    where pyw >nul 2>nul
    if not errorlevel 1 (
        start "" pyw "remote_keys.py"
    ) else (
        where pythonw >nul 2>nul
        if not errorlevel 1 (
            start "" pythonw "remote_keys.py"
        ) else (
            start "" /min python "remote_keys.py"
        )
    )
)
