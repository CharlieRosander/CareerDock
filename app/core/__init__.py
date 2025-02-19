"""Core package for CareerDock application."""
from .database import Base, engine, get_db
from .auth.routes import router as auth_router

__all__ = ['Base', 'engine', 'get_db', 'auth_router']
