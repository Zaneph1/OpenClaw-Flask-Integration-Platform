"""
会话管理器 - 管理用户与 OpenClaw 的对话会话
类似飞书的会话管理功能
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import threading


@dataclass
class Message:
    """消息对象"""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Session:
    """会话对象"""
    session_id: str
    user_id: str
    session_key: str  # OpenClaw 会话键
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class SessionManager:
    """
    会话管理器

    功能:
    - 自动创建/管理用户会话
    - 消息历史记录
    - 会话过期清理
    - 多用户隔离
    """

    def __init__(self, timeout_minutes: int = 30, max_history: int = 20):
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.timeout_minutes = timeout_minutes
        self.max_history = max_history
        self._lock = threading.RLock()

    def get_or_create_session(self, user_id: str) -> Session:
        """获取或创建用户会话"""
        with self._lock:
            # 检查用户是否已有活跃会话
            if user_id in self.user_sessions:
                session_id = self.user_sessions[user_id]
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    # 检查是否过期
                    if datetime.now() - session.last_active < timedelta(minutes=self.timeout_minutes):
                        return session
                    else:
                        # 过期了，创建新会话
                        del self.sessions[session_id]

            # 创建新会话
            session_id = str(uuid.uuid4())
            session_key = f"user:{user_id}:{session_id[:8]}"
            session = Session(
                session_id=session_id,
                user_id=user_id,
                session_key=session_key
            )
            self.sessions[session_id] = session
            self.user_sessions[user_id] = session_id
            return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and datetime.now() - session.last_active < timedelta(minutes=self.timeout_minutes):
                return session
            return None

    def add_message(self, session_id: str, role: str, content: str) -> Message:
        """添加消息到会话"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            message = Message(role=role, content=content)
            session.messages.append(message)
            session.last_active = datetime.now()

            # 限制历史记录数量
            if len(session.messages) > self.max_history:
                session.messages = session.messages[-self.max_history:]

            return message

    def get_messages(self, session_id: str, limit: int = 10) -> List[Dict]:
        """获取会话历史消息（用于发送给 OpenClaw）"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return []

            messages = session.messages[-limit:]
            return [{"role": m.role, "content": m.content} for m in messages]

    def get_all_messages(self, session_id: str) -> List[Message]:
        """获取所有消息对象"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return []
            return session.messages.copy()

    def clear_session(self, session_id: str) -> bool:
        """清除会话历史"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.messages = []
                session.last_active = datetime.now()
                return True
            return False

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        with self._lock:
            session = self.sessions.pop(session_id, None)
            if session:
                self.user_sessions.pop(session.user_id, None)
                return True
            return False

    def list_sessions(self) -> List[Dict]:
        """列出所有活跃会话"""
        with self._lock:
            now = datetime.now()
            active_sessions = []
            for session in self.sessions.values():
                if now - session.last_active < timedelta(minutes=self.timeout_minutes):
                    active_sessions.append({
                        "session_id": session.session_id,
                        "user_id": session.user_id,
                        "session_key": session.session_key,
                        "message_count": len(session.messages),
                        "last_active": session.last_active.isoformat()
                    })
            return active_sessions

    def cleanup_expired(self) -> int:
        """清理过期会话"""
        with self._lock:
            expired = []
            now = datetime.now()
            for session_id, session in self.sessions.items():
                if now - session.last_active > timedelta(minutes=self.timeout_minutes):
                    expired.append(session_id)

            for session_id in expired:
                self.delete_session(session_id)

        return len(expired)

    def get_stats(self) -> Dict:
        """获取会话统计"""
        with self._lock:
            now = datetime.now()
            active_count = sum(
                1 for s in self.sessions.values()
                if now - s.last_active < timedelta(minutes=self.timeout_minutes)
            )
            return {
                "total_sessions": len(self.sessions),
                "active_sessions": active_count,
                "unique_users": len(self.user_sessions)
            }
