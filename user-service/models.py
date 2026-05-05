from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column
from typing import Optional, List, Dict
import uuid

class User(SQLModel, table=True):
    # Unikaten ID uporabnika
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, 
        primary_key=True, 
        index=True
    )
    
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    password_hash: str  # Tukaj shranimo šifrirano geslo
    
    # Nastavitve aplikacije shranimo kot JSON (npr. {"theme": "dark", "lang": "sl"})
    app_settings: Dict = Field(
        default={}, 
        sa_column=Column(JSON)
    )
    
    # Seznam ID-jev naprav, ki pripadajo temu uporabniku
    # n.pr. ["pogobe-123456", "pogobe-sensor-2"]
    device_ids: List[str] = Field(
        default=[], 
        sa_column=Column(JSON)
    )

    is_active: bool = Field(default=True)