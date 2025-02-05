from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from typing import Optional, List

# Shorten Schemas
class ShortenBase(BaseModel):
    long_url: HttpUrl
    expires_at: Optional[datetime] = None

# schemas.py
class ShortenCreate(BaseModel):
    long_url: str

class ShortenUpdate(BaseModel):
    long_url: Optional[HttpUrl] = None
    expires_at: Optional[datetime] = None

class Shorten(ShortenBase):
    id: int
    short_url: str
    created_at: datetime
    user_id: int

    class Config:
        orm_mode = True

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    shorten: List[Shorten] = []

    class Config:
        orm_mode = True

# Response Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None