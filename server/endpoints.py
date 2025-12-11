'''
This file should contain the endpoints for the application user registration & login authorization flow with Google calendar
google calendar api documentation: https://developers.google.com/calendar/api/guides/overview
'''
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from server.db.database import get_db
from server.db import User
from server.services.google_calendar import GoogleCalendarService
from server.services.google_oauth import google_oauth_service

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

@router.get("/slots/{email}")
def get_slots(email: str, db: Session = Depends(get_db)):
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
        slots = google_calendar_service.get_slots()
        
        return {"slots": slots}
        
    except Exception as e:
        # Catch any errors during the refresh or API call
        print(f"Error accessing calendar for {email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch slots: {e}")