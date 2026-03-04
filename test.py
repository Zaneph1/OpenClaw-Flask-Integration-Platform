import requests

BASE_URL = "http://localhost:5000"

# 第一轮对话
response1 = requests.post(
    f"{BASE_URL}/api/message/send",
    json={"user_id": "user123", "message": "你好，我叫小明"}
)
print("回复 1:", response1.json()["reply"])

# 第二轮对话（系统会自动记住上下文）
response2 = requests.post(
    f"{BASE_URL}/api/message/send",
    json={"user_id": "user123", "message": "我叫什么名字？"}
)
print("回复 2:", response2.json()["reply"])

# 第三轮对话
response3 = requests.post(
    f"{BASE_URL}/api/message/send",
    json={"user_id": "user123", "message": "你能帮我做什么？"}
)
print("回复 3:", response3.json()["reply"])