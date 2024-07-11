import aiohttp
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_TOKEN = os.getenv('ACCESS_TOKEN')
VERSION = os.getenv('VERSION')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')

API_URL = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = '../modern-vortex-407314-ca4bebb5d895.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

def is_valid_date(date_text):
    try:
        datetime.strptime(date_text, '%d/%m/%Y %H:%M')
        return True
    except ValueError:
        return False

def generate_calendar_link(summary, location, description):
    base_url = "https://calendar.google.com/calendar/r/eventedit"
    params = {
        'text': summary,
        'location': location,
        'details': description,
        'sf': 'true', # indica que debe ser una creación rápida
        'output': 'xml' # formato de salida
    }
    query = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query}"

async def send_calendar_link(phone_number_id, to, message_id, event_id):
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json",
    }

    # Mapear el ID del evento seleccionado al nombre del evento
    event_name = {
        "event_birthday": "Cumpleaños",
        "event_wedding": "Casamiento",
        "event_party": "Fiesta"
    }.get(event_id, "evento")

    calendar_link = generate_calendar_link(
        summary=f"Reserva de {event_name}",
        location='',
        description=f"Selecciona la fecha y hora para tu {event_name}"
    )

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {
            "body": f"Por favor, utiliza el siguiente enlace para seleccionar la fecha y hora de tu {event_name}: {calendar_link}\nUna vez que hayas reservado en Google Calendar, por favor, responde con la fecha y hora para confirmar."
        },
        "context": {"message_id": message_id},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=data) as response:
            response_text = await response.text()
            print(f"Respuesta de la API: {response_text}")

async def confirm_event_reservation(phone_number_id, to, date_text, message_id):
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json",
    }

    event_date = datetime.strptime(date_text, '%d/%m/%Y %H:%M')

    event = {
        'summary': 'Evento Reservado',
        'start': {
            'dateTime': event_date.isoformat(),
            'timeZone': 'America/Montevideo',
        },
        'end': {
            'dateTime': (event_date + timedelta(hours=2)).isoformat(),
            'timeZone': 'America/Montevideo',
        },
    }
    
    event_result = service.events().insert(calendarId='primary', body=event).execute()

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": f"Tu evento ha sido reservado para el {date_text}. ¡Gracias!"},
        "context": {"message_id": message_id},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=data) as response:
            response_text = await response.text()
            print(f"Respuesta de la API: {response_text}")

    print(f"Evento creado: {event_result.get('htmlLink')}")

def create_event(event_data):
    try:
        event = {
            'summary': event_data['summary'],
            'start': {
                'dateTime': event_data['start_time'],
                'timeZone': event_data['timezone'],
            },
            'end': {
                'dateTime': event_data['end_time'],
                'timeZone': event_data['timezone'],
            },
            # ... (otros campos del evento, como descripción, ubicación, etc.)
        }
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        return event_result.get('htmlLink')
    except Exception as e:
        print(f"Error al crear evento: {e}")
        return None
