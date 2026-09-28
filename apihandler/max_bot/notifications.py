from django.conf import settings
from apihandler.max_bot import client

def send_message(max_id: str, message: str):
    token = settings.MAX_BOT_TOKEN

    response = client.post(f"/messages", params = {"user_id": max_id}, headers = {"Authorization": token, "Content-Type": "application/json"}, json = {"text": message})
    response.raise_for_status()

    return response.json()