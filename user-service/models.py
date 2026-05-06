from sqlmodel import SQLModel, Field, JSON, Relationship
from sqlalchemy import Column
from typing import Optional, List, Dict
import uuid


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    app_settings: Dict = Field(default={}, sa_column=Column(JSON))
    device_ids: List[str] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = Field(default=True)

class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(index=True, unique=True)  # npr. "goba_1"
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    
    #Povezava nazaj na uporabnika
    owner: "User" = Relationship(back_populates="devices")

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True)
    email: str
    hashed_password: str
    
    devices: list[Device] = Relationship(back_populates="owner")


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

class UserLogin(SQLModel):
    email: str
    password: str