@echo off
echo Installing dependencies...
pip install pyinstaller watchdog

echo.
echo Building AutoSortFolder.exe...
pyinstaller --onefile --windowed --name AutoSortFolder gui.py

echo.
if exist dist\AutoSortFolder.exe (
    echo  Build successful!
    echo  Find your EXE at:  dist\AutoSortFolder.exe
    echo.
    echo  Copy config.json next to the EXE before running it,
    echo  then edit downloads_dir in config.json to match your username.
) else (
    echo  Build failed. Check the output above for errors.
)
pause
