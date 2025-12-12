from fastapi import Depends
from server.services.google_calendar import GoogleCalendarService
from langchain.tools import tool
class SlotTool:
    def __init__(self, google_calendar_service: GoogleCalendarService = Depends(GoogleCalendarService)):
        self.google_calendar_service = google_calendar_service
    @tool
    def get_slots(self) -> list[dict]:
        """
        Get the slots from the google calendar
        """
        slots = self.google_calendar_service.get_slots()
        return slots
    
    @tool
    def book_slot(self, slot: dict) -> dict:
        """
        Book the slot on the google calendar
        """
        response = self.google_calendar_service.book_slot(slot)
        return response