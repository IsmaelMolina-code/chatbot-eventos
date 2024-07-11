import aiohttp
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

GRAPH_API_TOKEN = os.getenv('ACCESS_TOKEN')
VERSION = os.getenv('VERSION')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')

API_URL = f"https://graph.facebook.com/{os.getenv('VERSION')}/{os.getenv('PHONE_NUMBER_ID')}/messages"

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
