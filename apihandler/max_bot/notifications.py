from httpx import post
from django.conf import settings

def send_message(max_id: str, message: str):
    max_url = settings.MAX_API_BASE_URL
    token = settings.MAX_BOT_TOKEN

    response = post(f"{max_url}/messages", params = {"user_id": max_id}, headers = {"Authorization": token, "Content-Type": "application/json"}, json = {"text": message}, timeout = 10, verify=False)
    response.raise_for_status()

    return response.json()