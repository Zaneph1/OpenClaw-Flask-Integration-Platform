"""
OpenClaw Flask 集成平台 - 配置文件
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件（在本模块导入时立即加载）
load_dotenv()

# ==================== OpenClaw 配置 ====================
# OpenClaw Gateway 基础 URL (Tailscale Serve 地址)
# 启动后运行 `tailscale status` 获取你的地址
OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", "https://your-tailscale-url.ts.net")

# Gateway 认证 Token (用于聊天 API)
OPENCLAW_GATEWAY_TOKEN = os.getenv("OPENCLAW_GATEWAY_TOKEN", "your-gateway-token")

# Webhook 认证 Token (用于 Webhook API)
OPENCLAW_WEBHOOK_TOKEN = os.getenv("OPENCLAW_WEBHOOK_TOKEN", "your-webhook-token")

# ==================== Flask 配置 ====================
# Flask 密钥 (用于 session 加密)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# ==================== 会话配置 ====================
# 会话超时时间（分钟）
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# 最大保留历史消息数
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "flask_openclaw.log")
