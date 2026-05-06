from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, JSON


class SensorData(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float
    timestamp: datetime = datetime.utcnow()

    class Config:
        schema_extra = {
            "example": {
                "sensor_id": "lht65-12345",
                "temperature": 22.5,
                "humidity": 60.0
            }
        }

class SensorData(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    # Samodejno doda čas, če ga senzor ne pošlje
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class User(SQLModel, table=True):
    # ... ostala polja ...
    device_ids: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))