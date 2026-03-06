@echo off
chcp 65001 >nul
echo ============================================================
echo    WPP MD 小红书链接监测工具 v4 Ultimate - EXE打包程序
echo ============================================================
echo.
echo 正在开始打包 Ultimate v4...
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 build_ultimate_v4_exe.py
) else (
    python build_ultimate_v4_exe.py
)

if not %errorlevel%==0 (
    echo.
    echo [失败] 打包过程出现错误，请检查上方日志。
    pause
    exit /b 1
)

echo.
echo [完成] 打包成功，EXE 位于 dist 目录。

pause








