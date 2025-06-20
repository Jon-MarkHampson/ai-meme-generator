from pydantic import BaseModel
from typing import Optional
from ..users.models import UserRead


# Maybe unused
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class SignupResponse(BaseModel):
    user: UserRead
    access_token: str
    token_type: str
