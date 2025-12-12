from typing import Any, Dict, List

from pydantic.v1 import BaseModel, Field
from server.services.google_calendar import GoogleCalendarService
from langchain.tools import tool

# --- Pydantic Schemas for Tool Arguments ---

class GetSlotsInput(BaseModel):
    """Input for getting available calendar slots."""
    time_min: str = Field(..., description="The start time of the period to check, in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).")
    time_max: str = Field(..., description="The end time of the period to check, in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).")

class DateTimeInput(BaseModel):
    """Structure for date and time fields in a booking."""
    dateTime: str = Field(..., description="The time of the event in ISO 8601 format (YYYY-MM-DDTHH:MM:SS+HH:MM or Z).")

class BookSlotInput(BaseModel):
    """Input for booking a slot on the calendar."""
    summary: str = Field(..., description="A brief title or summary for the event (e.g., 'Client Meeting').")
    description: str = Field(..., description="A detailed description of the event.")
    start: DateTimeInput
    end: DateTimeInput

class SlotTool:
    """
    Wrapper class for Google Calendar operations.
    An instance of this class must be created per user session.
    """
    def __init__(self, google_calendar_service: GoogleCalendarService):
        self.google_calendar_service = google_calendar_service

    @tool(args_schema=GetSlotsInput)
    def get_slots(self, time_min: str, time_max: str) -> List[Dict[str, Any]]:
        """
        Get the busy slots from the Google calendar.
        Use this tool to check the user's availability within a specific time range.
        The times must be provided in UTC (Z) format.
        """
        # The service call needs to be updated to accept the new arguments
        # slots = self.google_calendar_service.get_slots(time_min, time_max) # Example
        # You will need to define this service method to accept time_min, time_max
        return self.google_calendar_service.get_slots(time_min, time_max)
    
    @tool(args_schema=BookSlotInput)
    def book_slot(self, summary: str, description: str, start: Dict[str, str], end: Dict[str, str]) -> Dict[str, Any]:
        """
        Book a new event slot on the Google calendar.
        Requires summary, description, and start/end times in ISO 8601 format with timezone offset.
        """
        # Reconstruct the slot dictionary needed by the service
        slot = {
            "summary": summary,
            "description": description,
            "start": start,
            "end": end
        }
        response = self.google_calendar_service.book_slot(slot)
        return response