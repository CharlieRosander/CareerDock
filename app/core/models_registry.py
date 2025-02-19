"""
Detta är en central plats för att registrera alla modeller för Alembic.
Denna fil importeras BARA av Alembic för migrationer, inte av applikationen.
"""

from .auth.models import User, UserCredentials

# Lista över alla modeller för Alembic
MODELS = [User, UserCredentials]
