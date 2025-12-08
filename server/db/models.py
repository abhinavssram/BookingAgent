from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime,timezone
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    google_tokens = Column(JSON, nullable=True)  # Stores access_token, refresh_token, etc.
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"