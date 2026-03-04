#!/bin/bash
# OpenClaw + Flask 集成自动配置脚本
# 用于 Windows Git Bash / Linux / Mac

set -e

echo "========================================"
echo "  OpenClaw + Flask 集成自动配置脚本"
echo "========================================"
echo ""

# 检测操作系统
OS_TYPE=$(uname -s)
echo "检测到操作系统：$OS_TYPE"

# 定义配置路径
if [[ "$OS_TYPE" == *"NT"* ]] || [[ "$OS_TYPE" == "MINGW"* ]] || [[ "$OS_TYPE" == "MSYS"* ]]; then
    # Windows Git Bash
    OPENCLAW_DIR="/c/Users/$USER/.openclaw"
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
else
    # Linux/Mac
    OPENCLAW_DIR="$HOME/.openclaw"
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

echo "OpenClaw 配置目录：$OPENCLAW_DIR"
echo "脚本目录：$SCRIPT_DIR"
echo ""

# 检查 OpenClaw 目录是否存在
if [ ! -d "$OPENCLAW_DIR" ]; then
    echo "❌ OpenClaw 目录不存在，正在创建..."
    mkdir -p "$OPENCLAW_DIR"
fi

# 检查 Tailscale 是否安装
echo "=== 检查 Tailscale 状态 ==="
if command -v tailscale &> /dev/null; then
    echo "✓ Tailscale 已安装"
    TAILSCALE_STATUS=$(tailscale status 2>/dev/null | head -n 5 || echo "未登录")
    echo "$TAILSCALE_STATUS"
else
    echo "⚠ Tailscale 未安装，请前往 https://tailscale.com/download 下载安装"
fi
echo ""

# 生成随机 Token
echo "=== 生成认证 Token ==="
if command -v openssl &> /dev/null; then
    GATEWAY_TOKEN=$(openssl rand -hex 32)
    WEBHOOK_TOKEN=$(openssl rand -hex 32)
elif command -v node &> /dev/null; then
    GATEWAY_TOKEN=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
    WEBHOOK_TOKEN=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
else
    echo "❌ 需要 openssl 或 node 来生成随机 token"
    exit 1
fi

echo "✓ Gateway Token: ${GATEWAY_TOKEN:0:16}... (已生成)"
echo "✓ Webhook Token: ${WEBHOOK_TOKEN:0:16}... (已生成)"
echo ""

# 获取 Tailscale 地址
echo "=== 获取 Tailscale 地址 ==="
if command -v tailscale &> /dev/null; then
    TAILSCALE_IP=$(tailscale ip 2>/dev/null | head -n 1 || echo "")
    TAILSCALE_HOSTNAME=$(hostname)

    if [ -n "$TAILSCALE_IP" ]; then
        # 尝试获取 MagicDNS 名称
        MAGIC_DNS=$(tailscale status --json 2>/dev/null | grep -o '"DNSName":"[^"]*"' | head -n 1 | cut -d'"' -f4 | sed 's/.$//')

        if [ -n "$MAGIC_DNS" ]; then
            OPENCLAW_BASE_URL="https://${MAGIC_DNS}.ts.net"
        else
            OPENCLAW_BASE_URL="http://${TAILSCALE_IP}:18789"
        fi
        echo "✓ Tailscale IP: $TAILSCALE_IP"
        echo "✓ Base URL: $OPENCLAW_BASE_URL"
    else
        OPENCLAW_BASE_URL="http://127.0.0.1:18789"
        echo "⚠ 无法获取 Tailscale IP，使用本地地址：$OPENCLAW_BASE_URL"
    fi
else
    OPENCLAW_BASE_URL="http://127.0.0.1:18789"
    echo "⚠ Tailscale 未安装，使用本地地址：$OPENCLAW_BASE_URL"
fi
echo ""

# 备份现有配置
if [ -f "$OPENCLAW_DIR/.env" ]; then
    echo "=== 备份现有配置 ==="
    cp "$OPENCLAW_DIR/.env" "$OPENCLAW_DIR/.env.backup.$(date +%Y%m%d%H%M%S)"
    echo "✓ 已备份到 .env.backup.*"
fi

# 创建/更新 .env 文件
echo "=== 创建 .env 配置文件 ==="
cat > "$OPENCLAW_DIR/.env" <<EOF
# ==================== OpenClaw Flask 集成配置 ====================
# 此文件由自动配置脚本生成于 $(date '+%Y-%m-%d %H:%M:%S')

# OpenClaw Gateway 基础 URL
OPENCLAW_BASE_URL=${OPENCLAW_BASE_URL}

# Gateway 认证 Token (用于聊天 API 和工具调用)
OPENCLAW_GATEWAY_TOKEN=${GATEWAY_TOKEN}

