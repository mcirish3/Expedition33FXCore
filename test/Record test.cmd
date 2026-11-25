@echo off
rem Records frame times (PresentMon) while you play. PresentMon needs administrator rights.
net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
cd /d "%~dp0"
if not exist "%~dp0PresentMon-2.6.0-x64.exe" (
  echo Put PresentMon-2.6.0-x64.exe from github.com/GameTechDev/PresentMon/releases next to this file.
  pause
  exit /b 1
)
for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set STAMP=%%t
set GAME=C:\Program Files (x86)\Steam\steamapps\common\Expedition 33\Sandfall\Binaries\Win64
echo Clair Obscur test recorder. Nothing in the game is changed by this window.
echo.
echo Waiting for the game. Start it from Steam now (or keep playing if it is running).
:wait
tasklist /fi "imagename eq SandFall-Win64-Shipping.exe" 2>nul | find /i "SandFall-Win64" >nul
if errorlevel 1 ( timeout /t 2 /nobreak >nul & goto wait )
echo Recording. Leave this window open. It stops by itself when you quit the game.
set PM=%~dp0PresentMon-2.6.0-x64.exe
start "" /b "%PM%" --process_name SandFall-Win64-Shipping.exe --output_file "captures\%STAMP%.frames.csv" --qpc_time --terminate_on_proc_exit --session_name E33Test --stop_existing_session --no_console_stats
rem PresentMon once missed the game closing, so watch for that here as well.
:play
timeout /t 3 /nobreak >nul
tasklist /fi "imagename eq SandFall-Win64-Shipping.exe" 2>nul | find /i "SandFall-Win64" >nul
if not errorlevel 1 goto play
echo.
echo The game has closed. Stopping the recording, about 10 seconds. Do not press Ctrl+C.
timeout /t 3 /nobreak >nul
tasklist /fi "imagename eq PresentMon-2.6.0-x64.exe" 2>nul | find /i "PresentMon" >nul
if errorlevel 1 goto save
echo Stopping PresentMon...
"%PM%" --session_name E33Test --terminate_existing_session >nul 2>&1
timeout /t 5 /nobreak >nul
taskkill /im PresentMon-2.6.0-x64.exe /f >nul 2>&1
:save
copy /y "%GAME%\Expedition33FXCore.log" "captures\%STAMP%.mod.log" >nul
copy /y "%GAME%\Expedition33FXCore.ini" "captures\%STAMP%.mod.ini" >nul
copy /y "%LOCALAPPDATA%\Sandfall\Saved\Config\Windows\GameUserSettings.ini" "captures\%STAMP%.settings.ini" >nul
echo.
echo DONE. Saved as %STAMP%. Tell Claude the test is done.
echo This window closes when you press a key.
pause >nul