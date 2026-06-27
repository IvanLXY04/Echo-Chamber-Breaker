import requests
try:
    response = requests.post("http://localhost:8000/chat", json={"message": "hello", "persona": "Socratic"})
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(e)
