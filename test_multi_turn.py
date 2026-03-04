#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多轮对话测试脚本
"""
import sys
import requests

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:5000"

def multi_turn_conversation():
    """测试多轮对话"""
    user_id = "multi_turn_test"

    print("=" * 60)
    print("多轮对话测试")
    print("=" * 60)
    print()

    # 对话列表
    conversation = [
        "介绍一下怎么学python"

    ]

    session_id = None

    for i, message in enumerate(conversation, 1):
        print(f"[第 {i} 轮] 用户：{message}")

        response = requests.post(
            f"{BASE_URL}/api/message/send",
            json={"user_id": user_id, "message": message},
            timeout=60
        )

        data = response.json()
        if data.get("ok"):
            if not session_id:
                session_id = data["session_id"]
                print(f"       会话 ID: {session_id}")

            reply = data.get("reply", "无回复")
            # 截取前 150 个字符显示
            if len(reply) > 150:
                reply = reply[:150] + "..."
            print(f"       助手：{reply}")
        else:
            print(f"       错误：{data.get('error')}")

        print()

    # 查看完整历史
    print("=" * 60)
    print("查看完整对话历史")
    print("=" * 60)

    if session_id:
        history_response = requests.get(
            f"{BASE_URL}/api/session/{session_id}/history"
        )
        history = history_response.json()

        for msg in history.get("messages", []):
            role = "用户" if msg["role"] == "user" else "助手"
            content = msg["content"]
            if len(content) > 80:
                content = content[:80] + "..."
            print(f"  {role}: {content}")

    print()
    print("=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        multi_turn_conversation()
    except Exception as e:
        print(f"测试失败：{e}")
        print("请确保 Flask 应用正在运行：python app.py")
