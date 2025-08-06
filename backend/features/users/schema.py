from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str  # raw password in -> hash


class UserUpdate(BaseModel):
    # REQUIRED: always supply the existing password if you want to change anything
    current_password: str

    # These three are optional—but if any are present, we will verify `current_password` first.
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None  # New password


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    first_name: str
    last_name: str
    email: EmailStr


class UserDelete(BaseModel):
    password: str
