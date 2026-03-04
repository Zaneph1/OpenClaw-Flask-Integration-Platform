@echo off
chcp 65001 >nul
echo ========================================
echo   OpenClaw + Flask 集成自动配置脚本
echo ========================================
echo.

:: 获取用户目录
set "USERPROFILE=%USERPROFILE%"
set "OPENCLAW_DIR=%USERPROFILE%\.openclaw"
set "SCRIPT_DIR=%~dp0"

echo OpenClaw 配置目录：%OPENCLAW_DIR%
echo 脚本目录：%SCRIPT_DIR%
echo.

:: 创建 OpenClaw 目录
if not exist "%OPENCLAW_DIR%" (
    echo 正在创建 OpenClaw 目录...
    mkdir "%OPENCLAW_DIR%"
)

:: 检查 Tailscale
echo === 检查 Tailscale 状态 ===
where tailscale >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Tailscale 已安装
    tailscale status
) else (
    echo [警告] Tailscale 未安装
)
echo.

:: 生成随机 Token (使用 PowerShell)
echo === 生成认证 Token ===
for /f "delims=" %%i in ('powershell -Command "[Convert]::ToHexString((New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes(32))"') do set "GATEWAY_TOKEN=%%i"
for /f "delims=" %%i in ('powershell -Command "[Convert]::ToHexString((New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes(32))"') do set "WEBHOOK_TOKEN=%%i"

echo Gateway Token: %GATEWAY_TOKEN:~0,16%... (已生成)
echo Webhook Token: %WEBHOOK_TOKEN:~0,16%... (已生成)
echo.

:: 获取 Tailscale 地址
echo === 获取网络地址 ===
set "OPENCLAW_BASE_URL=http://127.0.0.1:18789"
for /f "delims=" %%i in ('powershell -Command "try { (tailscale ip 2>$null) | Select-Object -First 1 } catch { '127.0.0.1' }"') do set "TAILSCALE_IP=%%i"

if defined TAILSCALE_IP (
    if not "%TAILSCALE_IP%"=="" (
        set "OPENCLAW_BASE_URL=http://%TAILSCALE_IP%:18789"
    )
)
echo Base URL: %OPENCLAW_BASE_URL%
echo.

:: 生成 Flask Secret
for /f "delims=" %%i in ('powershell -Command "[Convert]::ToHexString((New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes(16))"') do set "SECRET_KEY=%%i"

:: 备份现有配置
if exist "%OPENCLAW_DIR%\.env" (
    echo === 备份现有配置 ===
    copy "%OPENCLAW_DIR%\.env" "%OPENCLAW_DIR%\.env.backup.%date:~0,4%%date:~5,2%%date:~8,2%%time:~0,2%%time:~3,2%%time:~6,2%" >nul
    echo 已备份配置文件
)

:: 创建 .env 文件
echo === 创建 OpenClaw .env 配置文件 ===
(
echo # ==================== OpenClaw Flask 集成配置 ====================
echo # 生成时间：%date% %time%
echo.
echo OPENCLAW_BASE_URL=%OPENCLAW_BASE_URL%
echo.
echo # Gateway 认证 Token
echo OPENCLAW_GATEWAY_TOKEN=%GATEWAY_TOKEN%
echo.
echo # Webhook 认证 Token
echo OPENCLAW_WEBHOOK_TOKEN=%WEBHOOK_TOKEN%
echo.
echo # Flask 密钥
echo SECRET_KEY=%SECRET_KEY%
echo.
echo # 会话配置
echo SESSION_TIMEOUT_MINUTES=30
echo MAX_HISTORY_MESSAGES=20
echo.
echo # 日志配置
echo LOG_LEVEL=INFO
echo LOG_FILE=flask_openclaw.log
) > "%OPENCLAW_DIR%\.env"

echo 配置文件已创建：%OPENCLAW_DIR%\.env
echo.

:: 配置 openclaw.json
echo === 配置 OpenClaw Gateway ===
set "OPENCLAW_CONFIG=%OPENCLAW_DIR%\openclaw.json"

if exist "%OPENCLAW_CONFIG%" (
    echo 检测到现有配置文件
    echo 请手动更新以下配置项
) else (
    echo 创建 Gateway 配置文件...
    (
echo {
echo   "gateway": {
echo     "port": 18789,
echo     "bind": "loopback",
echo     "auth": {
echo       "mode": "token",
echo       "token": "%GATEWAY_TOKEN%"
echo     },
echo     "http": {
echo       "endpoints": {
echo         "chatCompletions": { "enabled": true },
echo         "responses": { "enabled": true }
echo       }
echo     },
echo     "tailscale": { "mode": "serve" }
echo   },
echo   "hooks": {
echo     "enabled": true,
echo     "token": "%WEBHOOK_TOKEN%",
echo     "path": "/webhook",
echo     "defaultSessionKey": "webhook:flask",
echo     "allowRequestSessionKey": true,
echo     "allowedSessionKeyPrefixes": ["webhook:", "flask:", "user:"]
echo   },
echo   "session": {
echo     "dmScope": "per-peer",
echo     "reset": { "mode": "idle", "idleMinutes": 60 }
echo   },
echo   "agents": {
echo     "defaults": {
echo       "workspace": "~/.openclaw/workspace",
echo       "model": { "primary": "anthropic/claude-sonnet-4-5" }
echo     }
echo   },
echo   "env": { "loadEnvFiles": true }
echo }
    ) > "%OPENCLAW_CONFIG%"
    echo 配置文件已创建：%OPENCLAW_CONFIG%
)
echo.

:: 更新 Flask .env
echo === 配置 Flask .env 文件 ===
(
echo # ==================== OpenClaw Flask 集成配置 ====================
echo # 生成时间：%date% %time%
echo.
echo OPENCLAW_BASE_URL=%OPENCLAW_BASE_URL%
echo OPENCLAW_GATEWAY_TOKEN=%GATEWAY_TOKEN%
echo OPENCLAW_WEBHOOK_TOKEN=%WEBHOOK_TOKEN%
echo SECRET_KEY=%SECRET_KEY%
echo.
echo SESSION_TIMEOUT_MINUTES=30
echo MAX_HISTORY_MESSAGES=20
echo LOG_LEVEL=INFO
echo LOG_FILE=flask_openclaw.log
) > "%SCRIPT_DIR%.env"

echo Flask .env 已更新：%SCRIPT_DIR%.env
echo.

:: 显示摘要
echo ========================================
echo           配置完成摘要
echo ========================================
echo.
echo 配置文件位置:
echo   OpenClaw: %OPENCLAW_CONFIG%
echo   OpenClaw 环境变量：%OPENCLAW_DIR%\.env
echo   Flask 环境变量：%SCRIPT_DIR%.env
echo.
echo 认证信息 (已保存):
echo   Gateway Token: %GATEWAY_TOKEN%
echo   Webhook Token: %WEBHOOK_TOKEN%
echo.
echo 访问地址:
echo   OPENCLAW_BASE_URL: %OPENCLAW_BASE_URL%
echo.
echo ========================================
echo           下一步操作
echo ========================================
echo.
echo 1. 启动 OpenClaw Gateway:
echo    openclaw gateway --tailscale serve
echo.
echo 2. 安装 Flask 依赖:
echo    cd %SCRIPT_DIR%
echo    pip install -r requirements.txt
echo.
echo 3. 启动 Flask 应用:
echo    python app.py
echo.
echo ========================================
echo.
pause
