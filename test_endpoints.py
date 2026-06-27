import requests
import json

print("Testing /chats POST...")
try:
    res = requests.post("http://localhost:8000/chats", json={"email": "test@test.com"})
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Error:", e)
