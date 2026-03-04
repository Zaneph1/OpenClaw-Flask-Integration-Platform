# OpenClaw Flask Integration Platform

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🤖 A Flask AI integration middleware for OpenClaw, similar to Feishu channel functionality, enabling any application with intelligent conversation capabilities

---

## ✨ Features

- **🔄 Multi-turn Conversations** - Automatic session management with context-aware continuous dialogue
- **👥 Multi-user Isolation** - Independent sessions per user, completely isolated
- **🛠️ Tool Invocation** - Support for all OpenClaw tools (file operations, browser control, etc.)
- **📡 Webhook Support** - Trigger AI tasks from external events
- **🔌 Easy Integration** - RESTful API, integrate with just a few lines of code
- **📦 Out-of-the-Box** - Auto-configuration script, up and running in 5 minutes

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- OpenClaw Gateway

### 1. Install Dependencies

```bash
cd flask
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Configuration is auto-generated, check the .env file
# Edit .env to modify settings if needed
```

### 3. Start Services

```bash
# Terminal 1: Start OpenClaw Gateway
openclaw gateway

# Terminal 2: Start Flask Application
python app.py
```

### 4. Test the API

```bash
curl -X POST http://localhost:5000/api/message/send \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Hello"}'
```

---

## 📖 API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/message/send` | POST | Send message and get reply |
| `/api/message/batch` | POST | Send multiple messages |
| `/api/message/stream` | POST | Stream output (SSE) |
| `/api/session/{id}` | GET | Get session details |
| `/api/session/{id}/history` | GET | Get session history |
| `/api/session/{id}/clear` | POST | Clear session |
| `/api/sessions` | GET | List all sessions |
| `/api/tools/invoke` | POST | Invoke OpenClaw tool |
| `/api/webhook/trigger` | POST | Trigger webhook task |
| `/api/health` | GET | Health check |

---

## 💡 Usage Examples

### Simple Chat

```python
import requests

BASE_URL = "http://localhost:5000"

# Send a message
response = requests.post(
    f"{BASE_URL}/api/message/send",
    json={"user_id": "user1", "message": "Hello, I want to learn Python"}
)

print(response.json()["reply"])
```

### Multi-turn Conversation

```python
# First turn
requests.post(f"{BASE_URL}/api/message/send",
    json={"user_id": "user1", "message": "My name is John"})

# Second turn - AI remembers context
response = requests.post(f"{BASE_URL}/api/message/send",
    json={"user_id": "user1", "message": "What is my name?"})

# Reply will mention "John"
print(response.json()["reply"])
```

### Invoke Tool

```python
# List all sessions
response = requests.post(f"{BASE_URL}/api/tools/invoke",
    json={"tool": "sessions_list", "args": {}})

print(response.json()["result"])
```

---

## 📁 Project Structure

```
flask/
├── app.py                 # Flask main application
├── config.py              # Configuration management
├── session_manager.py     # Session manager
├── openclaw_client.py     # OpenClaw API client
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
├── test_api.py            # API test script
├── test_multi_turn.py     # Multi-turn conversation test
├── DEVELOPMENT.md         # Development documentation
└── README.md              # This file
```

---

## ⚙️ Configuration

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENCLAW_BASE_URL` | OpenClaw address | `http://127.0.0.1:18789` |
| `OPENCLAW_GATEWAY_TOKEN` | Gateway auth token | (auto-generated) |
| `OPENCLAW_WEBHOOK_TOKEN` | Webhook auth token | (auto-generated) |
| `SESSION_TIMEOUT_MINUTES` | Session timeout | `30` |
| `MAX_HISTORY_MESSAGES` | History message count | `20` |

---

## 🧪 Running Tests

```bash
# API tests
python test_api.py

# Multi-turn conversation test
python test_multi_turn.py
```

---

## 📚 Documentation

- **[Development Documentation](DEVELOPMENT.md)** - Complete API docs and development guide
- **[OpenClaw Documentation](https://openclaw.ai)** - Official OpenClaw docs

---

## 🔧 Troubleshooting

### Q: Multi-turn conversation has no context?
Ensure you're using the same `user_id`. The system automatically maintains session history.

### Q: How to clear conversation history?
```python
requests.post(f"{BASE_URL}/api/session/{session_id}/clear")
```

### Q: OpenClaw returns 500 error?
Check if Gateway is running: `openclaw gateway status`

### Q: Connection refused?
Make sure both OpenClaw Gateway and Flask app are running:
```bash
# Check Gateway
openclaw gateway status

# Check Flask (port 5000)
netstat -ano | findstr :5000
```

---

## 🔐 Security Notes

- Keep your `OPENCLAW_GATEWAY_TOKEN` and `OPENCLAW_WEBHOOK_TOKEN` secure
- Do not commit `.env` file to version control
- Use HTTPS in production environments
- Implement rate limiting for production use

---

## 🚀 Production Deployment

For production deployment, consider:

1. **Use a production WSGI server** (Gunicorn/uWSGI):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set up a reverse proxy** (Nginx/Caddy)

3. **Enable authentication** for API endpoints

4. **Configure logging** to a centralized system

5. **Set up monitoring** for health endpoints

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- [OpenClaw](https://openclaw.ai) - Powerful AI automation framework
- [Flask](https://flask.palletsprojects.com/) - Lightweight Python web framework

---

<div align="center">

**🤖 Empower your application with AI!**

[Get Started](#-quick-start) · [View Documentation](DEVELOPMENT.md) · [Report Issues](../../issues)

</div>
