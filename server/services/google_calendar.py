from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class GoogleCalendarService:
    def __init__(self, creds: Credentials): 
        self.client = build('calendar', 'v3', credentials=creds)

    def get_slots(self):

        body = {
            "timeMin": "2025-12-15T00:00:00Z",
            "timeMax": "2025-12-16T23:59:59Z",
            "items": [
                {"id": "primary"}
            ]
        }

        # 3. Execute the Query
        response = self.client.freebusy().query(body=body).execute()

        # 4. Process the Response
        slots = response['calendars']['primary']
        return slots
    
    # def book_slot(self, slot: dict):
    #     body = {
    #         "summary": "Meeting",
    #         "description": "Meeting with John Doe",
    #         "start": {
    #             "dateTime": slot["start"],
    #         },
    #         "end": {
    #             "dateTime": slot["end"],
    #         }
    #     }
    #     response = self.client.events().insert(calendarId='primary', body=body).execute()
    #     return response