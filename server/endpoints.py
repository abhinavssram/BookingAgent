'''
This file should contain the endpoints for the application user registration & login authorization flow with Google calendar
google calendar api documentation: https://developers.google.com/calendar/api/guides/overview
'''
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from brain import llm_config
from brain.agent_state import MessagesState
from brain.tools.config import setup_agent_tools
from server.db.database import get_db
from server.db import User
from server.services.google_calendar import GoogleCalendarService
from server.services.google_oauth import google_oauth_service
from re import S
from typing import Literal
from unittest import result
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import START
from brain.llm_config.config import LLMConfig

router = APIRouter()


# Generate a session ID for tracking
@router.get("/connect-calendar")
def connect_google_calendar():
    session_id = str(uuid.uuid4())  # Temporary ID
    authorization_url = google_oauth_service.get_authorization_url(session_id)
    return RedirectResponse(url=authorization_url)

@router.get("/oauth/google/callback")
def oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    session_id = state
    
    tokens = google_oauth_service.exchange_code_for_tokens(code)
    
    # Fetch email from Google's userinfo endpoint
    google_email, google_name = google_oauth_service.get_user_info(tokens["token"])  # Returns a dict
    
    # Create/update user with their actual Google email
    user = google_oauth_service.save_tokens(db, session_id, google_email, tokens)
    
    return {
        "message": "Connected!", 
        "email": google_email,
        "name": google_name  # Also return the name
    }

@router.post("/slots/{email}")
def get_slots(email: str, time_slots: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.google_refresh_token: # Check for the refresh token now
        raise HTTPException(status_code=403, detail="User has not authorized calendar access.")
    
    try:
        # 1. Get/Refresh the Credentials object
        creds = google_oauth_service.refresh_and_get_credentials(db, user)
        
        # 2. Use the valid credentials to build the service
        google_calendar_service = GoogleCalendarService(creds)
        slots = google_calendar_service.get_slots(time_slots["min"],time_slots["max"])
        
        return {"slots": slots}
        
    except Exception as e:
        # Catch any errors during the refresh or API call
        print(f"Error accessing calendar for {email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch slots: {e}")

@router.post("/book-slot/{email}")
def book_slot(email: str, slot: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.google_refresh_token:
        raise HTTPException(status_code=403, detail="User has not authorized calendar access.")
    
    try:
        creds = google_oauth_service.refresh_and_get_credentials(db, user)
        google_calendar_service = GoogleCalendarService(creds)
        response = google_calendar_service.book_slot(slot)
        return {"message": "Slot booked successfully", "response": response}
    except Exception as e:
        print(f"Error booking slot for {email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to book slot: {e}")

@router.post("/talk/{email}")
def converse(email: str, user_input: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.google_refresh_token:
        raise HTTPException(status_code=403, detail="User has not authorized calendar access.")
    
    try:
        def get_system_prompt(): 
            return """You are helpful assistant that helps user with information related to available slots.
    You can assist the user with booking a slot, get the availability of slot on the google calendar.

    You are very polite and helpful and always try to assist the user with the best of your ability.
    You are very friendly and always try to make the user feel comfortable.
    You are very professional and always try to maintain the professionalism.

    Always clarify and get the precise information from the user before proceeding with the task.
    If the user is not clear or not providing the precise information, ask for the information again.

    You have tools at your disposal to assist the user with the task."""

        creds = google_oauth_service.refresh_and_get_credentials(db, user)
        google_calendar_service = GoogleCalendarService(creds)
        # print(creds)
        # Set up the tools for the agent run (PER SESSION)
        llm_config = LLMConfig()
        tools, tool_by_name = setup_agent_tools(google_calendar_service)

        # print(llm_config.llm)
        llm_with_tools = llm_config.llm.bind_tools(tools)

        def llm_call(state: MessagesState):
            system_message = SystemMessage(content=get_system_prompt())
            
            # 2. Construct the full list of messages: [SystemMessage, *HistoryMessages]
            full_message_list = [system_message] + state["messages"]
            
            # 3. Invoke the LLM with the complete message list
            response_message = llm_with_tools.invoke(full_message_list)
            
            return {
                "messages": [response_message]
            }

        def tool_node(state: dict):
            '''Excecute the tool call'''

            result = []

            for tool_call in state["messages"][-1].tool_calls:
                tool = tool_by_name[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                result.append(
                    ToolMessage(content=observation,tool_call_id=tool_call["id"])
                )
            
            return {"messages": result}

        def should_continue(state: MessagesState) -> Literal["environment", END]:
            """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

            messages = state["messages"]
            last_message = messages[-1]
            # If the LLM makes a tool call, then perform an action
            if last_message.tool_calls:
                return "Action"
            # Otherwise, we stop (reply to the user)
            return END


        agent_builder = StateGraph(MessagesState)
        agent_builder.add_node("llm_call", llm_call)
        agent_builder.add_node("environment", tool_node)

        agent_builder.add_edge(START, "llm_call")
        agent_builder.add_conditional_edges(
            "llm_call",
            should_continue,
            {
                # Name returned by should_continue : Name of next node to visit
                "Action": "environment",
                END: END,
            }
        )
        agent_builder.add_edge("environment", "llm_call")
        booking_agent = agent_builder.compile()

        messages = [HumanMessage(content=user_input["query"])]
        messages = booking_agent.invoke({"messages": messages})
        for m in messages["messages"]:
            m.pretty_print()
        return {"messages": messages}
    except Exception as e:
        print(f"Error in conversation {email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to talk: {e}")

