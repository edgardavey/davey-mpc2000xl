@echo off
rem SPDX-License-Identifier: BSD-3-Clause
setlocal DisableDelayedExpansion
where py.exe >nul 2>&1
if not errorlevel 1 goto use_py
where python.exe >nul 2>&1
if not errorlevel 1 goto use_python
echo Python 3.9 or newer is required. Install it from python.org with Tcl/Tk and add it to PATH.
pause
exit /b 1
:use_py
if "%~1"=="" (
    py -3 "%~dp0run.py" --auto --remember
) else (
    py -3 "%~dp0run.py" %*
)
set "LAUNCH_EXIT=%ERRORLEVEL%"
goto finished
:use_python
if "%~1"=="" (
    python "%~dp0run.py" --auto --remember
) else (
    python "%~dp0run.py" %*
)
set "LAUNCH_EXIT=%ERRORLEVEL%"
goto finished
:finished
if not "%LAUNCH_EXIT%"=="0" pause
exit /b %LAUNCH_EXIT%
