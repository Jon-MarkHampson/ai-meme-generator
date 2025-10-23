"""
Central registry for all SQLModel ORM models.
This module imports all database models to ensure they are registered
with SQLModel before database operations.
"""

from features.conversations.model import Conversation
from features.messages.model import Message
from features.user_memes.model import UserMeme
# Import all SQLModel table models from feature modules
from features.users.model import User

# List of all models for easy reference and validation
all_models = [
    User,
    Conversation,
    Message,
    UserMeme,
]

# Export for convenience
__all__ = [
    "User",
    "Conversation", 
    "Message",
    "UserMeme",
    "all_models",
]