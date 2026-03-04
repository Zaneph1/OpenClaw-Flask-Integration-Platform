"""
Flask AI 集成平台 - 类似飞书通道功能
与 OpenClaw Gateway 集成，提供会话管理和消息处理

API 端点:
- POST /api/message/send      - 发送消息并获取回复
- POST /api/message/batch     - 批量发送消息
- POST /api/message/stream    - 流式输出 (SSE)
- GET  /api/session/<id>      - 获取会话详情
- GET  /api/session/<id>/history - 获取会话历史
- POST /api/session/<id>/clear   - 清除会话历史
- DELETE /api/session/<id>       - 删除会话
- GET  /api/sessions          - 列出所有会话
- POST /api/tools/invoke      - 调用工具
- POST /api/webhook/trigger   - 触发 Webhook
- GET  /api/health            - 健康检查
"""
from flask import Flask, request, jsonify, Response
from session_manager import SessionManager
from openclaw_client import OpenClawClient
from config import (
    SESSION_TIMEOUT_MINUTES,
    MAX_HISTORY_MESSAGES,
    LOG_LEVEL,
    LOG_FILE
)
from dotenv import load_dotenv
import logging
import json

# 加载 .env 文件
load_dotenv()

# ==================== 日志配置 ====================
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 初始化 Flask 应用 ====================
app = Flask(__name__)

# 初始化会话管理器
session_manager = SessionManager(
    timeout_minutes=SESSION_TIMEOUT_MINUTES,
    max_history=MAX_HISTORY_MESSAGES
)

# 初始化 OpenClaw 客户端
openclaw_client = OpenClawClient()


# ==================== 消息接口 ====================

