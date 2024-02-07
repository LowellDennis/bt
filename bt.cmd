@echo off

:: Delete post executable command file (if it exists)
if exist %TEMP%\postbt.cmd del %TEMP%\postbt.cmd > NUL
:: Excute the BIOS tool
py.exe %~dp0%~n0.py %*
:: See if there is a post executable command file
if not exist %TEMP%\postbt.cmd goto :EOF
:: Execute post command file
call %TEMP%\postbt.cmd
