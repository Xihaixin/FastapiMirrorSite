@echo off
chcp 65001 >nul
cls
echo 正在启动指定程序...
echo.

REM 使用相对路径，避免绝对路径中的中文字符编码问题
set "EXE_FILE=first_batch_mirror\server.exe"

echo 正在检查路径：%EXE_FILE%
echo.

REM 首先检查文件是否存在
if exist "%EXE_FILE%" (
    echo [成功] 找到文件，正在以管理员身份启动...
    echo.
    
    REM 方法1：使用PowerShell以管理员身份运行
    powershell -Command "Start-Process '%EXE_FILE%' -Verb RunAs"
    
    REM 检查PowerShell命令是否成功
    if errorlevel 1 (
        echo [警告] PowerShell启动失败，尝试普通方式启动...
        start "" "%EXE_FILE%"
    )
) else (
    echo [错误] 未找到文件！
    echo.
    echo 可能的解决方案：
    echo 1. 检查当前目录：%CD%
    echo 2. 尝试手动导航到目录执行
    echo 3. 检查文件名是否正确：server.exe
    echo.
    
    REM 尝试使用dir命令列出文件
    echo 当前目录下的文件列表：
    dir "first_batch_mirror\*.exe" /b
)

echo.
pause