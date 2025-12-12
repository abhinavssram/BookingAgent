from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class GoogleCalendarService:
    def __init__(self, creds: Credentials): 
        self.client = build('calendar', 'v3', credentials=creds)

    def get_slots(self, time_min: str, time_max: str):

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [
                {"id": "primary"}
            ]
        }

        # 3. Execute the Query
        response = self.client.freebusy().query(body=body).execute()

        # 4. Process the Response
        slots = response['calendars']['primary']
        return slots
    
    def book_slot(self, slot: dict):
        body = {
            "summary": slot["summary"],
            "description": slot["description"],
            "start": {
                "dateTime": slot["start"]["dateTime"],
            },
            "end": {
                "dateTime": slot["end"]["dateTime"],
            }
        }
        response = self.client.events().insert(calendarId='primary', body=body).execute()
        return response