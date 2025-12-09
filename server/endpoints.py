'''
This file should contain the endpoints for the application user registration & login authorization flow with Google calendar
google calendar api documentation: https://developers.google.com/calendar/api/guides/overview
'''
import uuid
from fastapi import APIRouter, Depends, Request
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from server.db.database import get_db
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
    user_info = google_oauth_service.get_user_info(tokens["token"])  # Returns a dict
    google_email = user_info["email"]  # Extract email from dict
    
    # Create/update user with their actual Google email
    user = google_oauth_service.save_tokens(db, google_email, google_email, tokens)
    
    return {
        "message": "Connected!", 
        "email": google_email,
        "name": user_info.get("name")  # Also return the name
    }