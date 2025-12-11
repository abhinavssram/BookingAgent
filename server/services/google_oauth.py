from googleapiclient.discovery import build
from server.config import settings
from google_auth_oauthlib.flow import Flow
from server.db.models import User
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from datetime import datetime

class GoogleOAuthService:
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
    
    def get_authorization_url(self, user_id: str) -> str:
        """
        Generate Google OAuth authorization URL
        
        Args:
            user_id: User identifier to track in state parameter
            
        Returns:
            Authorization URL to redirect user to
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        # Generate authorization URL with state parameter
        authorization_url, state = flow.authorization_url(
            access_type='offline',  # Get refresh token
            include_granted_scopes='true',
            prompt='consent',  # Force consent screen to get refresh token
            state=user_id  # Store user_id in state
        )
        
        return authorization_url
    
    def exchange_code_for_tokens(self, code: str) -> dict:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Dictionary containing tokens and user info
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Return tokens as dictionary
        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    def save_tokens(self, db: Session, user_id: str, email: str, tokens: dict):
        """
        Save or update user tokens in database
        
        Args:
            db: Database session
            user_id: User identifier
            email: User email
            tokens: Token dictionary from exchange_code_for_tokens
        """
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            # Update existing user
            user.google_access_token = tokens["token"]
            user.google_refresh_token = tokens["refresh_token"]
            user.google_token_expiry = tokens["expiry"]
            user.email = email
        else:
            # Create new user
            user = User(
                id=user_id,
                email=email,
                google_access_token=tokens["token"],
                google_refresh_token=tokens["refresh_token"],
                google_token_expiry=tokens["expiry"]
            )
            db.add(user)
        
        db.commit() # synchronous blocking operation
        db.refresh(user) # synchronous blocking operation
        return user

    def get_user_info(self, access_token: str) -> tuple[str, str]:
        """
        Fetch user info (email, name) from Google using access token
        """
        from google.oauth2.credentials import Credentials
        
        creds = Credentials(token=access_token)
        
        # Use Google's OAuth2 API to get user info
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        
        return user_info.get("email"), user_info.get("name") if user_info.get("name") else "Unknown Name"
    
    def refresh_and_get_credentials(self, db: Session, user: User) -> Credentials:
            """
            Constructs and refreshes Google Credentials for a user.
            Updates the database if the access token is refreshed.
            """
            
            # Check if the expiry time exists and is a non-empty string
            if user.google_token_expiry and isinstance(user.google_token_expiry, str):
                # Convert the ISO string to a datetime object
                expiry_dt = datetime.fromisoformat(user.google_token_expiry)
            else:
                # If the expiry is missing or invalid, treat it as expired 
                # (or set it to None, which the Credentials object can handle)
                expiry_dt = None
            
            creds = Credentials(
                token=user.google_access_token,
                # CRITICAL: We need the refresh_token to exist here!
                refresh_token=user.google_refresh_token, 
                token_uri=self.client_config["web"]["token_uri"],
                client_id=self.client_config["web"]["client_id"],
                client_secret=self.client_config["web"]["client_secret"],
                scopes=settings.GOOGLE_SCOPES,
                expiry=expiry_dt
            )
            
            # The library uses the 'expiry' argument to determine if it needs to refresh.
            # It handles the case where 'expiry' is None/in the past by checking refresh_token.
            if creds.expired and creds.refresh_token:
                print("DEBUG: Access token expired. Attempting refresh...")
                # refresh() will update creds.token and creds.expiry in-place
                try:
                    creds.refresh(None)
                except Exception as e:
                    # Catch specific errors related to a revoked refresh token
                    raise Exception(f"Failed to refresh token. Re-authentication required: {e}")
                
                # Save the new access token and expiry time back to the database
                user.google_access_token = creds.token
                user.google_token_expiry = creds.expiry.isoformat()
                
                db.commit() # Save the new token data
                db.refresh(user)
                
            elif creds.expired and not creds.refresh_token:
                raise Exception("Refresh token is missing or invalid. User must re-authenticate.")
                
            return creds

google_oauth_service = GoogleOAuthService()