from langchain_core.tools import StructuredTool
from brain.tools.slots_tool import BookSlotInput, GetSlotsInput, SlotTool
from brain.tools.time_tools import get_current_date
from server.services.google_calendar import GoogleCalendarService


def setup_agent_tools(google_calendar_service: GoogleCalendarService):
    """
    Instantiates the SlotTool class and retrieves the runnable tools.
    This function should be called for every API request/session.
    """
    # 1. Instantiate the tool wrapper with the dependency
    slot_tool_instance = SlotTool(google_calendar_service=google_calendar_service)
    get_slots_tool = StructuredTool.from_function(
            func=slot_tool_instance.get_slots,
            args_schema=GetSlotsInput,
            name="get_slots",
            description="Get the busy slots from the Google calendar. Use this tool to check the user's availability within a specific time range. The times must be provided in UTC (Z) format."
        )
        
    book_slot_tool = StructuredTool.from_function(
        func=slot_tool_instance.book_slot,
        args_schema=BookSlotInput,
        name="book_slot",
        description="Book a new event slot on the Google calendar. Requires summary, description, and start/end times in ISO 8601 format with timezone offset."
    )
    # 2. Get the bound methods (which are now callable tools)
    tools = [
        get_current_date,
        get_slots_tool,
        book_slot_tool,
    ]

    # 3. Create the lookup dictionary
    tool_by_name = {tool.name: tool for tool in tools}
    
    return tools, tool_by_name