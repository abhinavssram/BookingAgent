
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class MessagesState(TypedDict):
    """
    Represents the state of the conversation, which is a list of messages.
    """
    messages: Annotated[list[AnyMessage], add_messages] #add_messages automaticaly adds 
    conversation_id: str
    timezone: str