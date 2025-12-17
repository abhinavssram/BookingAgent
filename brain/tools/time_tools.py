from langchain.tools import tool

from brain.agent_state import MessagesState

@tool()
def get_current_date():
    """
        Get the user's current date and time from session state.
    """
    return "Resolved at runtime"