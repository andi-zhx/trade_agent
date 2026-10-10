@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
pushd "%~dp0"
if errorlevel 1 goto folder_error

echo Trade Agent - Windows Local Launcher
echo Project directory: "%CD%"
echo =============================================
set "LAUNCH_PY="
set "LAUNCH_SELECTOR="
call :try_python "%CD%\.venv\Scripts\python.exe"
if defined TRADE_PYTHON call :try_python "%TRADE_PYTHON%"
if defined CONDA_PREFIX call :try_python "%CONDA_PREFIX%\python.exe"
call :try_python "%USERPROFILE%\anaconda3\python.exe"
call :try_python "%USERPROFILE%\miniconda3\python.exe"
call :try_python "%LOCALAPPDATA%\anaconda3\python.exe"
call :try_python "%LOCALAPPDATA%\miniconda3\python.exe"
call :try_python "%ProgramData%\anaconda3\python.exe"
call :try_python "%ProgramData%\miniconda3\python.exe"
call :try_python "C:\Anaconda3\python.exe"
call :try_python "C:\Miniconda3\python.exe"
for %%V in (3.13 3.12 3.11 3.10 3.9) do call :try_py %%V
for /f "delims=" %%P in ('where python.exe 2^>nul ^| findstr /v /i "WindowsApps"') do call :try_python "%%P"
for /f "delims=" %%C in ('where conda.exe 2^>nul') do call :try_conda "%%C"
for /f "delims=" %%C in ('where conda.bat 2^>nul') do call :try_conda "%%C"
if not defined LAUNCH_PY goto python_missing

"%LAUNCH_PY%" %LAUNCH_SELECTOR% -u "%~dp0launch_local.py" %*
set "LAUNCH_EXIT=%errorlevel%"
goto finish

:try_python
if defined LAUNCH_PY exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import sys; sys.exit(not ((3, 9) <= sys.version_info[:2] < (3, 14)))" >nul 2>&1
if errorlevel 1 exit /b 0
set "LAUNCH_PY=%~1"
exit /b 0

:try_py
if defined LAUNCH_PY exit /b 0
py -%1 -c "import sys; sys.exit(not ((3, 9) <= sys.version_info[:2] < (3, 14)))" >nul 2>&1
if errorlevel 1 exit /b 0
set "LAUNCH_PY=py"
set "LAUNCH_SELECTOR=-%1"
exit /b 0

:try_conda
if defined LAUNCH_PY exit /b 0
call :try_python "%~dp1..\python.exe"
exit /b 0

:python_missing
echo [ERROR] No compatible Python was found. Supported versions: 3.9 - 3.13.
echo Python 3.12 is NOT specifically required.
echo If Conda is installed in a custom folder, open Anaconda Prompt,
echo activate your environment and run this BAT again.
echo Or install Python 3.13 from https://www.python.org/downloads/windows/
echo and select "Add python.exe to PATH" during installation.
set "LAUNCH_EXIT=1"
goto finish

:folder_error
echo [ERROR] Cannot open the project directory.
set "LAUNCH_EXIT=1"
goto pause_exit

:finish
popd
:pause_exit
if not "%LAUNCH_EXIT%"=="0" echo Startup failed. See the error above. Your data has not been deleted.
if not "%TRADE_LAUNCHER_NO_PAUSE%"=="1" pause
exit /b %LAUNCH_EXIT%
