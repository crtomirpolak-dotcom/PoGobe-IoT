from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from typing import Optional, List, Dict
import uuid

# 1. Osnovni podatki (niso tabela)
class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    app_settings: Dict = Field(default={}, sa_column=Column(JSON))
    is_active: bool = Field(default=True)

# 2. Tabela za naprave (Relacijski pristop)
class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(index=True, unique=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    
    owner: "User" = Relationship(back_populates="devices")

# 3. EDINA IN PRAVA tabela za uporabnike
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    password_hash: str 
    
    # Seznam ID-jev naprav v JSON obliki (za tvoj trenutni main.py)
    device_ids: Optional[List[str]] = Field(
        default_factory=list, 
        sa_column=Column(JSON)
    )
    
    # Povezava na Device tabelo (za prihodnost)
    devices: List[Device] = Relationship(back_populates="owner")

# 4. Modeli za API
class UserCreate(UserBase):
    password: str

class UserLogin(SQLModel):
    email: str
    password: str

class Token(SQLModel):
    access_token: str
    token_type: str