import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/google/callback")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # Google OAuth Scopes
    GOOGLE_SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    def validate(self):
        """Validate required settings"""
        if not self.GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID is required in .env")
        if not self.GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_SECRET is required in .env")

settings = Settings()