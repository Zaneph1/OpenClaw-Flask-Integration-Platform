# OpenClaw Flask 集成平台

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🤖 为 OpenClaw 打造的 Flask AI 集成中间件，类似飞书通道功能，让任何应用快速拥有智能对话能力

---

## ✨ 特性

- **🔄 多轮对话** - 自动会话管理，支持上下文感知的连续对话
- **👥 多用户隔离** - 每个用户独立会话，互不干扰
- **🛠️ 工具调用** - 支持调用 OpenClaw 的所有工具（文件操作、浏览器控制等）
- **📡 Webhook 支持** - 外部事件触发 AI 任务
- **🔌 简单易用** - RESTful API，几行代码即可集成
- **📦 开箱即用** - 自动配置脚本，5 分钟快速启动

---

## 🚀 快速开始

### 前置要求

- Python 3.13+
- OpenClaw Gateway

### 1. 安装依赖

```bash
cd flask
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 配置已自动生成，检查 .env 文件
# 如需修改，编辑 .env 文件中的配置项
```

### 3. 启动服务

```bash
# 终端 1: 启动 OpenClaw Gateway
openclaw gateway

# 终端 2: 启动 Flask 应用
python app.py
```

### 4. 测试 API

```bash
curl -X POST http://localhost:5000/api/message/send \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "你好"}'
```

---

## 📖 API 概览

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/message/send` | POST | 发送消息获取回复 |
| `/api/message/batch` | POST | 批量发送消息 |
| `/api/message/stream` | POST | 流式输出 (SSE) |
| `/api/session/{id}` | GET | 获取会话详情 |
| `/api/session/{id}/history` | GET | 获取会话历史 |
| `/api/session/{id}/clear` | POST | 清除会话 |
| `/api/sessions` | GET | 列出所有会话 |
| `/api/tools/invoke` | POST | 调用工具 |
| `/api/webhook/trigger` | POST | 触发 Webhook |
| `/api/health` | GET | 健康检查 |

---

## 💡 使用示例

### 简单对话

```python
import requests

BASE_URL = "http://localhost:5000"

# 发送消息
response = requests.post(
    f"{BASE_URL}/api/message/send",
    json={"user_id": "user1", "message": "你好，我想学习 Python"}
)

print(response.json()["reply"])
```

### 多轮对话

```python
# 第一轮
requests.post(f"{BASE_URL}/api/message/send",
    json={"user_id": "user1", "message": "我叫小明"})

# 第二轮 - AI 会记住上下文
response = requests.post(f"{BASE_URL}/api/message/send",
    json={"user_id": "user1", "message": "我叫什么名字？"})

# 回复会提到"小明"
print(response.json()["reply"])
```

### 调用工具

```python
# 列出所有会话
response = requests.post(f"{BASE_URL}/api/tools/invoke",
    json={"tool": "sessions_list", "args": {}})

print(response.json()["result"])
```

---

## 📁 项目结构

```
flask/
├── app.py                 # Flask 主应用
├── config.py              # 配置管理
├── session_manager.py     # 会话管理器
├── openclaw_client.py     # OpenClaw API 客户端
├── requirements.txt       # Python 依赖
├── .env                   # 环境变量配置
├── test_api.py            # API 测试脚本
├── test_multi_turn.py     # 多轮对话测试
├── DEVELOPMENT.md         # 开发文档
└── README.md              # 本文件
```

---

## ⚙️ 配置说明

### 环境变量 (.env)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENCLAW_BASE_URL` | OpenClaw 地址 | `http://127.0.0.1:18789` |
| `OPENCLAW_GATEWAY_TOKEN` | Gateway 认证 Token | (自动生成) |
| `OPENCLAW_WEBHOOK_TOKEN` | Webhook 认证 Token | (自动生成) |
| `SESSION_TIMEOUT_MINUTES` | 会话超时时间 | `30` |
| `MAX_HISTORY_MESSAGES` | 历史消息数量 | `20` |

---

## 🧪 运行测试

```bash
# API 测试
python test_api.py

# 多轮对话测试
python test_multi_turn.py
```

---

## 📚 文档

- **[开发文档](DEVELOPMENT.md)** - 完整的 API 文档和开发指南
- **[OpenClaw 文档](https://openclaw.ai)** - OpenClaw 官方文档

---

## 🔧 常见问题

### Q: 多轮对话没有上下文？
确保使用相同的 `user_id`，系统会自动维护会话历史。

### Q: 如何清除对话历史？
```python
requests.post(f"{BASE_URL}/api/session/{session_id}/clear")
```

### Q: OpenClaw 返回 500 错误？
检查 Gateway 是否运行：`openclaw gateway status`

---

## 📝 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [OpenClaw](https://openclaw.ai) - 强大的 AI 自动化框架
- [Flask](https://flask.palletsprojects.com/) - 轻量级 Python Web 框架

---

<div align="center">

**🤖 让 AI 为你的应用赋能！**

[开始使用](#-快速开始) · [查看文档](DEVELOPMENT.md) · [报告问题](../../issues)

</div>
