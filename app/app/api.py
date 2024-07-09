from ninja import NinjaAPI
from django.http import HttpResponse, JsonResponse
from dotenv import load_dotenv
import requests
import os
import json
import aiohttp

api = NinjaAPI()

load_dotenv()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("ACCESS_TOKEN")
VERSION = os.getenv("VERSION")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
API_URL = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"


@api.post("/webhook")
async def webhook(request):
    try:
        body_unicode = request.body.decode('utf-8')  # Decodificar el cuerpo a UTF-8
        print("Incoming webhook message:", json.dumps(body_unicode, indent=2))

        data = json.loads(body_unicode)
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]

        if message["type"] == "text":
            business_phone_number_id = data["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
            recipient_id = message["from"]
            message_text = message["text"]["body"]
            message_id = message["id"]

            # Send reply message
            await send_reply_message(business_phone_number_id, recipient_id, message_text, message_id)

            # Mark message as read
            await mark_message_as_read(business_phone_number_id, message_id)

    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error al procesar el mensaje: {e}")

    return HttpResponse(status=200)


@api.get("/webhook")
def verify_webhook(request):
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")


    print(f"Received mode: {mode}")
    print(f"Received token: {token}")
    print(f"Received challenge: {challenge}")
    print(f"VERIFY_TOKEN en el código: {VERIFY_TOKEN}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return HttpResponse(challenge)
    else:
        return HttpResponse("Verification failed", status=403, content_type="text/plain")

async def send_reply_message(phone_number_id, to, message_text, message_id):
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": f"Echo: {message_text}"},
        "context": {"message_id": message_id},
    }

    print(f"URL de la API: {API_URL}")  # Imprimir la URL

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=data) as response:
            response_text = await response.text()
            print(f"Respuesta de la API: {response_text}")

async def mark_message_as_read(phone_number_id, message_id):
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=data) as response:
            response_text = await response.text()
            print(f"Respuesta de la API (marcar como leído): {response_text}")
