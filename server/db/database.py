from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv
from server.db.models import Base

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Create engine
# For PostgreSQL: postgresql://user:password@localhost:5432/dbname
# For SQLite (testing): sqlite:///./test.db
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production to reduce logging
    pool_pre_ping=True,  # Verify connections before using them
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialize the database by creating all tables.
    Call this when starting the application.
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def get_db() -> Session:
    """
    Dependency for FastAPI routes to get a database session.
    Usage in endpoints:
        def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()