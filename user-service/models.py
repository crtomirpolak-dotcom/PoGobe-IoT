from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column
from typing import Optional, List, Dict
import uuid


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    app_settings: Dict = Field(default={}, sa_column=Column(JSON))
    device_ids: List[str] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    password: str  # Zaenkrat surovo geslo -> verjetno bi blo fajn enkripcijo nardit

# Osnovni model za bazo
class User(UserBase, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, 
        primary_key=True, 
        index=True
    )
    password_hash: str  # Baza pozna samo hash


class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None