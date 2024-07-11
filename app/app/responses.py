import aiohttp
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

GRAPH_API_TOKEN = os.getenv('ACCESS_TOKEN')
VERSION = os.getenv('VERSION')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')

API_URL = f"https://graph.facebook.com/{os.getenv('VERSION')}/{os.getenv('PHONE_NUMBER_ID')}/messages"

KEYWORDS_RESPONSES = {
    "hola": "¡Hola! ¿Cómo puedo ayudarte? Escribe *evento* si quieres agendar o cotizar uno.",
    "evento": "Puedo ayudarte a planificar un evento. ¿Qué tipo de evento tienes en mente?",
    "gracias": "¡De nada! Si tienes más preguntas, no dudes en preguntar.",
    # Agrega más palabras clave y respuestas aquí
}

async def send_event_options(phone_number_id, to, message_id):
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Por favor, selecciona el tipo de evento que deseas reservar:"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "event_birthday",
                            "title": "Cumpleaños"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "event_wedding",
                            "title": "Casamiento"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "event_party",
                            "title": "Fiesta"
                        }
                    }
                ]
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=data) as response:
            response_text = await response.text()
            print(f"Respuesta de la API: {response_text}")

def generate_default_response(message_text):
    return "Lo siento, no entendí tu mensaje. ¿Podrías reformular tu consulta?"

async def send_default_reply(phone_number_id, to, message_text, message_id):
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json",
    }

    response_text = generate_default_response(message_text)
    print(response_text)
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": response_text},
        "context": {"message_id": message_id},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=data) as response:
            response_text = await response.text()
            print(f"Respuesta de la API: {response_text}")

async def send_reply_message(phone_number_id, to, message_text, message_id, buttons=None):
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json",
    }

    if buttons:
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message_text
                },
                "action": {
                    "buttons": buttons
                }
            }
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {"body": message_text},
            "context": {"message_id": message_id},
        }

    print(f"URL de la API: {API_URL}")  # Imprimir la URL

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=data) as response:
            response_text = await response.text()
            print(f"Respuesta de la API: {response_text}")
