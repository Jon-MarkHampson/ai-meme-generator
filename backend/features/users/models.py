from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # raw password in -> hash


class UserUpdate(BaseModel):
    # REQUIRED: always supply the existing password if you want to change anything
    current_password: str

    # These three are optional—but if any are present, we will verify `current_password` first.
    username: Optional[str]    = None
    email:    Optional[EmailStr] = None
    password: Optional[str]    = None # New password

    class Config:
        from_attributes = True


class UserRead(BaseModel):
    id: str
    username: str
    email: EmailStr

    class Config:
        from_attributes = True
        
class DeleteRequest(BaseModel):
    password: str
