# OpenClaw + Flask 自动配置脚本

Write-Host "========================================" -ForegroundColor Green
Write-Host "  OpenClaw + Flask 集成自动配置" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取配置目录
$openclawDir = Join-Path $env:USERPROFILE ".openclaw"
$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent

Write-Host "OpenClaw 目录：$openclawDir"
Write-Host "脚本目录：$scriptDir"
Write-Host ""

# 创建目录
if (!(Test-Path $openclawDir)) {
    Write-Host "创建 OpenClaw 目录..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force $openclawDir | Out-Null
}

# 生成 Token
Write-Host "=== 生成认证 Token ===" -ForegroundColor Cyan
$gatewayToken = [Convert]::ToHexString((New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes(32))
$webhookToken = [Convert]::ToHexString((New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes(32))
$secretKey = [Convert]::ToHexString((New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes(16))

Write-Host "Gateway Token: $($gatewayToken.Substring(0,16))... (已生成)" -ForegroundColor Green
Write-Host "Webhook Token: $($webhookToken.Substring(0,16))... (已生成)" -ForegroundColor Green
Write-Host "Secret Key: $($secretKey.Substring(0,16))... (已生成)" -ForegroundColor Green
Write-Host ""

# 获取网络地址
Write-Host "=== 获取网络地址 ===" -ForegroundColor Cyan
$baseUrl = "http://127.0.0.1:18789"
try {
    $tailscaleIp = tailscale ip 2>$null | Select-Object -First 1
    if ($tailscaleIp) {
        $baseUrl = "http://$($tailscaleIp):18789"
        Write-Host "Tailscale IP: $tailscaleIp" -ForegroundColor Green
    }
} catch {
    Write-Host "使用本地地址" -ForegroundColor Yellow
}
Write-Host "Base URL: $baseUrl" -ForegroundColor Green
Write-Host ""

# 创建 Flask .env
Write-Host "=== 创建 Flask .env ===" -ForegroundColor Cyan
$flaskEnv = @"
# OpenClaw Flask 集成配置
# 生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

OPENCLAW_BASE_URL=$baseUrl
OPENCLAW_GATEWAY_TOKEN=$gatewayToken
OPENCLAW_WEBHOOK_TOKEN=$webhookToken
SECRET_KEY=$secretKey

# 会话配置
SESSION_TIMEOUT_MINUTES=30
MAX_HISTORY_MESSAGES=20

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=flask_openclaw.log
"@

$flaskEnv | Out-File -FilePath (Join-Path $scriptDir ".env") -Encoding utf8 -NoNewline
Write-Host "Flask .env 已创建" -ForegroundColor Green

# 创建 openclaw.json
Write-Host "=== 创建 openclaw.json ===" -ForegroundColor Cyan
if (Test-Path (Join-Path $openclawDir "openclaw.json")) {
    Write-Host "检测到现有配置，创建备份..." -ForegroundColor Yellow
    Copy-Item (Join-Path $openclawDir "openclaw.json") (Join-Path $openclawDir "openclaw.json.backup.$(Get-Date -Format 'yyyyMMddHHmmss')")
}

$configJson = @"
{
  "gateway": {
    "port": 18789,
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "$gatewayToken"
    },
    "http": {
      "endpoints": {
        "chatCompletions": { "enabled": true },
        "responses": { "enabled": true }
      }
    },
    "tailscale": {
      "mode": "serve"
    }
  },
  "hooks": {
    "enabled": true,
    "token": "$webhookToken",
    "path": "/webhook",
    "defaultSessionKey": "webhook:flask",
    "allowRequestSessionKey": true,
    "allowedSessionKeyPrefixes": ["webhook:", "flask:", "user:"]
  },
  "session": {
    "dmScope": "per-peer",
    "reset": {
      "mode": "idle",
      "idleMinutes": 60
    }
  },
  "agents": {
    "defaults": {
      "workspace": "~/.openclaw/workspace",
      "model": {
        "primary": "anthropic/claude-sonnet-4-5"
      }
    }
  },
  "env": {
    "loadEnvFiles": true
  }
}
"@

$configJson | Out-File -FilePath (Join-Path $openclawDir "openclaw.json") -Encoding utf8 -NoNewline
Write-Host "openclaw.json 已创建" -ForegroundColor Green

# 创建 .env
Write-Host "=== 创建 ~/.openclaw/.env ===" -ForegroundColor Cyan
$envContent = @"
# OpenClaw 环境变量
# 生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

OPENCLAW_BASE_URL=$baseUrl
OPENCLAW_GATEWAY_TOKEN=$gatewayToken
OPENCLAW_WEBHOOK_TOKEN=$webhookToken
SECRET_KEY=$secretKey
"@

$envContent | Out-File -FilePath (Join-Path $openclawDir ".env") -Encoding utf8 -NoNewline
Write-Host ".env 已创建" -ForegroundColor Green

# 显示摘要
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  配置完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "配置文件:" -ForegroundColor Cyan
Write-Host "  - $openclawDir\openclaw.json"
Write-Host "  - $openclawDir\.env"
Write-Host "  - $scriptDir\.env"
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "  1. 启动 Gateway: openclaw gateway --tailscale serve"
Write-Host "  2. 安装依赖：pip install -r requirements.txt"
Write-Host "  3. 启动 Flask: python app.py"
Write-Host ""

# 保存 token 信息到文本文件
$tokenInfo = @"
OpenClaw Flask 集成 - 认证信息
生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

OPENCLAW_BASE_URL=$baseUrl
OPENCLAW_GATEWAY_TOKEN=$gatewayToken
OPENCLAW_WEBHOOK_TOKEN=$secretKey
SECRET_KEY=$secretKey

请妥善保管此文件!
"@

$tokenInfo | Out-File -FilePath (Join-Path $scriptDir "credentials.txt") -Encoding utf8 -NoNewline
Write-Host "认证信息已保存到：$scriptDir\credentials.txt" -ForegroundColor Green
Write-Host ""
