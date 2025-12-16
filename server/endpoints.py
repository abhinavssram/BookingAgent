'''
This file should contain the endpoints for the application user registration & login authorization flow with Google calendar
google calendar api documentation: https://developers.google.com/calendar/api/guides/overview
'''
import uuid
from fastapi import APIRouter, Cookie, Depends, HTTPException
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from brain.agent import BookingAgent
from server.db.database import get_db
from server.db import User
from server.services.google_calendar import GoogleCalendarService
from server.services.google_oauth import google_oauth_service
from langchain_core.messages import HumanMessage

router = APIRouter()

def get_current_user(
    booking_session: str = Cookie(None),
    db: Session = Depends(get_db)
):
    if not booking_session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == booking_session).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    return user
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
    
    response = RedirectResponse(url="/")

    # 🔑 Store identity in HTTP-only cookie
    response.set_cookie(
        key="booking_session",
        value=user.id,              # or UUID
        httponly=True,
        samesite="lax",
        secure=False  # True in prod (HTTPS)
    )

    return response

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

@router.post("/talk")
def converse(user_input: dict,user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.google_refresh_token:
        raise HTTPException(status_code=403, detail="User has not authorized calendar access.")
    
    try:
        creds = google_oauth_service.refresh_and_get_credentials(db, user)
        google_calendar_service = GoogleCalendarService(creds)
        booking_agent = BookingAgent(google_calendar_service).get_booking_agent()

        conversation_id = user_input.get("conversation_id",None)
        timezone = user_input["timezone"]
        query = user_input["query"]
        if conversation_id=="" or not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": conversation_id}}

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "conversation_id": conversation_id,
            "timezone": timezone
        }
        if booking_agent.checkpointer:
            # Checkpointer will merge with existing state automatically
            result = booking_agent.invoke(initial_state, config=config)
        else:
            # Without checkpointer, just invoke normally
            result = booking_agent.invoke(initial_state)
        
        return {
            "conversation_id": conversation_id,
            "messages": result.get("messages", []),
            "timezone": result.get("timezone", timezone)
        }
    except Exception as e:
        print(f"Error in conversation {user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to talk: {e}")

@router.post("v1/talk/{email}")
def conversev1(email: str, user_input: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.google_refresh_token:
        raise HTTPException(status_code=403, detail="User has not authorized calendar access.")
    
    try:
        creds = google_oauth_service.refresh_and_get_credentials(db, user)
        google_calendar_service = GoogleCalendarService(creds)
        booking_agent = BookingAgent(google_calendar_service).get_booking_agent()

        conversation_id = user_input.get("conversation_id",None)
        timezone = user_input["timezone"]
        query = user_input["query"]
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": conversation_id}}

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "conversation_id": conversation_id,
            "timezone": timezone
        }
        if booking_agent.checkpointer:
            # Checkpointer will merge with existing state automatically
            result = booking_agent.invoke(initial_state, config=config)
        else:
            # Without checkpointer, just invoke normally
            result = booking_agent.invoke(initial_state)
        
        return {
            "conversation_id": conversation_id,
            "messages": result.get("messages", []),
            "timezone": result.get("timezone", timezone)
        }
    except Exception as e:
        print(f"Error in conversation {email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to talk: {e}")


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "email": user.email,
    }