# Webhook 认证 Token (用于 Webhook API)
OPENCLAW_WEBHOOK_TOKEN=${WEBHOOK_TOKEN}

# ==================== Flask 配置 ====================
# Flask 密钥 (用于 session 加密)
SECRET_KEY=$(openssl rand -hex 16 2>/dev/null || node -e "console.log(require('crypto').randomBytes(16).toString('hex'))")

# ==================== 会话配置 ====================
# 会话超时时间（分钟）
SESSION_TIMEOUT_MINUTES=30

# 最大保留历史消息数
MAX_HISTORY_MESSAGES=20

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
LOG_FILE=flask_openclaw.log
EOF

echo "✓ 配置文件已创建：$OPENCLAW_DIR/.env"
echo ""

# 检查并更新 openclaw.json 配置
echo "=== 配置 OpenClaw Gateway ==="
OPENCLAW_CONFIG="$OPENCLAW_DIR/openclaw.json"

if [ -f "$OPENCLAW_CONFIG" ]; then
    echo "✓ 检测到现有配置文件：$OPENCLAW_CONFIG"
    echo "  请手动确保以下配置已设置："
    echo ""
    echo "  gateway.auth.token: \"${GATEWAY_TOKEN}\""
    echo "  hooks.token: \"${WEBHOOK_TOKEN}\""
    echo "  hooks.enabled: true"
    echo ""
else
    echo "⚠ 配置文件不存在，正在创建基础配置..."

    cat > "$OPENCLAW_CONFIG" <<EOF
{
  "gateway": {
    "port": 18789,
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "${GATEWAY_TOKEN}"
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
    "token": "${WEBHOOK_TOKEN}",
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
EOF

    echo "✓ 配置文件已创建：$OPENCLAW_CONFIG"
fi
echo ""

# 更新 Flask 目录的 .env 文件
FLASK_ENV="$SCRIPT_DIR/.env"
echo "=== 配置 Flask .env 文件 ==="
cat > "$FLASK_ENV" <<EOF
# ==================== OpenClaw Flask 集成配置 ====================
# 此文件由自动配置脚本生成于 $(date '+%Y-%m-%d %H:%M:%S')

# OpenClaw Gateway 基础 URL
OPENCLAW_BASE_URL=${OPENCLAW_BASE_URL}

# Gateway 认证 Token (用于聊天 API)
OPENCLAW_GATEWAY_TOKEN=${GATEWAY_TOKEN}

# Webhook 认证 Token (用于 Webhook API)
OPENCLAW_WEBHOOK_TOKEN=${WEBHOOK_TOKEN}

# Flask 密钥
SECRET_KEY=$(openssl rand -hex 16 2>/dev/null || node -e "console.log(require('crypto').randomBytes(16).toString('hex'))")

# 会话配置
SESSION_TIMEOUT_MINUTES=30
MAX_HISTORY_MESSAGES=20

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=flask_openclaw.log
EOF

echo "✓ Flask .env 文件已更新：$FLASK_ENV"
echo ""

# 显示配置摘要
echo "========================================"
echo "           配置完成摘要"
echo "========================================"
echo ""
echo "📁 配置文件位置:"
echo "   OpenClaw 配置：$OPENCLAW_CONFIG"
echo "   OpenClaw 环境变量：$OPENCLAW_DIR/.env"
echo "   Flask 环境变量：$FLASK_ENV"
echo ""
echo "🔑 认证信息:"
echo "   Gateway Token: ${GATEWAY_TOKEN}"
echo "   Webhook Token: ${WEBHOOK_TOKEN}"
echo ""
echo "🌐 访问地址:"
echo "   OpenClaw Base URL: $OPENCLAW_BASE_URL"
echo ""
echo "========================================"
echo "           下一步操作"
echo "========================================"
echo ""
echo "1. 启动 OpenClaw Gateway:"
echo "   openclaw gateway --tailscale serve"
echo ""
echo "2. 安装 Flask 依赖:"
echo "   cd $SCRIPT_DIR"
echo "   pip install -r requirements.txt"
echo ""
echo "3. 启动 Flask 应用:"
echo "   python app.py"
echo ""
echo "4. 测试连接:"
echo "   curl -H \"Authorization: Bearer ${GATEWAY_TOKEN}\" ${OPENCLAW_BASE_URL}/health"
echo ""
echo "========================================"
echo ""

# 可选：直接启动服务
read -p "是否现在启动 OpenClaw Gateway? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在启动 OpenClaw Gateway..."
    if command -v openclaw &> /dev/null; then
        openclaw gateway --tailscale serve &
        echo "✓ Gateway 已在后台启动"
    else
        echo "⚠ openclaw 命令未找到，请手动启动"
    fi
fi

echo ""
echo "配置完成！🎉"
