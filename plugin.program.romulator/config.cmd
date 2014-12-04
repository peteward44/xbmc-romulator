@echo off

set PYTHON_PATH="c:\Python27\python.exe"

if exist %PYTHON_PATH% (
call %PYTHON_PATH% %~dp0resources\lib\DoCommandLineConfig.py 
) else (
echo Could not find Python 2.7 installation in location %PYTHON_PATH%
)

pause
