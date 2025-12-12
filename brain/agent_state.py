
from typing import TypedDict, List
from langchain_core.messages import BaseMessage

class MessagesState(TypedDict):
    """
    Represents the state of the conversation, which is a list of messages.
    """
    messages: List[BaseMessage]