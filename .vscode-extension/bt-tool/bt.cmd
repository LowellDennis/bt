@echo off
setlocal EnableDelayedExpansion

:: Generate unique session ID based on timestamp and random number
set "BTID=%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%%TIME:~9,2%%RANDOM%"
set "BTID=!BTID: =0!"
set "POSTCMD=%TEMP%\postbt_!BTID!.cmd"

:: Delete post executable command file (if it exists)
if exist "!POSTCMD!" del "!POSTCMD!" > NUL
:: Execute the BIOS tool with session ID
py.exe "%~dp0%~n0.py" --btid=!BTID! %*
:: Check if there is a post executable command file
if not exist "!POSTCMD!" goto :EOF
:: End local scope and execute post command file (so cd persists)
endlocal & call "%TEMP%\postbt_%BTID%.cmd" & del "%TEMP%\postbt_%BTID%.cmd" > NUL 2>&1
