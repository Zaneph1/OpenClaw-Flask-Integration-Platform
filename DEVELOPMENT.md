# OpenClaw Flask 集成平台开发文档

**文档版本**: 1.0
**创建日期**: 2026-03-04
**最后更新**: 2026-03-04

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术架构](#2-技术架构)
3. [环境配置](#3-环境配置)
4. [快速开始](#4-快速开始)
5. [API 接口文档](#5-api-接口文档)
6. [会话管理](#6-会话管理)
7. [开发指南](#7-开发指南)
8. [常见问题](#8-常见问题)
9. [附录](#9-附录)

---

## 1. 项目概述

### 1.1 项目简介

OpenClaw Flask 集成平台是一个类似飞书通道功能的 AI 集成中间件，通过 HTTP API 将 OpenClaw 的智能对话能力集成到任意 Flask 应用中。

### 1.2 核心功能

- **智能对话**: 与 OpenClaw AI 进行多轮对话
- **会话管理**: 自动管理用户会话和历史记录
- **工具调用**: 调用 OpenClaw 的各种工具（文件操作、浏览器控制等）
- **Webhook 支持**: 支持外部事件触发 AI 任务

### 1.3 适用场景

- 企业客服系统集成 AI 能力
- 内部工具添加智能助手
- 多用户聊天平台
- 自动化任务触发

---

## 2. 技术架构

### 2.1 架构图

```
┌─────────────────┐      HTTP API      ┌─────────────────┐
│   客户端应用     │ ◄───────────────► │  Flask 平台      │
│  (Web/Mobile)   │                    │  (本项目的)      │
└─────────────────┘                    └────────┬────────┘
                                                │
                                                │ HTTP
                                                ▼
                                       ┌─────────────────┐
                                       │  OpenClaw       │
                                       │  Gateway        │
                                       └─────────────────┘
```

### 2.2 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| Web 框架 | Flask | 3.0.0 |
| HTTP 客户端 | Requests | 2.31.0 |
| 环境配置 | python-dotenv | >=1.0.1 |
| Python | CPython | 3.13+ |

### 2.3 目录结构

```
flask/
├── app.py                 # Flask 主应用（API 路由）
├── config.py              # 配置管理
├── session_manager.py     # 会话管理器
├── openclaw_client.py     # OpenClaw API 客户端
├── requirements.txt       # Python 依赖
├── .env                   # 环境变量配置
├── test_api.py            # API 测试脚本
├── test_multi_turn.py     # 多轮对话测试
└── README.md              # 用户文档
```

---

## 3. 环境配置

### 3.1 前置要求

- Python 3.13+
- OpenClaw Gateway 已安装并运行
- pip 包管理器

### 3.2 安装依赖

```bash
cd flask
pip install -r requirements.txt
```

### 3.3 OpenClaw 配置

确保 OpenClaw Gateway 已正确配置：

**文件位置**: `~/.openclaw/openclaw.json`

```json
{
  "gateway": {
    "port": 18789,
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "你的-gateway-token"
    },
    "http": {
      "endpoints": {
        "chatCompletions": { "enabled": true }
      }
    }
  },
  "hooks": {
    "enabled": true,
    "token": "你的-webhook-token",
    "allowRequestSessionKey": true,
    "allowedSessionKeyPrefixes": ["webhook:", "flask:", "user:"]
  }
}
```

### 3.4 Flask 配置

**文件位置**: `flask/.env`

```bash
# OpenClaw 地址
OPENCLAW_BASE_URL=http://127.0.0.1:18789

# Gateway 认证 Token（用于聊天和工具调用）
OPENCLAW_GATEWAY_TOKEN=你的-gateway-token

# Webhook 认证 Token
OPENCLAW_WEBHOOK_TOKEN=你的-webhook-token

# Flask 密钥
SECRET_KEY=随机生成的-secret-key

# 会话配置
SESSION_TIMEOUT_MINUTES=30
MAX_HISTORY_MESSAGES=20
```

---

## 4. 快速开始

### 4.1 启动服务

**步骤 1**: 启动 OpenClaw Gateway
```bash
openclaw gateway
```

**步骤 2**: 启动 Flask 应用
```bash
cd flask
python app.py
```

服务将在 `http://localhost:5000` 启动。

### 4.2 第一个 API 调用

```bash
curl -X POST http://localhost:5000/api/message/send \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "message": "你好"}'
```

**响应**:
```json
{
  "ok": true,
  "reply": "你好！有什么可以帮助你的？",
  "session_id": "xxx-xxx-xxx",
  "usage": {...}
}
```

### 4.3 运行测试

```bash
# API 测试
python test_api.py

# 多轮对话测试
python test_multi_turn.py
```

---

## 5. API 接口文档

### 5.1 消息接口

#### POST /api/message/send

发送消息并获取 AI 回复。

**请求体**:
```json
{
  "user_id": "user123",
  "message": "你好"
}
```

**响应**:
```json
{
  "ok": true,
  "reply": "你好！...",
  "session_id": "uuid",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

#### POST /api/message/batch

批量发送多条消息。

**请求体**:
```json
{
  "user_id": "user123",
  "messages": [
    {"content": "第一条"},
    {"content": "第二条"}
  ]
}
```

#### POST /api/message/stream

流式输出（SSE）。

**请求体**:
```json
{
  "user_id": "user123",
  "message": "你好"
}
```

**响应**: `text/event-stream` 格式

### 5.2 会话管理接口

#### GET /api/session/{session_id}

获取会话详情。

**响应**:
```json
{
  "ok": true,
  "session": {
    "session_id": "uuid",
    "user_id": "user123",
    "session_key": "user:user123:uuid",
    "message_count": 10,
    "created_at": "2026-03-04T10:00:00",
    "last_active": "2026-03-04T10:30:00"
  }
}
```

#### GET /api/session/{session_id}/history

获取会话历史。

**查询参数**:
- `limit`: 返回消息数量（默认 20）

**响应**:
```json
{
  "ok": true,
  "messages": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！"}
  ]
}
```

#### POST /api/session/{session_id}/clear

清除会话历史。

**响应**:
```json
{"ok": true}
```

#### DELETE /api/session/{session_id}

删除会话。

**响应**:
```json
{"ok": true}
```

#### GET /api/sessions

列出所有活跃会话。

**查询参数**:
- `user_id`: 过滤特定用户（可选）

**响应**:
```json
{
  "ok": true,
  "sessions": [...],
  "stats": {
    "total_sessions": 5,
    "active_sessions": 3,
    "unique_users": 3
  }
}
```

### 5.3 工具调用接口

#### POST /api/tools/invoke

调用 OpenClaw 工具。

**请求体**:
```json
{
  "user_id": "user123",
  "tool": "browser_navigate",
  "args": {"url": "https://example.com"},
  "action": "json"
}
```

**响应**:
```json
{
  "ok": true,
  "result": {...}
}
```

### 5.4 Webhook 接口

#### POST /api/webhook/trigger

触发 Webhook 任务。

**请求体**:
```json
{
  "message": "Summarize this...",
  "user_id": "user123",
  "name": "My Task",
  "deliver": false
}
```

#### POST /api/webhook/wake

唤醒 Agent 处理事件。

**请求体**:
```json
{
  "text": "New event occurred",
  "mode": "now"
}
```

### 5.5 系统接口

#### GET /api/health

健康检查。

**响应**:
```json
{
  "ok": true,
  "openclaw_connected": true,
  "sessions": {
    "active_sessions": 3,
    "unique_users": 3
  }
}
```

#### GET /api/stats

获取统计信息。

---

## 6. 会话管理

### 6.1 会话生命周期

```
创建 → 活跃 → 过期 → 清除
  │      │       │       │
  用户   持续    30 分钟   自动/
  发送   交互    无活动   手动
  消息
```

### 6.2 会话隔离

- 每个 `user_id` 拥有独立的会话
- 不同用户的会话完全隔离
- 支持同一用户多个并发会话

### 6.3 历史消息管理

**配置项**:
```bash
# .env 文件
MAX_HISTORY_MESSAGES=20  # 保留最近 N 条消息
SESSION_TIMEOUT_MINUTES=30  # 超时时间（分钟）
```

### 6.4 会话键映射

Flask 会话自动映射到 OpenClaw 会话键：
```
user_id: user123
  ↓
session_key: user:user123:8 位 uuid
```

---

## 7. 开发指南

### 7.1 添加新 API 端点

**步骤 1**: 在 `app.py` 中添加路由

```python
@app.route('/api/custom', methods=['POST'])
def custom_endpoint():
    data = request.json
    user_id = data.get('user_id')

    # 获取会话
    session = session_manager.get_or_create_session(user_id)

    # 调用 OpenClaw
    response = openclaw_client.chat(
        messages=[{"role": "user", "content": "自定义逻辑"}],
        session_key=session.session_key
    )

    return jsonify({"ok": True, "data": response.content})
```

### 7.2 自定义 OpenClaw 客户端

继承 `OpenClawClient` 类添加新方法：

```python
# openclaw_client.py
class OpenClawClient:
    # ... 现有代码 ...

    def custom_method(self, param):
        response = self.session.post(
            f"{self.base_url}/custom",
            headers=self._get_chat_headers(),
            json={"param": param}
        )
        return response.json()
```

### 7.3 中间件示例

**日志中间件**:
```python
@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path}")
    logger.info(f"Request data: {request.json}")

@app.after_request
def log_response(response):
    logger.info(f"Response: {response.status_code}")
    return response
```

**认证中间件**:
```python
@app.before_request
def check_api_key():
    if request.path.startswith('/api/'):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return jsonify({"error": "Unauthorized"}), 401
```

### 7.4 错误处理

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(requests.exceptions.RequestException)
def openclaw_error(error):
    logger.error(f"OpenClaw error: {error}")
    return jsonify({"error": "AI service unavailable"}), 503
```

---

## 8. 常见问题

### 8.1 启动问题

**Q: Flask 启动后无法访问**
```
A: 检查端口占用
   netstat -ano | findstr :5000
   或修改 app.py 中的端口
```

**Q: OpenClaw 返回 500 错误**
```
A: 检查 Gateway 是否运行
   openclaw gateway status
   检查 token 是否正确
```

### 8.2 会话问题

**Q: 多轮对话没有上下文**
```
A: 确保使用相同的 user_id
   检查 MAX_HISTORY_MESSAGES 配置
```

**Q: 会话丢失**
```
A: 检查 SESSION_TIMEOUT_MINUTES 配置
   会话 30 分钟无活动会自动过期
```

### 8.3 性能优化

**Q: 响应速度慢**
```
A: 1. 检查 OpenClaw 模型响应时间
   2. 启用流式输出 /api/message/stream
   3. 减少 MAX_HISTORY_MESSAGES 数量
```

**Q: 内存占用高**
```
A: 1. 定期清理过期会话
   2. 减少历史消息数量
   3. 使用 POST /api/sessions/cleanup
```

---

## 9. 附录

### 9.1 配置文件模板

**~/.openclaw/openclaw.json**:
```json
{
  "gateway": {
    "port": 18789,
    "bind": "loopback",
    "auth": {"mode": "token", "token": "your-token"},
    "http": {
      "endpoints": {
        "chatCompletions": {"enabled": true},
        "responses": {"enabled": true}
      }
    }
  },
  "hooks": {
    "enabled": true,
    "token": "your-webhook-token",
    "allowRequestSessionKey": true,
    "allowedSessionKeyPrefixes": ["webhook:", "flask:", "user:"]
  }
}
```

**flask/.env**:
```bash
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_GATEWAY_TOKEN=your-token
OPENCLAW_WEBHOOK_TOKEN=your-webhook-token
SECRET_KEY=your-secret-key
SESSION_TIMEOUT_MINUTES=30
MAX_HISTORY_MESSAGES=20
LOG_LEVEL=INFO
LOG_FILE=flask_openclaw.log
```

### 9.2 依赖列表

**requirements.txt**:
```
Flask==3.0.0
requests==2.31.0
python-dotenv>=1.0.1
```

### 9.3 相关资源

- [OpenClaw 官方文档](https://openclaw.ai)
- [Flask 官方文档](https://flask.palletsprojects.com/)
- [Requests 库文档](https://requests.readthedocs.io/)

---

**文档结束**
