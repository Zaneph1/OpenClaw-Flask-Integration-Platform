#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask OpenClaw 集成平台 - 测试脚本
"""
import sys
import requests
import json

BASE_URL = "http://localhost:5000"

def test_send_message():
    """测试发送消息"""
    print("=" * 50)
    print("测试：发送消息")
    print("=" * 50)

    response = requests.post(
        f"{BASE_URL}/api/message/send",
        json={"user_id": "test_user", "message": "你好，我是测试用户"},
        timeout=30
    )

    result = response.json()
    print(f"状态：{result.get('ok')}")
    print(f"会话 ID: {result.get('session_id')}")
    print(f"回复：{result.get('reply')[:200]}...")
    print()

    return result.get('session_id')

def test_get_history(session_id):
    """测试获取会话历史"""
    print("=" * 50)
    print("测试：获取会话历史")
    print("=" * 50)

    response = requests.get(
        f"{BASE_URL}/api/session/{session_id}/history",
        timeout=10
    )

    result = response.json()
    print(f"消息数量：{len(result.get('messages', []))}")
    for msg in result.get('messages', []):
        print(f"  - {msg['role']}: {msg['content'][:50]}...")
    print()

def test_tool_invoke():
    """测试工具调用"""
    print("=" * 50)
    print("测试：调用工具 (sessions_list)")
    print("=" * 50)

    response = requests.post(
        f"{BASE_URL}/api/tools/invoke",
        json={"user_id": "test_user", "tool": "sessions_list", "args": {}},
        timeout=30
    )

    result = response.json()
    print(f"状态：{result.get('ok')}")
    print(f"结果：{str(result.get('result'))[:200]}...")
    print()

def test_health():
    """测试健康检查"""
    print("=" * 50)
    print("测试：健康检查")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/api/health", timeout=10)
    result = response.json()
    print(f"OpenClaw 连接：{result.get('openclaw_connected')}")
    print(f"会话统计：{result.get('sessions')}")
    print()

def main():
    """主测试流程"""
    print("\nOpenClaw Flask 集成平台 - 测试套件 (Python)\n")
    print("System encoding:", sys.getdefaultencoding())

    try:
        # 1. 健康检查
        test_health()

        # 2. 发送消息
        session_id = test_send_message()

        # 3. 获取历史
        if session_id:
            test_get_history(session_id)

        # 4. 工具调用
        test_tool_invoke()

        print("=" * 50)
        print("✅ 所有测试完成!")
        print("=" * 50)

    except Exception as e:
        print(f"❌ 测试失败：{e}")

if __name__ == "__main__":
    main()
