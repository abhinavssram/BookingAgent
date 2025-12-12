from brain.tools.slots_tool import SlotTool
from server.services.google_calendar import GoogleCalendarService


def setup_agent_tools(google_calendar_service: GoogleCalendarService):
    """
    Instantiates the SlotTool class and retrieves the runnable tools.
    This function should be called for every API request/session.
    """
    # 1. Instantiate the tool wrapper with the dependency
    slot_tool_instance = SlotTool(google_calendar_service=google_calendar_service)

    # 2. Get the bound methods (which are now callable tools)
    tools = [
        slot_tool_instance.get_slots,
        slot_tool_instance.book_slot
    ]

    # 3. Create the lookup dictionary
    tool_by_name = {tool.name: tool for tool in tools}
    
    return tools, tool_by_name