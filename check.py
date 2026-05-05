import requests

url = "https://chat-ai.academiccloud.de/v1/models"
headers = {"Authorization": f"Bearer 04f55d244af5c784f0b88b76d2a54581"}

response = requests.get(url, headers=headers)
print(response.json())