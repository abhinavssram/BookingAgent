# Makes db a proper Python package
from server.db.database import get_db, init_db
from server.db.models import User, Base

__all__ = ["get_db", "init_db", "User", "Base"]