@app.route('/api/message/send', methods=['POST'])
def send_message():
    """
    发送消息到 OpenClaw 并获取回复
    类似飞书的发送消息功能

    Request Body:
        {
            "user_id": "user123",      # 用户 ID (必需)
            "message": "你好"            # 消息内容 (必需)
        }

    Response:
        {
            "ok": true,
            "reply": "你好！有什么可以帮你...",
            "session_id": "xxx",
            "usage": {...}
        }
    """
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')

    if not user_id or not message:
        return jsonify({"error": "user_id and message are required"}), 400

    try:
        # 获取或创建会话
        session = session_manager.get_or_create_session(user_id)

        # 添加用户消息
        session_manager.add_message(session.session_id, "user", message)

        # 获取历史消息
        messages = session_manager.get_messages(session.session_id, limit=10)

        # 调用 OpenClaw
        response = openclaw_client.chat(
            messages=messages,
            session_key=session.session_key
        )

        # 添加助手回复
        session_manager.add_message(session.session_id, "assistant", response.content)

        logger.info(f"User {user_id} sent: {message[:50]}...")

        return jsonify({
            "ok": True,
            "reply": response.content,
            "session_id": session.session_id,
            "usage": response.usage
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/message/batch', methods=['POST'])
def batch_messages():
    """
    批量发送多条消息

    Request Body:
        {
            "user_id": "user123",
            "messages": [
                {"content": "第一条消息"},
                {"content": "第二条消息"}
            ]
        }
    """
    data = request.json
    user_id = data.get('user_id')
    messages = data.get('messages', [])

    if not user_id or not messages:
        return jsonify({"error": "user_id and messages are required"}), 400

    try:
        session = session_manager.get_or_create_session(user_id)

        # 添加所有用户消息
        for msg in messages:
            session_manager.add_message(
                session.session_id,
                "user",
                msg.get('content', '')
            )

        # 获取历史消息
        history = session_manager.get_messages(session.session_id, limit=15)

        # 调用 OpenClaw
        response = openclaw_client.chat(
            messages=history,
            session_key=session.session_key
        )

        session_manager.add_message(
            session.session_id,
            "assistant",
            response.content
        )

        return jsonify({
            "ok": True,
            "reply": response.content,
            "session_id": session.session_id
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/message/stream', methods=['POST'])
def stream_message():
    """
    流式发送消息 (SSE 输出)

    Request Body:
        {
            "user_id": "user123",
            "message": "你好"
        }

    Response: SSE stream
    """
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')

    if not user_id or not message:
        return jsonify({"error": "user_id and message are required"}), 400

    def generate():
        try:
            session = session_manager.get_or_create_session(user_id)
            session_manager.add_message(session.session_id, "user", message)
            messages = session_manager.get_messages(session.session_id, limit=10)

            # 使用流式 API
            for chunk in openclaw_client.chat_stream(
                messages=messages,
                session_key=session.session_key
            ):
                if chunk.startswith('data: '):
                    yield f"{chunk}\n\n"
                else:
                    yield f"data: {chunk}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


# ==================== 会话管理接口 ====================

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    获取会话详情
    """
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({
        "ok": True,
        "session": {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_key": session.session_key,
            "message_count": len(session.messages),
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat()
        }
    })


@app.route('/api/session/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """
    获取会话历史

    Query Params:
        limit: 返回消息数量 (默认 20)
    """
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    limit = request.args.get('limit', 20, type=int)
    messages = session_manager.get_messages(session_id, limit=limit)

    return jsonify({
        "ok": True,
        "messages": messages
    })


@app.route('/api/session/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    """
    获取会话所有消息对象（包含元数据）
    """
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    messages = session_manager.get_all_messages(session_id)
    return jsonify({
        "ok": True,
        "messages": [
            {
                "message_id": m.message_id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]
    })


@app.route('/api/session/<session_id>/clear', methods=['POST'])
def clear_session(session_id):
    """
    清除会话历史
    """
    success = session_manager.clear_session(session_id)
    return jsonify({"ok": success})


@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    删除会话
    """
    success = session_manager.delete_session(session_id)
    return jsonify({"ok": success})


@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """
    列出所有活跃会话

    Query Params:
        user_id: 过滤特定用户 (可选)
    """
    user_id = request.args.get('user_id')

    if user_id:
        # 过滤特定用户的会话
        sessions = [
            s for s in session_manager.list_sessions()
            if s['user_id'] == user_id
        ]
    else:
        sessions = session_manager.list_sessions()

    return jsonify({
        "ok": True,
        "sessions": sessions,
        "stats": session_manager.get_stats()
    })


@app.route('/api/sessions/cleanup', methods=['POST'])
def cleanup_sessions():
    """
    清理过期会话
    """
    count = session_manager.cleanup_expired()
    return jsonify({
        "ok": True,
        "cleaned": count
    })


# ==================== 工具调用接口 ====================

@app.route('/api/tools/invoke', methods=['POST'])
def invoke_tool():
    """
    调用 OpenClaw 工具

    Request Body:
        {
            "user_id": "user123",        # 用户 ID (可选)
            "tool": "browser_navigate",  # 工具名称 (必需)
            "args": {"url": "xxx"},      # 工具参数 (可选)
            "action": "json"             # 工具动作 (可选)
        }
    """
    data = request.json
    tool = data.get('tool')
    args = data.get('args', {})
    user_id = data.get('user_id')
    action = data.get('action')

    if not tool:
        return jsonify({"error": "tool is required"}), 400

    try:
        session_key = None
        if user_id:
            session = session_manager.get_or_create_session(user_id)
            session_key = session.session_key

        result = openclaw_client.invoke_tool(
            tool=tool,
            args=args,
            session_key=session_key,
            action=action
        )

        return jsonify({
            "ok": True,
            "result": result
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tools/list', methods=['GET'])
def list_tools():
    """
    列出可用工具 (通过 sessions_list 间接获取)
    """
    try:
        # 获取工具列表需要调用 Gateway
        # 这里返回一个示例响应
        return jsonify({
            "ok": True,
            "tools": [
                "browser_navigate",
                "browser_click",
                "file_read",
                "file_write",
                "shell",
                "sessions_list",
                "sessions_send"
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== Webhook 接口 ====================

@app.route('/api/webhook/trigger', methods=['POST'])
def trigger_webhook():
    """
    触发 OpenClaw Webhook 任务

    Request Body:
        {
            "message": "Summarize this...",  # 消息内容 (必需)
            "user_id": "user123",            # 用户 ID (可选)
            "name": "My Task",               # 任务名称 (可选)
            "agent_id": "main",              # 指定 agent (可选)
            "deliver": false                 # 是否发送到频道 (可选)
        }
    """
    data = request.json
    message = data.get('message')
    user_id = data.get('user_id')
    task_name = data.get('name', 'Flask Task')
    agent_id = data.get('agent_id')
    deliver = data.get('deliver', False)

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        session = session_manager.get_or_create_session(user_id) if user_id else None
        session_key = session.session_key if session else f"webhook:{task_name}"

        result = openclaw_client.trigger_webhook(
            message=message,
            session_key=session_key,
            name=task_name,
            agent_id=agent_id,
            deliver=deliver
        )

        return jsonify({
            "ok": True,
            **result
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/webhook/wake', methods=['POST'])
def wake_agent():
    """
    唤醒 agent 处理事件

    Request Body:
        {
            "text": "New event occurred",  # 事件描述 (必需)
            "mode": "now"                  # 模式 (now | next-heartbeat)
        }
    """
    data = request.json
    text = data.get('text')
    mode = data.get('mode', 'now')

    if not text:
        return jsonify({"error": "text is required"}), 400

    try:
        result = openclaw_client.wake_agent(text=text, mode=mode)
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== 系统接口 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查
    """
    openclaw_status = openclaw_client.health_check()
    session_stats = session_manager.get_stats()

    return jsonify({
        "ok": True,
        "openclaw_connected": openclaw_status,
        "sessions": session_stats
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    获取统计信息
    """
    return jsonify({
        "ok": True,
        "sessions": session_manager.get_stats()
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """
    获取当前配置 (不包含敏感信息)
    """
    from config import (
        OPENCLAW_BASE_URL,
        SESSION_TIMEOUT_MINUTES,
        MAX_HISTORY_MESSAGES
    )
    return jsonify({
        "ok": True,
        "config": {
            "openclaw_base_url": OPENCLAW_BASE_URL,
            "session_timeout_minutes": SESSION_TIMEOUT_MINUTES,
            "max_history_messages": MAX_HISTORY_MESSAGES
        }
    })


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


# ==================== 主入口 ====================

if __name__ == '__main__':
    logger.info("Starting Flask OpenClaw Integration Platform...")
    logger.info(f"OpenClaw Base URL: http://127.0.0.1:18789")
    app.run(debug=True, port=5000, host='0.0.0.0')

