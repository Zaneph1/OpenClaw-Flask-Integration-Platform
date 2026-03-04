"""
OpenClaw HTTP 客户端 - 封装与 OpenClaw Gateway 的交互
"""
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from config import (
    OPENCLAW_BASE_URL,
    OPENCLAW_GATEWAY_TOKEN,
    OPENCLAW_WEBHOOK_TOKEN
)


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    session_key: str
    usage: Optional[Dict] = None
    model: Optional[str] = None


class OpenClawClient:
    """
    OpenClaw HTTP 客户端

    功能:
    - 聊天对话 (Chat Completions API)
    - 工具调用 (Tools Invoke API)
    - Webhook 触发
    - 健康检查
    """

    def __init__(
        self,
        base_url: str = None,
        gateway_token: str = None,
        webhook_token: str = None
    ):
        self.base_url = base_url or OPENCLAW_BASE_URL
        self.gateway_token = gateway_token or OPENCLAW_GATEWAY_TOKEN
        self.webhook_token = webhook_token or OPENCLAW_WEBHOOK_TOKEN
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def _get_chat_headers(self) -> Dict:
        """获取聊天 API 的 headers"""
        return {
            'Authorization': f'Bearer {self.gateway_token}'
        }

    def _get_webhook_headers(self) -> Dict:
        """获取 Webhook API 的 headers"""
        return {
            'Authorization': f'Bearer {self.webhook_token}'
        }

    def chat(
        self,
        messages: List[Dict],
        session_key: str = None,
        model: str = None,
        stream: bool = False
    ) -> ChatResponse:
        """
        发送聊天请求到 OpenClaw

        Args:
            messages: 消息历史 [{"role": "user", "content": "你好"}, ...]
            session_key: OpenClaw 会话键 (用于会话路由)
            model: 模型名称 (如 "openclaw:main")
            stream: 是否使用流式输出

        Returns:
            ChatResponse: 聊天响应
        """
        payload = {
            "model": model or "openclaw:dev",
            "messages": messages,
            "stream": stream
        }

        if session_key:
            payload["user"] = session_key  # 用于会话路由

        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._get_chat_headers(),
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        return ChatResponse(
            content=result['choices'][0]['message']['content'],
            session_key=session_key or "default",
            usage=result.get('usage'),
            model=result.get('model')
        )

    def chat_stream(self, messages: List[Dict], session_key: str = None, model: str = None):
        """
        流式聊天（生成器）

        Args:
            messages: 消息历史
            session_key: 会话键
            model: 模型名称

        Yields:
            流式响应块
        """
        payload = {
            "model": model or "openclaw:dev",
            "messages": messages,
            "stream": True
        }

        if session_key:
            payload["user"] = session_key

        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._get_chat_headers(),
            json=payload,
            stream=True,
            timeout=120
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                yield line.decode('utf-8')

    def invoke_tool(
        self,
        tool: str,
        args: Dict,
        session_key: str = None,
        action: str = None
    ) -> Dict:
        """
        调用 OpenClaw 工具

        Args:
            tool: 工具名称 (如 "browser_navigate", "file_read")
            args: 工具参数
            session_key: 会话键
            action: 工具动作 (可选)

        Returns:
            工具执行结果
        """
        payload = {
            "tool": tool,
            "args": args
        }

        if action:
            payload["action"] = action

        if session_key:
            payload["sessionKey"] = session_key

        response = self.session.post(
            f"{self.base_url}/tools/invoke",
            headers=self._get_chat_headers(),
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        return result.get('result', {})

    def trigger_webhook(
        self,
        message: str,
        session_key: str,
        name: str = "Flask",
        agent_id: str = None,
        deliver: bool = False
    ) -> Dict:
        """
        触发 Webhook agent 运行

        Args:
            message: 消息内容/提示词
            session_key: 会话键
            name: 任务名称
            agent_id: 指定 agent (可选)
            deliver: 是否发送到聊天频道

        Returns:
            执行结果
        """
        payload = {
            "message": message,
            "name": name,
            "sessionKey": session_key,
            "wakeMode": "now",
            "deliver": deliver
        }

        if agent_id:
            payload["agentId"] = agent_id

        response = self.session.post(
            f"{self.base_url}/hooks/agent",
            headers=self._get_webhook_headers(),
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        return {"status": "started", "code": response.status_code}

    def wake_agent(self, text: str, mode: str = "now") -> Dict:
        """
        唤醒 agent 处理事件

        Args:
            text: 事件描述
            mode: 模式 (now | next-heartbeat)

        Returns:
            执行结果
        """
        payload = {
            "text": text,
            "mode": mode
        }

        response = self.session.post(
            f"{self.base_url}/hooks/wake",
            headers=self._get_webhook_headers(),
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        return {"status": "ok"}

    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                headers=self._get_chat_headers(),
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_session_info(self, session_key: str) -> Optional[Dict]:
        """
        获取会话信息（通过 tools/invoke 查询）

        Args:
            session_key: 会话键

        Returns:
            会话信息或 None
        """
        try:
            result = self.invoke_tool("sessions_list", {})
            return result.get(session_key)
        except Exception:
            return None
