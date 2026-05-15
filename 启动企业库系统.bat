@echo off
chcp 65001 >nul
setlocal

REM 切换到本 bat 文件所在目录（即项目根目录），避免从桌面快捷方式启动时路径不正确。
cd /d "%~dp0"

REM 默认使用 Anaconda base 环境；如项目使用独立环境，可改为 trade_agent 等环境名。
set "CONDA_ENV=base"
set "APP_URL=http://127.0.0.1:5000/登录"
set "APP_PORT=5000"

echo ========================================
echo 企业库系统启动器
echo 项目目录：%CD%
echo Conda 环境：%CONDA_ENV%
echo ========================================
echo.

REM 检查 5000 端口是否已被占用。
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort %APP_PORT% -State Listen -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }" >nul 2>nul
if errorlevel 1 (
    echo [错误] 端口 %APP_PORT% 已被占用，Flask 服务无法启动。
    echo 请关闭占用该端口的程序，或结束已有的 Python/Flask 服务后重试。
    echo.
    pause
    exit /b 1
)

REM 查找 Anaconda/Miniconda 的 conda.bat。
set "CONDA_BAT="
if exist "%USERPROFILE%\anaconda3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\anaconda3\condabin\conda.bat"
if not defined CONDA_BAT if exist "%USERPROFILE%\miniconda3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
if not defined CONDA_BAT if exist "%ProgramData%\anaconda3\condabin\conda.bat" set "CONDA_BAT=%ProgramData%\anaconda3\condabin\conda.bat"
if not defined CONDA_BAT if exist "%ProgramData%\miniconda3\condabin\conda.bat" set "CONDA_BAT=%ProgramData%\miniconda3\condabin\conda.bat"

if not defined CONDA_BAT (
    for /f "delims=" %%I in ('where conda 2^>nul') do (
        if not defined CONDA_BAT set "CONDA_BAT=%%I"
    )
    if not defined CONDA_BAT (
        echo [错误] 找不到 conda 命令。
        echo 请确认已安装 Anaconda/Miniconda，并将 conda 加入 PATH，或修改本 bat 中的 CONDA_BAT 路径。
        echo.
        pause
        exit /b 1
    )
)

echo 正在激活 Conda 环境：%CONDA_ENV%
call "%CONDA_BAT%" activate "%CONDA_ENV%"
if errorlevel 1 (
    echo [错误] Conda 环境激活失败：%CONDA_ENV%
    echo 如果你的环境名不是 base，请编辑本 bat，将 CONDA_ENV 改为正确的环境名。
    echo.
    pause
    exit /b 1
)

echo 正在检查 Python 依赖...
python -c "import flask, flask_sqlalchemy, sqlalchemy, openpyxl" >nul 2>nul
if errorlevel 1 (
    echo [错误] 依赖未安装或当前环境不正确。
    echo 请先在当前项目目录执行：pip install -r requirements.txt
    echo 如果使用的不是 base 环境，请先修改本 bat 中的 CONDA_ENV。
    echo.
    pause
    exit /b 1
)

echo 正在启动 Flask 服务...
echo 浏览器会在服务启动成功后自动打开：%APP_URL%
echo 关闭服务的方法：关闭本命令行窗口，或按 Ctrl+C 后输入 Y。
echo.

REM 另开一个轻量等待进程轮询本地服务，成功后自动打开浏览器。
start "等待企业库系统启动" powershell -NoProfile -ExecutionPolicy Bypass -Command "$url='%APP_URL%'; for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 1; if ($r.StatusCode -ge 200) { Start-Process $url; exit 0 } } catch { Start-Sleep -Seconds 1 } }; Write-Host '服务未在 60 秒内响应，请查看后端命令行窗口日志。'; pause"

python app.py
set "APP_EXIT=%ERRORLEVEL%"
echo.
if not "%APP_EXIT%"=="0" (
    echo [错误] Flask 服务异常退出，退出码：%APP_EXIT%
    echo 请检查上方日志；常见原因包括端口被占用、依赖缺失或配置错误。
) else (
    echo Flask 服务已停止。
)
echo.
pause
exit /b %APP_EXIT%
