'''
This file should contain the endpoints for the application user registration & login authorization flow with Google calendar
google calendar api documentation: https://developers.google.com/calendar/api/guides/overview
'''
from fastapi import APIRouter, Request

router = APIRouter()


# first endpoint is to register the user with google calendar
'''
this endpoint shoud get the consent from the user to access their google calendar
and then redirect to the google calendar api to get the access token
and then store the access token in the database
and then return the user to the application
'''
@router.post("/google-calendar/register")
def register_google_calendar_user(request: Request):
    return {"message": "User registered with google calendar successfully"}
