import requests

response = requests.post("http://localhost:1234/v1/chat/completions", json={
    "model": "local-llm",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 200
})

print(response.json())