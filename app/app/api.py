from ninja import NinjaAPI
from django.http import HttpResponse, JsonResponse
from dotenv import load_dotenv
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import timedelta
import requests
import os
import json
import aiohttp

from .responses import KEYWORDS_RESPONSES, send_event_options, send_default_reply, send_reply_message
from .google_calendar import create_event, confirm_event_reservation, generate_calendar_link, send_calendar_link, is_valid_date
from .utils import mark_message_as_read

api = NinjaAPI()

load_dotenv()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("ACCESS_TOKEN")
VERSION = os.getenv("VERSION")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
API_URL = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

# Google Calendar Config
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = '../modern-vortex-407314-ca4bebb5d895.json'

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)


@api.get("/webhook")
def verify_webhook(request):
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return HttpResponse(challenge)
    else:
        return HttpResponse("Verification failed", status=403, content_type="text/plain")



@api.post("/webhook")
async def webhook(request):
    try:
        body_unicode = request.body.decode('utf-8')
        print("Incoming webhook message:", body_unicode)

        data = json.loads(body_unicode)
        
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                if "messages" in value:
                    for message in value["messages"]:
                        if message["type"] == "text":
                            business_phone_number_id = value["metadata"]["phone_number_id"]
                            recipient_id = message["from"]
                            message_text = message["text"]["body"]
                            message_id = message["id"]

                            if "evento" in message_text.lower():
                                await send_event_options(business_phone_number_id, recipient_id, message_id)
                            elif is_valid_date(message_text):
                                await confirm_event_reservation(business_phone_number_id, recipient_id, message_text, message_id)
                            else:
                                await send_default_reply(business_phone_number_id, recipient_id, message_text, message_id)

                            await mark_message_as_read(business_phone_number_id, message_id)

                        elif message["type"] == "interactive" and "button_reply" in message["interactive"]:
                            action = message["interactive"]["button_reply"]
                            event_id = action["id"]
                            
                            # Obtener 'recipient_id' del mensaje interactivo
                            recipient_id = message["from"]
                            
                            # Verificar si 'business_phone_number_id' está disponible en 'metadata'
                            business_phone_number_id = value.get("metadata", {}).get("phone_number_id", None)
                            if business_phone_number_id:
                                # Llamar a la función adecuada según el evento seleccionado
                                if event_id in ['event_birthday', 'event_wedding', 'event_party']:
                                    await send_calendar_link(business_phone_number_id, recipient_id, message["id"], event_id)
                                else:
                                    print(f"Evento no reconocido: {event_id}")
                            else:
                                print("No se pudo obtener 'business_phone_number_id' del mensaje interactivo.")
                
                
        return HttpResponse(status=200)

    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")
        return HttpResponse(status=500)

async def send_text_message(phone_number_id, to, text, message_id):
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text},
        "context": {"message_id": message_id},
    }

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



