@echo off
chcp 65001 >nul
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%ai_news_digest.py

echo ========================================
echo    AI 日报 - 注册 Windows 定时任务
echo ========================================
echo.

schtasks /create /tn "AI_News_Digest" /tr "python \"%PYTHON_SCRIPT%\"" /sc daily /st 08:00 /f

if %errorlevel% == 0 (
    echo [成功] 定时任务已创建，每天 08:00 自动运行
    echo.
    echo 查看任务: schtasks /query /tn "AI_News_Digest"
    echo 删除任务: schtasks /delete /tn "AI_News_Digest" /f
) else (
    echo [失败] 无法创建任务，请右键"以管理员身份运行"此文件
)

echo.
pause
