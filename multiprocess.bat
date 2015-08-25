@echo off
setlocal EnableDelayedExpansion
for /l %%i in (1,1,20) do call :loop %%i
goto :eof
:loop
call :checkinstances
if %INSTANCES% LSS 15 (
    echo Starting processing instance for %1
    for /f "skip=%1 tokens=*" %%G in (text.txt) do set "url=%%G" & goto nextline
    :nextline
    if [%url%] == [] goto end
    start /min python27 fbAlbumDownload.py "%url%"
    goto :eof
)
rem wait a second, can be adjusted with -w (-n 2 because the first ping returns immediately;
rem otherwise just use an address that's unused and -n 1)
echo Waiting for instances to close ...
ping -n 2 ::1 >nul 2>&1
rem jump back to see whether we can spawn a new process now
goto loop
goto :eof

:checkinstances
rem this could probably be done better. But INSTANCES should contain the number of running instances afterwards.
for /f "usebackq" %%t in (`tasklist /fo csv /fi "imagename eq cmd.exe"^|wc -l`) do set INSTANCES=%%t
goto :eof
:end